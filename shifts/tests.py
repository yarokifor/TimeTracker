from django.test import SimpleTestCase, TransactionTestCase, TestCase, Client
from django.contrib import auth
from django.contrib.auth.models import User, Permission
from shifts.models import Event, Shift, Profile
from django.db import DataError
from django.db.models import QuerySet
from django.utils import timezone
import datetime

# Create your tests here.

class Common_Views(TestCase):
    def setUp(self):
        User.objects.create_user(username = 'user', password='user')
        self.client = Client()

    def test_login_required(self):
        urls = ["/logout","/shifts","/export","/profile"]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response['Location'], "/?next=%s"%url)

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'login.html')

    def test_index_redirect(self):
        self.client.login(username = 'user', password = 'user')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/shifts')

        self.client.logout()

    def test_login_handler(self):
        self.client.post('/login',{'username': 'user', 'password': 'user'})
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated())

        self.client.logout()

    def test_login_handler_incorrect(self):
        response = self.client.post('/login',{'username': 'user', 'password': 'password'}, follow=True)
        self.assertEqual(len(response.context['messages']), 1)
        for message in response.context['messages']:
            self.assertEqual(message.tags, 'error')
            self.assertEqual(str(message), 'Incorrect password.')

        response = self.client.get("/login")
        self.assertEqual(response.status_code, 405)
         
    def test_logout_handler(self):
        self.client.login(username = 'user', password='user')
        response = self.client.get("/logout", follow=True)

        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated())
        
        if user.is_authenticated()== True:
            self.client.logout()

class Shift_View(TransactionTestCase):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username = 'user', password='user')
        self.client.login(username = 'user', password = 'user')
        self.user = auth.get_user(self.client)

    def test_no_data(self):
        response = self.client.get("/shifts")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["last_shift"])
        self.assertIsNone(response.context["last_event"])
        self.assertEqual(len(response.context["lastest_events"]), 0)
        self.assertIs(response.context['event_choices'], Event.EVENTS)
        self.assertIs(response.context['possible_events'], Event.REQUIRED_EVENT[None])
        self.assertNotIn('task_completed', response.context)

    def test_no_data_post_task(self):
        response = self.client.post('/shifts', {'event':'task','desc':''})
        self.assertEqual(response.status_code, 200)
       
    def test_no_data_post_invalid_event(self): 
        invalid_events = ['OUT','BST','BEN']
        for event in invalid_events:
            print(event)
            with self.assertRaises(DataError):
                self.client.post('/shifts', {'event': event})


    def test_post_task(self):
        event = Event(event = 'IN', user = self.user, time = timezone.now())
        event.save()
        Shift(start = event, user = self.user).save()
        
        response = self.client.post('/shifts', {'event':'task','desc':'Test'})

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['last_shift'])
        self.assertIn('tasks_completed', response.context)
        self.assertEqual(response.context['tasks_completed'],['Test'])
        
        response = self.client.post('/shifts', {'event':'task','desc':'Test2'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['last_shift'])
        self.assertIn('tasks_completed', response.context)
        self.assertEqual(response.context['tasks_completed'],['Test','Test2'])

    def test_clock_in(self):
        response = self.client.post('/shifts', {'event': 'IN'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['last_shift'])
        self.assertIsNotNone(response.context['last_event'])
        self.assertEqual(response.context['last_event'].event, 'IN')

    def test_break_start(self):
        event = Event(event = 'IN', user = self.user, time = timezone.now())
        event.save()
        Shift(start = event, user = self.user).save()

        response = self.client.post('/shifts', {'event': 'BST'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['last_shift'])
        self.assertIsNotNone(response.context['last_event'])
        self.assertEqual(response.context['last_event'].event, 'BST')
        
    def test_break_end(self):
        event = Event(event = 'IN', user = self.user, time = timezone.now())
        event.save()
        Shift(start = event, user = self.user).save()
        Event(event = 'BST', user = self.user, time = timezone.now()).save()

        response = self.client.post('/shifts', {'event': 'BEN'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['last_shift'])
        self.assertIsNotNone(response.context['last_event'])
        self.assertEqual(response.context['last_event'].event, 'BEN')

    def test_clock_out(self):
        event = Event(event = 'IN', user = self.user, time = timezone.now())
        event.save()
        Shift(start = event, user = self.user).save()

        response = self.client.post('/shifts', {'event': 'OUT'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['last_shift'])
        self.assertIsNotNone(response.context['last_event'])
        self.assertEqual(response.context['last_shift'].end, response.context['last_event'])
        self.assertEqual(response.context['last_event'].event, 'OUT')

    def test_second_clock_in(self):
        start = Event(event = 'IN', user = self.user, time = timezone.now())
        start.save()
        shift = Shift(start = start, user = self.user)
        shift.save()
        end = Event(event = 'OUT', user = self.user, time = timezone.now())
        end.save()
        shift.end = end
        shift.save() 
       
        response = self.client.post('/shifts', {'event': 'IN'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['last_shift'])
        self.assertIsNotNone(response.context['last_event'])
        self.assertNotEqual(response.context['last_shift'], shift)
        self.assertIsInstance(response.context['last_shift'], Shift)
        self.assertEqual(response.context['last_event'].event, 'IN')

class Export_View(TransactionTestCase):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username = 'user', password='user')
        self.client.login(username = 'user', password = 'user')
        self.user = auth.get_user(self.client)

    def test_no_data(self):
        response = self.client.get('/export')
        
        self.assertNotIn('view_user', response.context)
        self.assertNotIn('users', response.context)

        self.assertEqual(response.context['total_hours'], 0)
        self.assertIsNotNone(response.context['day_shifts_and_hours'])
        for day,shift,hours in response.context['day_shifts_and_hours']:
            self.assertIsInstance(day, datetime.datetime)
            self.assertEqual(len(shift), 0)
            self.assertEqual(hours, 0)
            
    def test_csv(self):
        response = self.client.get('/export',{'type':'csv'})
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_can_view_others(self):
        admin = User.objects.create_user(username = 'admin', password='admin')
        permission = Permission.objects.get(codename="can_view_others")
        admin.user_permissions.add(permission)
        admin_client = Client()
        admin_client.login(username = 'admin', password = 'admin') 

        response = admin_client.get("/export")
        self.assertIn('view_user', response.context)
        self.assertIn('users', response.context)

        self.assertEqual(response.context['view_user'], admin)
        self.assertEqual(len(response.context['users']), len(User.objects.all()))

        response = admin_client.get("/export",{'user': self.user.id})
        self.assertEqual(response.context['view_user'], self.user)

class Profile_View(TransactionTestCase):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username = 'user', password='user')
        self.client.login(username = 'user', password = 'user')
        self.user = auth.get_user(self.client)

    def test_no_data(self): 
        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 200)

    def test_set(self):
        response = self.client.post('/profile',{'event':'auto_clock_out','auto_clock_out':'17:00'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.user.profile.auto_clock_out, datetime.time(17, 0))
          
    def test_set_with_no_data(self):
        response = self.client.post('/profile')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.user.profile.auto_clock_out, None)

    def test_set_to_none(self):
        response = self.client.post('/profile',{'auto_clock_out':None})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.user.profile.auto_clock_out, None)

    def test_set_incorrectly(self):
        response = self.client.post('/profile',{'auto_clock_out':"XX:XX"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.user.profile.auto_clock_out, None)
        for message in response.context['messages']:
            self.assertEqual(message.tags, 'error')
            self.assertEqual(str(message), 'Invalid input.')

