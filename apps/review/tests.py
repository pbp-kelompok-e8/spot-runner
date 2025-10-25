# Create your tests here.
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.main.models import Runner
from apps.event.models import Event
from apps.event_organizer.models import EventOrganizer
from apps.review.models import Review

class CreateReviewViewTest(TestCase):
    def setUp(self):
        # Client untuk simulasi request
        self.client = Client()

        # Buat user dan login
        self.user = User.objects.create_user(username="runner1", password="password123")
        self.client.login(username="runner1", password="password123")

        # Buat Event Organizer
        self.eo_user = User.objects.create_user(username="eo1", password="password123")
        self.event_organizer = EventOrganizer.objects.create(user=self.eo_user, organization_name="EO Test")

        # Buat Runner
        self.runner = Runner.objects.create(user=self.user, age=25)

        # Buat Event
        self.event = Event.objects.create(
            name="Marathon Jakarta",
            user_eo=self.event_organizer,
            location="Jakarta",
            description="Event marathon 2025"
        )

        self.url = reverse('review:create_review')

    def test_create_review_success(self):
        """✅ Test membuat review baru berhasil"""
        data = {
            'event_id': self.event.id,
            'rating': 5,
            'review_text': 'Event luar biasa!'
        }
        response = self.client.post(self.url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {
                'success': True,
                'review': {
                    'user': 'runner1',
                    'event': 'Marathon Jakarta',
                    'rating': 5,
                    'review_text': 'Event luar biasa!',
                    'created_at': response.json()['review']['created_at']  # tanggal dinamis
                }
            }
        )
        self.assertTrue(Review.objects.filter(runner=self.runner, event=self.event).exists())

    def test_invalid_rating(self):
        """🚫 Test rating tidak valid (bukan angka)"""
        data = {
            'event_id': self.event.id,
            'rating': 'abc',
            'review_text': 'Harusnya gagal'
        }
        response = self.client.post(self.url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid rating', response.json()['error'])

    def test_rating_out_of_range(self):
        """🚫 Test rating di luar range (harus 1–5)"""
        data = {
            'event_id': self.event.id,
            'rating': 10,
            'review_text': 'Terlalu tinggi'
        }
        response = self.client.post(self.url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Rating must be between 1 and 5', response.json()['error'])

    def test_not_runner_user(self):
        """🚫 Test user yang bukan runner"""
        user2 = User.objects.create_user(username="bukan_runner", password="password123")
        self.client.login(username="bukan_runner", password="password123")

        data = {
            'event_id': self.event.id,
            'rating': 4,
            'review_text': 'Saya bukan runner'
        }
        response = self.client.post(self.url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)
        self.assertIn('Only runners can post reviews', response.json()['error'])

    def test_not_ajax_request(self):
        """🚫 Test request biasa (non-AJAX)"""
        data = {
            'event_id': self.event.id,
            'rating': 4,
            'review_text': 'Bukan AJAX'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid request', response.json()['error'])
