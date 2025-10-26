from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.event_organizer.models import EventOrganizer
from apps.event.models import Event, EventCategory
from apps.main.models import Runner 
from .forms import EventForm
import json
from django.utils import timezone
from datetime import timedelta

User = get_user_model()
class EventViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='eo', password='password', email="testeo@gmail.com")
        self.event_organizer = EventOrganizer.objects.create(user=self.user)
        self.client.login(username='eo', password='password')

        self.event = Event.objects.create(
            user_eo=self.event_organizer,
            name='Test Event',
            description='Test Desc',
            location='jakarta',
            event_status='upcoming',
            event_date=timezone.now() + timedelta(days=10),
            regist_deadline=timezone.now() + timedelta(days=5),
            contact='08123456789',
            capacity=100,
            total_participans=0,
            coin=50,
        )

    def test_create_event_get(self):
        """GET create_event harus menampilkan form"""
        response = self.client.get(reverse('event:create_event'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_event.html')

    def test_create_event_post_valid(self):
        """POST valid create_event berhasil redirect"""
        form_data = {
            'name': 'New Event',
            'description': 'Description',
            'location': 'jakarta',
            'event_status': 'upcoming',
            'event_date': (timezone.now() + timedelta(days=3)).date(),
            'regist_deadline': (timezone.now() + timedelta(days=2)).date(),
            'contact': '08123456789',
            'capacity': 50,
            'coin': 20,
            'event_category': []
        }
        response = self.client.post(reverse('event:create_event'), data=form_data)
        self.assertEqual(response.status_code, 302) 
        self.assertTrue(Event.objects.filter(name='New Event').exists())

    def test_edit_event_get(self):
        """GET edit_event harus menampilkan form"""
        url = reverse('event:edit_event', args=[self.event.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_event.html')

    def test_edit_event_post_valid(self):
        """POST valid edit_event berhasil ubah data"""
        url = reverse('event:edit_event', args=[self.event.id])
        data = {
            'name': 'Edited Event',
            'description': 'Updated',
            'location': 'jakarta',
            'event_status': 'upcoming',
            'event_date': (timezone.now() + timedelta(days=2)).date(),
            'regist_deadline': (timezone.now() + timedelta(days=1)).date(),
            'contact': '08123456789',
            'capacity': 100,
            'coin': 100,
            'event_category': []
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, 'Edited Event')

    def test_delete_event_post(self):
        """POST delete_event menghapus event"""
        url = reverse('event:delete_event', args=[self.event.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Event.objects.filter(id=self.event.id).exists())

    def test_show_event_view(self):
        """show_event menampilkan detail event"""
        url = reverse('event:show_event', args=[self.event.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.name)

    def test_show_json(self):
        """show_json mengembalikan JSON"""
        url = reverse('event:show_json')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_show_xml(self):
        """show_xml mengembalikan XML"""
        url = reverse('event:show_xml')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')

    def test_show_json_by_id(self):
        """show_json_by_id mengembalikan JSON untuk satu event"""
        url = reverse('event:show_json_by_id', args=[self.event.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_show_xml_by_id(self):
        """show_xml_by_id mengembalikan XML untuk satu event"""
        url = reverse('event:show_xml_by_id', args=[self.event.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')
    def test_create_event_ajax_success(self):
        """POST AJAX create_event mengembalikan JSON sukses"""
        form_data = {
            'name': 'Ajax Event',
            'description': 'Ajax Desc',
            'location': 'jakarta',
            'event_status': 'upcoming',
            'event_date': (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
            'regist_deadline': (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'contact': '08123456789',
            'capacity': 30,
            'coin': 10
        }
        response = self.client.post(
            reverse('event:create_event'),
            data=form_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        self.assertTrue(json_data['success'])

    def test_create_event_invalid_form(self):
        """POST invalid create_event"""
        response = self.client.post(reverse('event:create_event'), data={})
        self.assertEqual(response.status_code, 200) 

    def test_edit_event_permission_denied(self):
        """User lain tidak boleh edit event"""
        other_user = User.objects.create_user(username='other', password='password')
        self.client.login(username='other', password='password')
        url = reverse('event:edit_event', args=[self.event.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_delete_event_ajax(self):
        """Hapus event via AJAX"""
        event = Event.objects.create(
            user_eo=self.event_organizer,
            name='To Delete',
            description='...',
            location='jakarta',
            event_status='upcoming',
            event_date=timezone.now() + timedelta(days=1),
            regist_deadline=timezone.now(),
            contact='0812',
            capacity=10,
            coin=10
        )
        url = reverse('event:delete_event', args=[event.id])
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Event.objects.filter(id=event.id).exists())

    def test_delete_event_invalid_method(self):
        """GET delete_event harus 400"""
        url = reverse('event:delete_event', args=[self.event.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_show_json_by_id_not_found(self):
        """show_json_by_id harus 404 jika event tidak ditemukan"""
        url = reverse('event:show_json_by_id', args=[9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

