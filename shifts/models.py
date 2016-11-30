from django.db import models
from django.contrib.auth.models import User

class Shift(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)

class Event(models.Model):
    EVENTS = (
        ("IN" ,"Clock in"),
        ("OUT","Clock out"),
        ("BST","Break start"),
        ("BEN","Break end"),
        )
    shift = models.ForeignKey(Shift, on_delete = models.CASCADE) 
    time = models.DateTimeField()
    event = models.CharField(max_length = 2, choices=EVENTS)

class Task(models.Model):
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    description = models.TextField()

