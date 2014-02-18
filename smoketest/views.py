from django.conf import settings
from django.http import HttpResponse
from django.utils.module_loading import import_by_path
import json
from smoketest.smoketests import CROSS
from smoketest.constants import Status

PASS, FAIL = (Status.PASS, Status.FAIL)


def view_smoketests(request):
    def get_result(smoketest):
        if isinstance(smoketest, basestring):
            test_path, args = smoketest, ()
        else:
            test_path, args = smoketest[0], smoketest[1:]
        try:
            tester = import_by_path(test_path)
            # We assume if tester(*args) fails, that at least
            # tester is left as the class and we can report tester.name
            tester = tester(*args)
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

    results = [get_result(smoketest) for smoketest in settings.SMOKETESTS]

    return HttpResponse(json.dumps(results),
                        content_type="application/json")
