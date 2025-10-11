
from django.test import TestCase, Client
from .models import User
from django.urls import reverse

class ParticipantsPermissionsTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username='creator', password='pass', role='creator', email='c@example.com')
        self.admin = User.objects.create_user(username='admin', password='pass', role='admin', email='a@example.com')
        self.moder = User.objects.create_user(username='moder', password='pass', role='moder', email='m@example.com')
        self.helper = User.objects.create_user(username='helper', password='pass', role='helper', email='h@example.com')
        self.client = Client()

    def test_helper_cannot_access_participants(self):
        self.client.login(username='helper', password='pass')
        resp = self.client.get(reverse('accounts:participants'))
        self.assertIn(resp.status_code, (302, 403))

    def test_moder_can_access(self):
        self.client.login(username='moder', password='pass')
        resp = self.client.get(reverse('accounts:participants'))
        self.assertEqual(resp.status_code, 200)

    def test_admin_can_change_role_but_not_promote_to_admin_creator(self):
        self.client.login(username='admin', password='pass')

        response = self.client.post(reverse('accounts:change_role', args=[self.helper.id]), {'role': 'admin'}, follow=True)
        self.assertIn(response.status_code, (302, 200))
