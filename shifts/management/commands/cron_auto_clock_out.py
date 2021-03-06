from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from shifts.models import Shift, Event, Profile
import datetime

class Command(BaseCommand):
    help = "This is for crontab, so the auto clock out feature will work"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        now = datetime.datetime.now()
        users = User.objects.exclude(profile__auto_clock_out__isnull = True)
        users = users.filter(profile__auto_clock_out__lte = now.time()) 
        for user in users:
            clock_out_event = Event(
                time = datetime.datetime.combine(now.date, user.profile.auto_clock_out),
                event = "OUT",
                user = user,
            )
            clock_out_event.save()
            last_shift = Shifts.objects.filter(user = user, end = None)
            last_shift.end = clock_out_event
            last_shift.save() 
