from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import UserProfile

class AuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('auth-register')
        self.login_url = reverse('auth-login')
        self.logout_url = reverse('auth-logout')
        self.refresh_url = reverse('auth-refresh')
        self.me_url = reverse('auth-me')

        # Create user
        self.user = User.objects.create_user(username='9876543210', email='test@example.com', password='password123', first_name='Test', last_name='User')
        self.profile = UserProfile.objects.create(user=self.user, phone='9876543210')

    def test_register_valid(self):
        data = {
            'first_name': 'New',
            'last_name': 'User',
            'phone': '1234567890',
            'email': 'new@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'accept_terms': True
        }
        res = self.client.post(self.register_url, data)
        self.assertEqual(res.status_code, 201)
        self.assertTrue(User.objects.filter(username='1234567890').exists())

    def test_login_valid_phone(self):
        data = {'identifier': '9876543210', 'password': 'password123'}
        res = self.client.post(self.login_url, data)
        self.assertEqual(res.status_code, 200)
        self.assertIn('access_token', res.cookies)

    def test_login_valid_email(self):
        data = {'identifier': 'test@example.com', 'password': 'password123'}
        res = self.client.post(self.login_url, data)
        self.assertEqual(res.status_code, 200)

    def test_login_invalid(self):
        data = {'identifier': '9876543210', 'password': 'wrong'}
        res = self.client.post(self.login_url, data)
        self.assertEqual(res.status_code, 401)

    def test_current_user_unauthenticated(self):
        res = self.client.get(self.me_url)
        self.assertEqual(res.status_code, 401)
        
    def test_logout(self):
        data = {'identifier': '9876543210', 'password': 'password123'}
        res = self.client.post(self.login_url, data)
        self.client.cookies = res.cookies
        res_logout = self.client.post(self.logout_url)
        self.assertEqual(res_logout.status_code, 200)
        self.assertEqual(res_logout.cookies['access_token'].value, '')
