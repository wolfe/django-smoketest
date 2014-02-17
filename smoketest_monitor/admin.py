from django.contrib import admin
from smoketest_monitor import models

admin.site.register(models.Remote)
admin.site.register(models.Run)
admin.site.register(models.Entry)
