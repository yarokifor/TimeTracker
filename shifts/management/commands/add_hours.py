from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from shifts.models import Shift, Event, Profile
import datetime

class Command(BaseCommand):
    help = "This allows an admin to add hours to user who forgot to use the software."

    def add_arguments(self, parser):
        parser.add_argument("--start_day", nargs=1, required=True, help='MM/DD/YYYY')
        parser.add_argument("--start_time", nargs=1, default=["09:00"], help='HH:MM')
        parser.add_argument("--num_hours", nargs=1, type=float, required=True)
        parser.add_argument("--username", nargs=1, required=True)


    def handle(self, *args, **options):
        try:
            if(settings.DISABLE_CLOCK_CHECK == False):
                raise CommandError('DISABLE_CLOCK_CHECK must be true for this command to work properly!')
        except:
                raise CommandError('DISABLE_CLOCK_CHECK must be true for this command to work properly!')
        start_month, start_day, start_year = options['start_day'][0].split('/')
        start_hour, start_minute = options['start_time'][0].split(':')
        start = datetime.datetime(
            year = int(start_year), 
            month = int(start_month),
            day = int(start_day),
            hour = int(start_hour),
            minute = int(start_minute))

        start = timezone.make_aware(start)

        user = None
        try:
            user = User.objects.get(username = options['username'][0])
        except User.DoesNotExist:
            raise CommandError('User, %s, does not exist.'% options['username'][0])

        self.stdout.write("Checking for conflicting events...")
        
        end = start + datetime.timedelta(hours = options['num_hours'][0])

        if len(Event.objects.filter(user = user, time__gte = start, time__lte = end )) != 0:
            raise CommandError('User has event between the start and end of pesudo shift.')
        
        
        start_event = Event(time = start, event = 'IN', user = user)
        
        start_event.save()
        
        end_event = Event(time = end, event = 'OUT', user = user)

        end_event.save()

        shift = Shift(user = user, start = start_event, end = end_event, tasks_completed = '`This shift was manully added via the command line`')

        shift.save()
