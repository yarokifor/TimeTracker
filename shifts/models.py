from django.db import models
from django.db import DataError 
from django.contrib.auth.models import User

class Event(models.Model):
    REQUIRED_EVENT = {
        'IN': ('OUT', None),
        'OUT': ('IN','BEN'),
        'BST': ('IN','BEN'),
        'BEN': ('BIN'),    
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
        if not self.last_event(user).event in self.REQUIRED_EVENT[self.event]:
            raise DataError('To "%s" you must "%s" first.' % (self.event, REQUIRED_EVENT[self.event]))

        super(Event, self).save(*args, **kwargs)

class Shift(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    start = models.ForeignKey(Event, related_name = "start",on_delete = models.CASCADE)
    end = models.ForeignKey(Event, related_name = "end", on_delete = models.SET_NULL, null = True)
    tasks_completed = models.TextField()
