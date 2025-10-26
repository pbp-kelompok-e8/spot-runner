from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.event_organizer.models import EventOrganizer
from apps.event.models import Event, EventCategory
from apps.main.models import Runner 
from .forms import EventForm
import json
from django.utils import timezone

User = get_user_model()
class EventViewsTest(TestCase):
    
    def setUp(self):
        """
        Setup data awal untuk setiap tes.
        Membuat user, organizer, kategori, client, dan login.
        """
        self.user = User.objects.create_user(username='testeo', password='password123',email='eoo@test')
        self.organizer = EventOrganizer.objects.create(user=self.user, base_location='Test Location')
        self.runner_user = User.objects.create_user(username='testrunner', password='password123', email='runner@test')
        self.runner = Runner.objects.create(user=self.runner_user)

        # self.cat_5k = EventCategory.objects.create(category='5k')
        # self.cat_10k = EventCategory.objects.create(category='10k')
        
        # 4. Buat Test Client dan Login
        self.client = Client()
        self.client.login(username='testeo', password='password123')
        self.event = Event.objects.create(
            user_eo=self.organizer,
            name="Test Event 1",
            location="jakarta_pusat",
            capacity=100,
            event_date=timezone.now(), 
            regist_deadline=timezone.now() + timezone.timedelta(days=1),
        )
        # self.event.event_category.add(self.cat_5k)
        
        # 6. Buat Review awal
        # self.review = Review.objects.create(
        #     event=self.event,
        #     runner=self.runner,
        #     rating=5,
        #     comment="Great event!"
        # )

    def test_create_event_get(self):
        """Tes halaman create event (GET)"""
        response = self.client.get(reverse('event:create_event'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_event.html')
        self.assertIsInstance(response.context['form'], EventForm)

    def test_create_event_post_success(self):
        """Tes membuat event baru (POST) dengan request standar"""
        data = {
            'name': 'New Event Created',
            'description': 'A new test event.',
            'location': 'jakarta_selatan',
            'capacity': 50,
            'event_status': 'coming_soon',
            'coin': 10,
        }
        response = self.client.post(reverse('event:create_event'), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('main:show_main'))
        self.assertTrue(Event.objects.filter(name='New Event Created').exists())
        self.assertEqual(Event.objects.get(name='New Event Created').event_category.count(), 2)

    def test_create_event_post_ajax_success(self):
        """Tes membuat event baru (POST) dengan request AJAX"""
        data = {
            'name': 'New AJAX Event',
            'location': 'jakarta_selatan',
            'capacity': 50,
            'event_status': 'coming_soon',
            'description': 'A valid test description.',
            'event_date': timezone.now(),
            'regist_deadline': timezone.now() + timezone.timedelta(days=1),
            'contact': '08123456789', 
            'coin': 100
        }
        response = self.client.post(reverse('event:create_event'), data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'success': True,
            'redirect_url': reverse('event_organizer:dashboard')
        })
        self.assertTrue(Event.objects.filter(name='New AJAX Event').exists())

    def test_create_event_post_invalid_form_ajax(self):
        """Tes membuat event (POST) dengan form tidak valid (AJAX)"""
        data = { 'name': '' } 
        response = self.client.post(reverse('event:create_event'), data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertFalse(json_response['success'])
        self.assertIn('errors', json_response)
        self.assertIn('name', json_response['errors'])

    def test_show_event_get(self):
        """Tes halaman detail event (GET)"""
        url = reverse('event:show_event', kwargs={'id': str(self.event.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'event_detail.html')
        self.assertEqual(response.context['event'], self.event)

    def test_edit_event_get_owner(self):
        """Tes halaman edit event (GET) oleh pemilik"""
        url = reverse('event:edit_event', kwargs={'id': self.event.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_event.html')
        self.assertEqual(response.context['event'], self.event)

    def test_edit_event_get_not_owner(self):
        """Tes halaman edit event (GET) oleh BUKAN pemilik (harus 403)"""
        other_user = User.objects.create_user(username='other', password='password123')
        EventOrganizer.objects.create(user=other_user)
        self.client.login(username='other', password='password123')
        url = reverse('event:edit_event', kwargs={'id': self.event.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_edit_event_post_owner_ajax(self):
        """Tes edit event (POST) oleh pemilik (AJAX)"""
        url = reverse('event:edit_event', kwargs={'id': self.event.id})
        data = {
            'name': 'Updated Event Name',
            'location': self.event.location,
            'capacity': self.event.capacity,
            'event_status': self.event.event_status,
        }
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, 'Updated Event Name')
        detail_url = reverse('event:show_event', kwargs={'id': self.event.id})
        self.assertJSONEqual(response.content, {
            'success': True,
            'redirect_url': detail_url
        })

    def test_delete_event_post_ajax_owner(self):
        """Tes hapus event (POST AJAX) oleh pemilik"""
        event_id = self.event.id
        url = reverse('event:delete_event', kwargs={'id': event_id})
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'success': True,
            'message': 'Event deleted successfully.'
        })
        self.assertFalse(Event.objects.filter(pk=event_id).exists())

    def test_delete_event_post_ajax_not_owner(self):
        """Tes hapus event (POST AJAX) oleh BUKAN pemilik"""
        other_user = User.objects.create_user(username='attacker', password='password123')
        EventOrganizer.objects.create(user=other_user)
        self.client.login(username='attacker', password='password123')
        
        event_id = self.event.id
        url = reverse('event:delete_event', kwargs={'id': event_id})
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 403)
        self.assertJSONEqual(response.content, {
            'success': False,
            'error': 'Not authorized'
        })
        self.assertTrue(Event.objects.filter(pk=event_id).exists())

    def test_delete_event_get_not_allowed(self):
        """Tes hapus event (GET), harus 400 Bad Request"""
        url = reverse('event:delete_event', kwargs={'id': self.event.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_show_json_endpoint(self):
        """Tes endpoint /json/"""
        response = self.client.get(reverse('event:show_json'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Test Event 1')
        self.assertEqual(data[0]['id'], str(self.event.id))
        self.assertIn('5K', data[0]['event_categories'])