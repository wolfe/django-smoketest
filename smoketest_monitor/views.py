import urllib2
import json
from collections import OrderedDict
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.generic.base import TemplateView
from smoketest.smoketests import CROSS, CHECK
from smoketest_monitor import models

PASS, FAIL = (models.Status.PASS, models.Status.FAIL)


class RunSmoketestsView(TemplateView):
    def process_old_style(self, data):
        """
        These are in an initial deployment of smoketests.
        """
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
        response = urllib2.urlopen(remote.url).read()
        try:
            data = json.loads(response)
        except ValueError:
            data = []
        if 'components' in data:
            data = self.process_old_style(data)
        run = models.Run.objects.create(remote=remote, raw_response=response)
        [models.Entry.objects.create(run=run, **item)
         for item in data]

    def get(self, request):
        for remote in models.Remote.objects.all():
            self.process(remote)
        url = reverse('smoketest_results')
        return HttpResponseRedirect(url)


class ResultsView(TemplateView):
    template_name = 'smoketest_monitor/remotes.html'

    def to_table(self, remotes):
        names = OrderedDict()
        for remote in remotes:
            for entry in remote.latest_entries:
                names[entry.name] = True
        names = names.keys()

        def to_row(remote):
            d = {entry.name: entry for entry in remote.latest_entries}
            return {'remote': remote,
                    'columns': [d.get(name) for name in names]}

        return {'headers': names,
                'rows': [to_row(remote) for remote in remotes]}

    def get_context_data(self, **kwargs):
        context = super(ResultsView, self).get_context_data(**kwargs)
        context['table'] = self.to_table(models.Remote.objects.all())
        return context
