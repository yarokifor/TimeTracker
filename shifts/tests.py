from django.test import TestCase, Client
from django.contrib import auth
from django.contrib.auth.models import User
from shifts.models import Event
from django.db import DataError
# Create your tests here.

class Views(TestCase):
    def setUp(self):
        #User.objects.create(username = 'admin', password = 'admin', is_superuser = True) 
        #User.objects.create(username = 'staff', password = 'staff', is_staff = True) 
        #User.objects.create(username = 'user', password = 'user', is_staff = False) 
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

    def test_shifts(self):
        self.client.login(username = 'user', password = 'user')
        response = self.client.get("/shifts")

        self.assertIsNone(response.context["last_shift"])
        self.assertIsNone(response.context["last_event"])
        self.assertEqual(len(response.context["lastest_events"]), 0)
        self.assertIs(response.context['event_choices'], Event.EVENTS)
        self.assertIs(response.context['possible_events'], Event.REQUIRED_EVENT[None])
        self.assertNotIn('task_completed', response.context)

        #response = self.client.post('/shifts', {'event':'task','desc':''})
        #self.assertEqual(response.status_code, 200)
        
        self.assertRaises(DataError, self.client.post('/shifts', {'event':'OUT'}))
            
