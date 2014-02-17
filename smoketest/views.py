import urllib2
from collections import OrderedDict
from django.conf import settings
from django.views.generic.base import TemplateView
from django.http import HttpResponse
from django.utils.module_loading import import_by_path
from django.utils import simplejson as json
from smoketest.smoketests import CROSS, CHECK
from smoketest import models
from smoketest.constants import Status

PASS, FAIL = (Status.PASS, Status.FAIL)


def view_smoketests(request):
    def get_result(smoketest):
        if isinstance(smoketest, basestring):
            test_path, args = smoketest, ()
        else:
            test_path, args = smoketest[0], smoketest[1:]
        try:
            tester = import_by_path(test_path)(*args)
        except Exception, e:  # On any exception, test has failed
            return {
                "name": tester.name,
                "status": "fail",
                "brief_result": CROSS,
                "detailed_result": "%s" % e
            }
        return {
            "name": tester.name,
            "status": tester.get_status(),
            "brief_result": tester.get_brief_result(),
            "detailed_result": tester.get_detailed_result()
        }
        return tester.perform_test()

    results = [get_result(smoketest) for smoketest in settings.SMOKETESTS]

    return HttpResponse(json.dumps(results),
                        content_type="application/json")


class RemoteSmoketestView(TemplateView):
    template_name = 'smoketest/remotes.html'

    def process_old_style(self, data):
        def process_df(directory, percent):
            f = float(percent.strip('%'))
            ok = f < 80
            return {'name': directory,
                    'status': PASS if ok else FAIL,
                    'brief_result': f,
                    'detailed_result': '%s: %s' % (directory, percent)}

        def process_component(c):
            ok = c['success']
            return {'name': c['name'],
                    'status': PASS if ok else FAIL,
                    'brief_result': CHECK if ok else CROSS,
                    'detailed_result': "OK" if ok else c['error_string']}

        return ([process_component(c) for c in data['components']]
                + [process_df(d, data[d])
                   for d in ['/tmp', '/boot', '/backups']])

    def process(self, remote):
        response = urllib2.urlopen(remote.url)
        data = json.load(response)
        if 'components' in data:
            data = self.process_old_style(data)
        run = models.SmoketestRun.objects.create(remote=remote)
        objs = [models.SmoketestEntry.objects.create(run=run, **item)
                for item in data]
        print objs
        return {'remote': remote,
                'results': data}

    def to_table(self, remotes):
        names = OrderedDict()
        for remote in remotes:
            for result in remote['results']:
                names[result['name']] = True
        names = names.keys()

        def to_row(r):
            d = {c['name']: c for c in r['results']}
            d['remote'] = r['remote']
            print d
            return [d.get(name) for name in names]

        return {'headers': names,
                'rows': [to_row(r) for r in remotes]}

    def get_context_data(self, **kwargs):
        context = super(RemoteSmoketestView, self).get_context_data(**kwargs)
        smoketests = models.RemoteSmoketest.objects.all()
        remotes = [self.process(smoketest) for smoketest in smoketests]
        context['table'] = self.to_table(remotes)
        return context
