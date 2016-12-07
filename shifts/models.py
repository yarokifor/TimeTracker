from django.db import models
from django.db import DataError 
from django.contrib.auth.models import User

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
    event = models.CharField(max_length = 2, choices=EVENTS)
    user = models.ForeignKey(User, on_delete = models.CASCADE)

    @staticmethod
    def last_event(user):
        return Event.objects.filter(user = user).order_by('time').last()
        
    def save(self, *args, **kwargs):
        last_event = self.last_event(self.user)
        if last_event != None and last_event.id != self.id and not self.event in self.REQUIRED_EVENT[last_event.event]:
            raise DataError('To "%s" you must "%s" first and not "%s"' % (self.event, self.REQUIRED_EVENT[last_event.event], last_event.event))

        super(Event, self).save(*args, **kwargs)

class Shift(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    start = models.ForeignKey(Event, related_name = "start",on_delete = models.CASCADE)
    end = models.ForeignKey(Event, related_name = "end", on_delete = models.SET_NULL, null = True)
    tasks_completed = models.TextField()
