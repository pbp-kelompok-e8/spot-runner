from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

from apps.event_organizer.models import EventOrganizer
from apps.event.models import Event
from apps.review.models import Review

User = get_user_model()


class EventOrganizerViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        # User EO
        self.user_eo = User.objects.create_user(
            username='eo_user',
            password='password123',
            role='event_organizer'
        )

        # Non EO User
        self.user_normal = User.objects.create_user(
            username='normal_user',
            password='password123',
            role='runner'
        )

        # Organizer profile
        self.organizer = EventOrganizer.objects.create(
            user=self.user_eo,
            base_location='Jakarta'
        )

    def test_dashboard_access_denied_for_non_organizer(self):
        self.client.login(username='normal_user', password='password123')
        response = self.client.get(reverse('event_organizer:dashboard'))
        self.assertEqual(response.status_code, 302)  # redirect
        self.assertIn(reverse('main:show_main'), response.url)

    def test_dashboard_loads_for_organizer(self):
        self.client.login(username='eo_user', password='password123')
        response = self.client.get(reverse('event_organizer:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'event_organizer/dashboard.html')
        self.assertIn('organizer', response.context)

    def test_profile_view_non_organizer(self):
        self.client.login(username='normal_user', password='password123')
        response = self.client.get(reverse('event_organizer:profile'))
        self.assertEqual(response.status_code, 302)

    def test_profile_view_success(self):
        self.client.login(username='eo_user', password='password123')
        response = self.client.get(reverse('event_organizer:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'event_organizer/profile.html')

    def test_edit_profile_post(self):
        self.client.login(username='eo_user', password='password123')
        response = self.client.post(reverse('event_organizer:edit_profile'), {
            'username': 'new_username',
            'base_location': 'Bandung',
            'profile_picture': 'http://example.com/image.jpg'
        })
        self.assertRedirects(response, reverse('event_organizer:profile'))

        self.user_eo.refresh_from_db()
        self.organizer.refresh_from_db()

        self.assertEqual(self.user_eo.username, 'new_username')
        self.assertEqual(self.organizer.base_location, 'Bandung')
        self.assertEqual(self.organizer.profile_picture, 'http://example.com/image.jpg')

    def test_change_password_valid(self):
        self.client.login(username='eo_user', password='password123')
        response = self.client.post(reverse('event_organizer:change_password'), {
            'old_password': 'password123',
            'new_password1': 'newsecurepassword456',
            'new_password2': 'newsecurepassword456',
        })
        self.assertRedirects(response, reverse('event_organizer:profile'))

        self.user_eo.refresh_from_db()
        self.assertTrue(check_password('newsecurepassword456', self.user_eo.password))

    def test_change_password_invalid(self):
        self.client.login(username='eo_user', password='password123')
        response = self.client.post(reverse('event_organizer:change_password'), {
            'old_password': 'wrongpassword',
            'new_password1': 'newpass123',
            'new_password2': 'newpass123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'event_organizer/change_password.html')
