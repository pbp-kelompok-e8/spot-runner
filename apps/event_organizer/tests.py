from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from datetime import date, timedelta

from apps.event_organizer.models import EventOrganizer
from apps.event.models import Event
from apps.review.models import Review
from django.utils import timezone

User = get_user_model()


class EventOrganizerViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        # User EO (dengan email unik)
        self.user_eo = User.objects.create_user(
            username='eo_user',
            email='eo_user@example.com',
            password='password123',
            role='event_organizer'
        )

        # Non EO user
        self.user_normal = User.objects.create_user(
            username='normal_user',
            email='normal_user@example.com',
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
        self.assertEqual(response.status_code, 302)
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

        # Refresh updated data
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

    def test_dashboard_updates_event_status(self):
        self.client.login(username='eo_user', password='password123')

        past_event = Event.objects.create(
            name="Past Event",
            user_eo=self.organizer,
            event_date=timezone.now() - timedelta(days=1),
            regist_deadline=timezone.now() - timedelta(days=2),
            event_status="on_going"
        )

        response = self.client.get(reverse('event_organizer:dashboard'))
        past_event.refresh_from_db()

        self.assertEqual(past_event.event_status, "finished")
