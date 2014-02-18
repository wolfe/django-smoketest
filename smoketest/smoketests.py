import os
import imaplib
import random
import string
from smoketest.constants import Status
from smoketest import models
from datetime import datetime, timedelta, date
from django.core.mail import send_mail

CROSS = u'\u2718'
CHECK = u'\u2714'
RECEIVED = "RECEIVED"


DEFAULT_MARKS = {
    'pass': CHECK,
    'warn': '?',
    'fail': CROSS
}


def random_string(alpha=string.ascii_lowercase, length=30):
    return ''.join(random.choice(alpha) for x in range(length))


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

    def get_status(self):
        return self.status

    def get_brief_result(self):
        return DEFAULT_MARKS[self.get_status()]

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


class DatabaseSmoketest(Smoketest):
    name = "DB"

    def __init__(self):
        o1 = models.Data.objects.create(name=self.name,
                                        data=random_string())
        o2 = models.Data.objects.get(pk=o1.pk)
        assert o1.data == o2.data, ("%s != %s" % (o1.data, o2.data))
        o2.delete()
        self.status = Status.PASS


class IMAPBox(object):
    """
    with IMAPBox(to="blah@gmail.com", password="lkjaslkje") as box:
      box.select('inbox')
      ...
    """
    def __init__(self, **credentials):
        self.creds = credentials

    def __enter__(self):
        self.box = imaplib.IMAP4_SSL('imap.gmail.com')
        self.box.login(self.creds['to'],
                       self.creds['password'])
        self.box.select('inbox')
        return self.box

    def __exit__(self, *args):
        self.box.expunge()
        self.box.close()
        self.box.logout()


# http://yuji.wordpress.com/2011/06/22/python-imaplib-imap-example-with-gmail/
class MailSmoketest(Smoketest):
    """
    This assumes a gmail account exists which we will send email to and then
    later (at least one minute later) ping to see if the email was received.

    In settings, entry should be:

    ('smoketest.smoketests.MailSmoketest', {'to': 'bcwfehqhzg@gmail.com',
                                            'from': 'me@company.ca',
                                            'purge_old_mail': True,
                                            'password': 'ljka09u3lkljkc'}))
    where the password authenticates into the gmail account.

    ******************************************************************
    *        purge_old_mail=True WARNING                         *
    * IT IS ASSUMED THAT THE GMAIL ACCOUNT IS FOR THIS USE ONLY. IN  *
    * PARTICULAR, ALL MESSAGES OVER TWO WEEKS OLD ARE PURGED         *
    ******************************************************************
    """
    name = 'Mail'

    def send_mail(self, creds, data):
        return
        send_mail('Test message', 'Here is the message: %s' % data,
                  creds['from'],
                  [creds['to']],
                  fail_silently=False)

    def check_mail(self, creds, data):
        with IMAPBox(**creds) as box:
            typ, msgnums = box.uid('search', None, 'TEXT', data)
            assert len(msgnums[0]) > 0, 'Message not found with text %s' % data

    def purge_old_mail(self, creds):
        """
        Purge messages over one week old
        """
        with IMAPBox(**creds) as box:
            before = date.today() - timedelta(days=7)
            typ, msgnums = box.uid('search', None, 'BEFORE',
                                   before.strftime('%m-%d-%Y'))
            for uid in msgnums[0].split():
                box.uid('store', uid, '+FLAGS', '\\Deleted')
            box.expunge()

    def __init__(self, options):
        self.status = Status.FAIL
        now = datetime.now()
        o1 = models.Data.objects.create(name=self.name,
                                        data=random_string())
        box = imaplib.IMAP4_SSL('imap.gmail.com')
        resp = box.login(options['to'], options['password'])
        assert 'OK' == resp[0], ('Login %s unsuccessful' % options['to'])
        o2 = None
        try:
            # Retrieve last item at least one minute old.  Assuming
            # gmail takes one minute to file email
            o2 = (models.Data.objects
                  .filter(name=self.name)
                  .filter(timestamp__lte=now - timedelta(minutes=1))
                  .latest())
        except models.Data.DoesNotExist:
            pass
        self.send_mail(options, o1.data)
        if o2:
            #  Flag message as already received with "RECEIVED"
            #  so we do not need to hit gmail again.
            if o2.data != RECEIVED:
                self.check_mail(options, o2.data)
                o2.data = RECEIVED
                o2.save()
                if options.get('purge_old_mail', False):
                    self.purge_old_mail(options)
            self.status = Status.PASS
        else:
            self.status = Status.WARN
