from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from authentication.models import UserProfile

class ProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.profile_url = reverse('profile')
        self.login_url = reverse('auth-login')
        
        self.user = User.objects.create_user(username='9876543210', email='test@example.com', password='password123', first_name='Test', last_name='User')
        self.profile = UserProfile.objects.create(user=self.user, phone='9876543210', preferred_language='en')

        # Login to get cookie
        res = self.client.post(self.login_url, {'identifier': '9876543210', 'password': 'password123'})
        self.client.cookies = res.cookies

    def test_get_profile(self):
        res = self.client.get(self.profile_url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['phone'], '9876543210')

    def test_update_profile(self):
        data = {
            'first_name': 'Updated',
            'preferred_language': 'hi'
        }
        res = self.client.put(self.profile_url, data, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.profile.preferred_language, 'hi')
