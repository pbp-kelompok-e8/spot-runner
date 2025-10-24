from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.event.models import Event
from apps.event_organizer.models import EventOrganizer
from apps.event.forms import EventForm
import json
from datetime import timedelta

User = get_user_model()

class EventViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user_runner = User.objects.create_user(username="runner", password="pass123", role="runner", email="runner@mail.com")
        self.user_eo = User.objects.create_user(username="eo_user", password="pass123", role="event_organizer", email="eo@mail.com")
        self.event_organizer = EventOrganizer.objects.create(user=self.user_eo)

        self.event = Event.objects.create(
            user_eo=self.event_organizer,
            name="Test Event",
            description="This is a test event.",
            location="jakarta",
            event_date=timezone.now() + timedelta(days=10),
            regist_deadline=timezone.now() + timedelta(days=5),
            contact="08123456789",
            capacity=100,
            total_participans=10,
            coin=50,
        )

    def test_create_event_requires_login(self):
        response = self.client.get(reverse('event:create_event'))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_create_event_as_eo_success(self):
        self.client.login(username='eo_user', password='pass123')
        form_data = {
            'name': 'New Event',
            'description': 'Some description',
            'location': 'bandung',
            'event_date': (timezone.now() + timedelta(days=10)).strftime('%Y-%m-%dT%H:%M'),
            'regist_deadline': (timezone.now() + timedelta(days=5)).strftime('%Y-%m-%dT%H:%M'),
            'contact': '08123456789',
            'capacity': 200,
            'coin': 100,
            'event_status': 'coming_soon',
            'event_category': [],
        }
        response = self.client.post(reverse('event:create_event'), form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Event.objects.filter(name='New Event').exists())

    def test_create_event_as_runner_denied(self):
        self.client.login(username='runner', password='pass123')
        response = self.client.get(reverse('event:create_event'))
        self.assertEqual(response.status_code, 403)

    def test_edit_event_success(self):
        self.client.login(username='eo_user', password='pass123')
        url = reverse('event:edit_event', args=[self.event.id])
        response = self.client.post(url, {
            'name': 'Updated Event Name',
            'description': 'Updated description',
            'location': 'surabaya',
            'event_date': (timezone.now() + timedelta(days=15)).strftime('%Y-%m-%dT%H:%M'),
            'regist_deadline': (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M'),
            'contact': '0899999999',
            'capacity': 150,
            'coin': 80,
        })
        self.assertEqual(response.status_code, 302)
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, "Updated Event Name")

    def test_edit_event_denied_for_other_user(self):
        other_user = User.objects.create_user(username='other_eo', password='pass123', role='event_organizer', email='other@mail.com')
        other_eo = EventOrganizer.objects.create(user=other_user)
        self.client.login(username='other_eo', password='pass123')
        response = self.client.get(reverse('event:edit_event', args=[self.event.id]))
        self.assertEqual(response.status_code, 403)

    def test_delete_event(self):
        self.client.login(username='eo_user', password='pass123')
        url = reverse('event:delete_event', args=[self.event.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Event.objects.filter(id=self.event.id).exists())

    def test_show_event(self):
        self.client.login(username='runner', password='pass123')
        url = reverse('event:show_event', args=[self.event.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.name)

    def test_show_xml(self):
        self.client.login(username='runner', password='pass123')
        response = self.client.get(reverse('event:show_xml'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<object", response.content)

    def test_show_json(self):
        self.client.login(username='runner', password='pass123')
        response = self.client.get(reverse('event:show_json'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIsInstance(data, list)
        self.assertEqual(data[0]['name'], self.event.name)

    def test_show_xml_by_id(self):
        url = reverse('event:show_xml_by_id', args=[self.event.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<object", response.content)

    def test_show_json_by_id(self):
        url = reverse('event:show_json_by_id', args=[self.event.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['name'], self.event.name)
        self.assertEqual(data['user_eo']['username'], self.user_eo.username)
