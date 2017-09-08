from django.db import models
from django.db import DataError 
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.conf import settings


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    auto_clock_out = models.TimeField(null=True, blank=True)

def profile_create_callback(sender, **kwargs):
    if kwargs['created'] == True:
        Profile(user = kwargs['instance']).save() 

post_save.connect(profile_create_callback, sender = User, weak = False)

class Event(models.Model):
    REQUIRED_EVENT = {
        'OUT': ('IN'),
        None: ('IN'),
        'IN': ('OUT','BST'),
        'BEN': ('OUT','BST'),
        'BST': ('BEN'),
    }
    EVENTS = (
        ('IN' ,'Clock in'),
        ('OUT','Clock out'),
        ('BST','Break start'),
        ('BEN','Break end'),
    )
    time = models.DateTimeField()
    event = models.CharField(max_length = 3, choices=EVENTS)
    user = models.ForeignKey(User, on_delete = models.CASCADE)

    @staticmethod
    def last_event(user):
        return Event.objects.filter(user = user).order_by('time').last()
        
    def save(self, *args, **kwargs):
        try:
            if(settings.DISABLE_CLOCK_CHECK == True ):
                super(Event, self).save(*args, **kwargs)
        except:
            pass
        last_event = self.last_event(self.user)
        if last_event != None:
            last_event = last_event.event
        if self.id == None and not self.event in self.REQUIRED_EVENT[last_event]:
            raise DataError('To "%s" you must "%s" first and not "%s"' % (self.event, self.REQUIRED_EVENT[last_event], last_event))

        super(Event, self).save(*args, **kwargs)

    def __str__(self):
        return "%d %s: %s @%s"%(self.id, self.user.username, self.event, self.time.strftime("%x %X"))

class Shift(models.Model):
    class Meta:
        permissions = (('can_view_others','Can veiw others shifts and events'),)

    user = models.ForeignKey(User, on_delete = models.CASCADE)
    start = models.ForeignKey(Event, related_name = "start",on_delete = models.CASCADE)
    end = models.ForeignKey(Event, related_name = "end", on_delete = models.SET_NULL, null = True)
    tasks_completed = models.TextField()

class Registration(models.Model):
    class Meta:
        permissions = (('can_send_registration','Can send a registration request.'),)
    email = models.TextField()
    key_hash = models.BinaryField()
