import os
from smoketest.constants import Status

CROSS = u'\u2718'
CHECK = u'\u2714'


class Smoketest(object):
    """
    A Smoketest should override the following:

    name:  Property (displayed as header of column)
    __init__:  Should run the smoketest to set up state
    get_status(): Return a constant from Status
    get_brief_result(): Returns a brief description of the result of the test.
    get_detailed_result(): Could include suggestions for repair.  HTML OK.
    """
    def __init__(self):
        assert 'name' in dir(self), "Smoketest requires a name"

    def get_detailed_result(self):
        return self.get_brief_result()


class DiskUsageSmoketest(Smoketest):
    def __init__(self, directory, threshhold=.90):
        self.directory = directory
        self.threshhold = threshhold
        if os.path.exists(self.directory):
            disk = os.statvfs(self.directory)
            capacity = float(disk.f_bsize * disk.f_blocks)
            used = float(disk.f_bsize * (disk.f_blocks - disk.f_bavail))
            self.usage = used / capacity
        else:
            self.usage = None
        super(DiskUsageSmoketest, self).__init__()

    @property
    def name(self):
        return self.directory

    def get_status(self):
        if self.usage is None:
            return Status.WARN
        elif self.usage < self.threshhold:
            return Status.PASS
        else:
            return Status.FAIL

    def get_brief_result(self):
        if self.usage is None:
            return "?"
        else:
            return "%d%%" % (self.usage * 100)

    def get_detailed_result(self):
        if self.usage is None:
            return "Directory %s not found" % self.directory
        else:
            return ("Disk with directory %s is %3.1f%% full"
                    % (self.directory, self.usage * 100))
