django-smoketest
================

A pair of Apps, one for running smoketests, and one for monitoring
them from another server.

Each app has an sample project (called example) with settings
configurations.  To demo locally, launch each project on a different port.

Suppose you run smoketest/example/ on 8000 and smoketest_monitor/example/ on 8001.
- Visit the /smoketest/ url of the smoketest app.  You should see a
  json response showing disk space. Configure settings.py to change
  which smoketest are run.  Some have external dependencies.
- Visit the admin of the smoketest_monitor app, add a "remote", entering
  the full URL of the /smoketest/ (During testing, it would look something like
  http://127.0.0.1:8000/smoketest/)
- Now visit http://127.0.0.1:8000/smoketest/run/ -- this should ping
  the smoketest and redirect to a tabular view of results.

History
=======

The smoketest app was first conceived by David Wolfe and Chris Troup
at Sheepdog, using a Google app script to monitor the Django
smoketests.  Both apps were later re-developed at aioTV by David Wolfe.
