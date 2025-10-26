import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.main.models import Runner, Attendance
from apps.main.forms import CustomUserCreationForm
from apps.event.models import Event # Diperlukan untuk tes partisipasi
from apps.event_organizer.models import EventOrganizer # Diperlukan untuk tes form

# Dapatkan model User kustom Anda
User = get_user_model()

class MainModelsTest(TestCase):
    """Tes untuk model User, Runner, dan Attendance."""

    def setUp(self):
        # Buat user untuk Runner
        self.user_runner = User.objects.create_user(
            username='testrunner',
            password='testpassword123',
            email='runner@example.com',
            role='runner'
        )
        self.runner = Runner.objects.create(
            user=self.user_runner,
            base_location='jakarta_pusat'
        )

        # Buat user untuk Event Organizer (diperlukan untuk Event)
        self.user_eo = User.objects.create_user(
            username='testeo',
            password='testpassword123',
            email='eo@example.com',
            role='event_organizer'
        )
        self.eo = EventOrganizer.objects.create(
            user=self.user_eo,
            base_location='depok'
        )

        # Buat sebuah Event
        self.event = Event.objects.create(
            user_eo=self.eo,
            name="Test Event",
            capacity=2,
            event_date=timezone.now() + timezone.timedelta(days=7),
            regist_deadline=timezone.now() + timezone.timedelta(days=5)
        )

    def test_runner_creation(self):
        """Memastikan Runner terhubung dengan User."""
        self.assertEqual(self.runner.user.username, 'testrunner')
        self.assertEqual(self.runner.base_location, 'jakarta_pusat')
        self.assertEqual(self.user_runner.runner, self.runner)

    def test_attendance_creation_and_str(self):
        """Memastikan Attendance dibuat dengan benar dan __str__ berfungsi."""
        attendance = Attendance.objects.create(
            runner=self.runner,
            event=self.event,
            status='attending'
        )
        self.assertEqual(attendance.runner, self.runner)
        self.assertEqual(attendance.event, self.event)
        self.assertEqual(attendance.status, 'attending')
        
        # Tes __str__
        expected_str = f"testrunner @ Test Event (attending)"
        self.assertEqual(str(attendance), expected_str)

    def test_attendance_unique_together(self):
        """Tes batasan unique_together ('runner', 'event')."""
        Attendance.objects.create(
            runner=self.runner,
            event=self.event,
            status='attending'
        )
        # Coba buat entri duplikat
        with self.assertRaises(Exception): # Harusnya IntegrityError
            Attendance.objects.create(
                runner=self.runner,
                event=self.event,
                status='canceled'
            )

