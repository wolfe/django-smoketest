from django.conf.urls import patterns, url
import views

urlpatterns = patterns(
    '',
    url(r'^$', views.view_smoketests),
    url(r'^all/$', views.RemoteSmoketestView.as_view()))
