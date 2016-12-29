from django.contrib.auth.models import User
import datetime
from djagno_cron import CronJobBase, Schedule
from shifts.models import Shift, Event, Profile


class Auto_Clock(CronJobBase):
    RUNS_EVERY_MINS = 30
    schedule = Schedule(run_every_mins=RUNS_EVERY_MINS)

    code = 'shifts.Auto_Clock'

    def do(self):
        now = datetime.datetime.now()
        users = User.objects.exclude(profile__auto_clock_out__isnull = False, profile__auto_clock_out__gte = now.time())
        for user in users:
            clock_out_event = Event(
                time = datetime.datetime.combine(now.date, user.profile.auto_clock_out)
                event = "OUT"
                user = user
            )
            clock_out_event.save()
            last_shift = Shifts.objects.filter(user = user, end = None)
            last_shift.end = clock_out_event
            last_shift.save()
