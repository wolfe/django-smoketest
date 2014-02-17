from django.db import models
from smoketest.constants import Status

STATUS_CHOICES = [getattr(Status, name) for name in dir(Status)
                  if not name.startswith('_')]


class Remote(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField(max_length=255)
    notes = models.TextField(blank=True)

    @property
    def latest_run(self):
        if not hasattr(self, '_latest_run'):
            try:
                self._latest_run = self.run_set.latest()
            except Run.DoesNotExist:
                self._latest_run = None
        return self._latest_run

    @property
    def latest_entries(self):
        if not hasattr(self, '_latest_entries'):
            if self.latest_run is None:
                self._latest_entries = []
            else:
                self._latest_entries = list(self.latest_run.entry_set
                                            .all())
        return self._latest_entries

    def __unicode__(self):
        return self.name


class Run(models.Model):
    class Meta(object):
        get_latest_by = 'timestamp'

    remote = models.ForeignKey(Remote)
    raw_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s: %s" % (self.timestamp, self.remote)


class Entry(models.Model):
    run = models.ForeignKey(Run)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=10,
                              choices=((s, s) for s in STATUS_CHOICES))
    brief_result = models.CharField(max_length=255)
    detailed_result = models.TextField()

    def __unicode__(self):
        return "%s: %s" % (self.name, self.status)
