from django.db import models
from django.db import DataError 
from django.contrib.auth.models import User
from django.db.models.signals import post_save

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
        last_event = self.last_event(self.user)
        if last_event != None and self.id == None and not self.event in self.REQUIRED_EVENT[last_event.event]:
            raise DataError('To "%s" you must "%s" first and not "%s"' % (self.event, self.REQUIRED_EVENT[last_event.event], last_event.event))

        super(Event, self).save(*args, **kwargs)

class Shift(models.Model):
    class Meta:
        permissions = (('can_view_others','Can veiw others shifts and events'),)

    user = models.ForeignKey(User, on_delete = models.CASCADE)
    start = models.ForeignKey(Event, related_name = "start",on_delete = models.CASCADE)
    end = models.ForeignKey(Event, related_name = "end", on_delete = models.SET_NULL, null = True)
    tasks_completed = models.TextField()