class MainFormsTest(TestCase):
    """Tes untuk CustomUserCreationForm."""

    def test_form_create_runner_valid(self):
        """Tes pembuatan Runner yang valid melalui form."""
        form_data = {
            'username': 'newrunner',
            'password': 'newpassword123',
            'email': 'newrunner@example.com',
            'role': 'runner',
            'base_location': 'bekasi'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.role, 'runner')
        self.assertTrue(Runner.objects.filter(user=user).exists())
        self.assertEqual(user.runner.base_location, 'bekasi')

    def test_form_create_eo_valid(self):
        """Tes pembuatan Event Organizer yang valid melalui form."""
        form_data = {
            'username': 'neweo',
            'password': 'newpassword123',
            'email': 'neweo@example.com',
            'role': 'event_organizer',
            'base_location': 'bogor',
            'profile_picture': 'http://example.com/img.png'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.role, 'event_organizer')
        self.assertTrue(EventOrganizer.objects.filter(user=user).exists())
        self.assertEqual(user.eventorganizer.base_location, 'bogor')

    def test_form_runner_missing_location(self):
        """Tes validasi form jika Runner tidak menyertakan lokasi."""
        form_data = {
            'username': 'newrunner2',
            'password': 'newpassword123',
            'email': 'newrunner2@example.com',
            'role': 'runner',
            # 'base_location' sengaja dikosongkan
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('base_location', form.errors)
        self.assertEqual(form.errors['base_location'][0], 'Base location is required for runners.')

class MainViewsUnauthenticatedTest(TestCase):
    """Tes view untuk pengguna yang tidak login."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')

    def test_show_main_view(self):
        response = self.client.get(reverse('main:show_main'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main.html')

    def test_register_view_get(self):
        response = self.client.get(reverse('main:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        self.assertIsInstance(response.context['form'], CustomUserCreationForm)

    def test_login_view_get(self):
        response = self.client.get(reverse('main:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_show_user_redirects_to_login(self):
        """Tes halaman profil harus redirect ke login jika belum login."""
        response = self.client.get(reverse('main:show_user', args=[self.user.username]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('main:login')}?next={reverse('main:show_user', args=[self.user.username])}")

    def test_participate_event_redirects_to_login(self):
        response = self.client.get(reverse('main:participate_event', args=[self.user.username, '123e4567']))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('main:login')}?next={reverse('main:participate_event', args=[self.user.username, '123e4567'])}")


class MainViewsRunnerTest(TestCase):
    """Tes view untuk pengguna yang login sebagai Runner."""

    def setUp(self):
        self.user_runner = User.objects.create_user(
            username='testrunner',
            password='testpassword123',
            email='runner@example.com',
            role='runner'
        )
        self.runner = Runner.objects.create(
            user=self.user_runner,
            base_location='jakarta_pusat'
        )
        
        self.user_eo = User.objects.create_user(username='testeo', password='password', role='event_organizer')
        self.eo = EventOrganizer.objects.create(user=self.user_eo)

        self.event1 = Event.objects.create(user_eo=self.eo, name="Event 1", capacity=2, event_date=timezone.now() + timezone.timedelta(days=7), regist_deadline=timezone.now() + timezone.timedelta(days=5))
        self.event2 = Event.objects.create(user_eo=self.eo, name="Event 2", capacity=1, event_date=timezone.now() + timezone.timedelta(days=10), regist_deadline=timezone.now() + timezone.timedelta(days=5))

        self.client = Client()
        self.client.login(username='testrunner', password='testpassword123')

    def test_show_user_profile_self(self):
        """Tes Runner bisa melihat profilnya sendiri."""
        response = self.client.get(reverse('main:show_user', args=[self.user_runner.username]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'runner_detail.html')
        self.assertEqual(response.context['user'], self.user_runner)

    def test_show_user_profile_forbidden(self):
        """Tes Runner tidak bisa melihat profil user lain."""
        other_user = User.objects.create_user(username='otheruser', password='password', role='runner')
        Runner.objects.create(user=other_user)
        
        response = self.client.get(reverse('main:show_user', args=[other_user.username]))
        self.assertEqual(response.status_code, 302) # Redirect
        self.assertRedirects(response, reverse('main:show_main'))

    def test_edit_profile_runner_ajax_success(self):
        """Tes edit profil via AJAX berhasil."""
        url = reverse('main:edit_profile', args=[self.user_runner.username])
        data = {'username': 'newrunnername', 'base_location': 'jakarta_utara'}
        
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        
        # Cek database
        self.user_runner.refresh_from_db()
        self.runner.refresh_from_db()
        self.assertEqual(self.user_runner.username, 'newrunnername')
        self.assertEqual(self.runner.base_location, 'jakarta_utara')

        # Cek JSON response
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['username'], 'newrunnername')
        self.assertEqual(response_data['base_location'], 'Jakarta Utara') # Memakai get_display()
        self.assertIn('new_urls', response_data)

    def test_edit_profile_username_taken_ajax(self):
        """Tes edit profil via AJAX gagal karena username sudah ada."""
        User.objects.create_user(username='existinguser', password='password')
        url = reverse('main:edit_profile', args=[self.user_runner.username])
        data = {'username': 'existinguser', 'base_location': 'jakarta_utara'}
        
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Username already taken')

    def test_participate_in_event(self):
        """Tes Runner berhasil mendaftar event."""
        url = reverse('main:participate_event', args=[self.user_runner.username, self.event1.id])
        response = self.client.post(url)

        self.assertEqual(Attendance.objects.count(), 1)
        attendance = Attendance.objects.first()
        self.assertEqual(attendance.runner, self.runner)
        self.assertEqual(attendance.event, self.event1)
        
        self.event1.refresh_from_db()
        self.assertEqual(self.event1.total_participans, 1)
        
        self.assertRedirects(response, reverse('main:show_user', args=[self.user_runner.username]))

    def test_participate_in_full_event(self):
        """Tes Runner gagal mendaftar event yang penuh."""
        # Buat user lain dan daftarkan
        other_user = User.objects.create_user(username='otherrunner', password='password', role='runner')
        other_runner = Runner.objects.create(user=other_user)
        # Event2 kapasitasnya 1
        Attendance.objects.create(runner=other_runner, event=self.event2)
        self.event2.increment_participans() # Event sekarang penuh
        
        url = reverse('main:participate_event', args=[self.user_runner.username, self.event2.id])
        response = self.client.post(url)

        self.assertEqual(Attendance.objects.count(), 1) # Hanya ada 1 dari other_runner
        self.assertFalse(Attendance.objects.filter(runner=self.runner, event=self.event2).exists())
        self.assertRedirects(response, reverse('main:show_user', args=[self.user_runner.username]))

    def test_cancel_event(self):
        """Tes Runner berhasil membatalkan event."""
        # Daftarkan dulu
        Attendance.objects.create(runner=self.runner, event=self.event1, status='attending')
        self.event1.increment_participans()
        self.assertEqual(self.event1.total_participans, 1)

        # Batalkan
        url = reverse('main:cancel_event', args=[self.user_runner.username, self.event1.id])
        response = self.client.post(url)

        attendance = Attendance.objects.get(runner=self.runner, event=self.event1)
        self.assertEqual(attendance.status, 'canceled')
        
        self.event1.refresh_from_db()
        self.assertEqual(self.event1.total_participans, 0)
        self.assertRedirects(response, reverse('main:show_user', args=[self.user_runner.username]))


class MainViewsEOTest(TestCase):
    """Tes view untuk pengguna yang login sebagai Event Organizer."""
    
    def setUp(self):
        self.user_eo = User.objects.create_user(
            username='testeo',
            password='testpassword123',
            email='eo@example.com',
            role='event_organizer'
        )
        self.eo = EventOrganizer.objects.create(user=self.user_eo)
        self.event = Event.objects.create(user_eo=self.eo, name="EO's Event", capacity=10, event_date=timezone.now() + timezone.timedelta(days=7), regist_deadline=timezone.now() + timezone.timedelta(days=5))

        self.client = Client()
        self.client.login(username='testeo', password='testpassword123')

    def test_show_user_profile_eo(self):
        """Tes EO bisa melihat profilnya sendiri (menggunakan template profile.html)."""
        response = self.client.get(reverse('main:show_user', args=[self.user_eo.username]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html') # Bukan runner_detail.html
        self.assertEqual(response.context['user'], self.user_eo)
        
    def test_eo_cannot_participate_event(self):
        """Tes EO tidak bisa mendaftar event."""
        url = reverse('main:participate_event', args=[self.user_eo.username, self.event.id])
        response = self.client.post(url)
        
        self.assertEqual(Attendance.objects.count(), 0)
        self.assertRedirects(response, reverse('main:show_main'))

    def test_eo_cannot_edit_profile_runner_view(self):
        """Tes EO tidak bisa mengakses view edit_profile_runner."""
        url = reverse('main:edit_profile', args=[self.user_eo.username])
        data = {'username': 'neweoname', 'base_location': 'jakarta_utara'}
        
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 403) # Forbidden
        self.assertEqual(response.json()['error'], 'You are not authorized to edit this profile.')