from django.test import SimpleTestCase, TransactionTestCase, TestCase, Client
from django.contrib import auth
from django.contrib.auth.models import User
from shifts.models import Event, Shift, Profile
from django.db import DataError
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

class Shift_Veiw(TransactionTestCase):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username = 'user', password='user')
        self.client.login(username = 'user', password = 'user')
        self.user = auth.get_user(self.client)

    def test_shifts_no_data(self):
        response = self.client.get("/shifts")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["last_shift"])
        self.assertIsNone(response.context["last_event"])
        self.assertEqual(len(response.context["lastest_events"]), 0)
        self.assertIs(response.context['event_choices'], Event.EVENTS)
        self.assertIs(response.context['possible_events'], Event.REQUIRED_EVENT[None])
        self.assertNotIn('task_completed', response.context)

    def test_shifts_no_data_post_task(self):
        response = self.client.post('/shifts', {'event':'task','desc':''})
        self.assertEqual(response.status_code, 200)
       
    def test_shifts_no_data_post_invalid_event(self): 
        invalid_events = ['OUT','BST','BEN']
        for event in invalid_events:
            with self.assertRaises(DataError):
                self.client.post('/shifts', {'event': event})

    def test_shifts_clock_in(self):
        response = self.client.post('/shifts', {'event': 'IN'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['last_shift'])
        self.assertIsNotNone(response.context['last_event'])
        self.assertIsNotNone(response.context['last_event'])
        

    def test_shifts_post_task(self):
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

    def test_shifts_break_start(self):
        event = Event(event = 'IN', user = self.user, time = timezone.now())
        event.save()
        Shift(start = event, user = self.user).save()

        response = self.client.post('/shifts', {'event': 'BST'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['last_shift'])
        self.assertIsNotNone(response.context['last_event'])
        self.assertEqual(response.context['last_event'].event, 'BST')
        
    def test_shifts_break_end(self):
        pass
    def test_shifts_clock_out(self):
        pass

