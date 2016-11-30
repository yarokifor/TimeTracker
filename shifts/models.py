from django.db import models
from django.db import DataError 
from django.contrib.auth.models import User

class Shift(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)

    def save(self, *args, **kwargs):
       
        if Event.last_event(self.user).event != "OUT":
            raise DataError("User is still clocked in.") 
        
        super(Shift, self).save(*arges, **kwargs)

class Event(models.Model):
    EVENTS = (
        ('IN' ,'Clock in'),
        ('OUT','Clock out'),
        ('BST','Break start'),
        ('BEN','Break end'),
        )
    shift = models.ForeignKey(Shift, on_delete = models.CASCADE) 
    time = models.DateTimeField()
    event = models.CharField(max_length = 2, choices=EVENTS)

    @staticmethod
    def last_event(user):
        return Event.objects.filter(shift__user = user).order_by('time').last()
        
    def save(self, *args, **kwargs):
        REQUIRED_EVENT = {
            'IN': ('OUT',None),
            'OUT': ('IN','BEN'),
            'BST': ('IN','BEN'),
            'BEN': ('BIN'),    
        }
        
        if not self.last_event(self.user).event in REQUIRED_EVENT[self.event]:
            raise DataError('To "%s" you must "%s" first.' % (self.event, REQUIRED_EVENT[self.event]))

        super(Event, self).save(*arges, **kwargs)

class Task(models.Model):
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    description = models.TextField()
