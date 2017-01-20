from django.test import TestCase, Client
from django.contrib import auth
from django.contrib.auth.models import User

# Create your tests here.

class Views(TestCase):
    def setUp(self):
        #User.objects.create(username = 'admin', password = 'admin', is_superuser = True) 
        #User.objects.create(username = 'staff', password = 'staff', is_staff = True) 
        #User.objects.create(username = 'user', password = 'user', is_staff = False) 
        User.objects.create_user(username = 'user', password='user')
        self.client = Client()

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
        self.assertEqual(user.is_authenticated(), True)

        self.client.logout()
         
    def test_logout_handler(self):
        self.client.login(username = 'user', password='user')
        response = self.client.get("/logout", follow=True)

        user = auth.get_user(self.client)
        self.assertEqual(user.is_authenticated(), False)
        
        if user.is_authenticated()== True:
            self.client.logout()

    def test_shifts(self):
        self.client.login(username = 'user', password = 'user')
        response = self.client.get("/shifts")

        self.assertEqual(response.context["last_shift"], None)
        self.assertEqual(response.context["last_event"], None)
        self.assertEqual(len(response.context["lastest_events"]), 0)

