from django.db import models


class Data(models.Model):
    """
    A catch-all column for storing any random data that might be required for
    smoketests.
    """
    class Meta(object):
        get_latest_by = 'timestamp'

    timestamp = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=256)  # Smoketest name, presumably
    data = models.TextField()
