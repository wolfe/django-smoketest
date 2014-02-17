from django.conf.urls import patterns, url
from smoketest_monitor import views

urlpatterns = patterns(
    '',
    url(r'^view/$', views.ResultsView.as_view(), name='smoketest_results'),
    url(r'^run/$', views.RunSmoketestsView.as_view()))
