import json
from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.utils import timezone 

#
from apps.main.models import User, Runner, Attendance
from apps.event.models import Event, EventCategory
from apps.review.models import Review 


UserModel = get_user_model()

class BaseTestCase(TestCase):
    """
    Setup data pengujian dasar yang akan digunakan di semua kelas pengujian.
    """
    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        cls.password = 'Testpass123!'
        cls.now = timezone.now()


        cls.user = UserModel.objects.create_user(
            username='testrunner',
            email='testrunner@example.com',
            password=cls.password,
            role='runner'
        )

        cls.runner = Runner.objects.create(user=cls.user, base_location='jakarta_pusat')

        cls.other_user = UserModel.objects.create_user(
            username='otherrunner',
            email='other@example.com',
            password=cls.password,
            role='runner'
        )
        cls.other_runner = Runner.objects.create(user=cls.other_user, base_location='bogor')

        cls.org_user = UserModel.objects.create_user(
            username='testorg',
            email='testorg@example.com',
            password=cls.password,
            role='event_organizer'
        )
        

        cls.cat_5k = EventCategory.objects.create(category='5k')
        cls.cat_10k = EventCategory.objects.create(category='10k')


        cls.event_coming = Event.objects.create(
            name='Upcoming Run',
            event_date=cls.now + timedelta(days=10),
            location='jakarta_pusat',
            event_status='coming_soon',
            capacity=100,
            total_participans=1 
        )
        cls.event_coming.event_category.add(cls.cat_5k)

        cls.event_finished = Event.objects.create(
            name='Finished Run',
            event_date=cls.now - timedelta(days=10),
            event_status='finished',
            location='bogor',
            capacity=50,
            total_participans=1
        )
        cls.event_finished.event_category.add(cls.cat_10k)

        cls.event_full = Event.objects.create(
            name='Full Run',
            event_date=cls.now + timedelta(days=20),
            event_status='coming_soon',
            location='jakarta_pusat',
            capacity=1,
            total_participans=1 
        )
        cls.event_full.event_category.add(cls.cat_5k)
        
        cls.event_to_join = Event.objects.create(
            name='Joinable Run',
            event_date=cls.now + timedelta(days=5),
            event_status='coming_soon',
            location='jakarta_pusat',
            capacity=100,
            total_participans=0 
        )
        cls.event_to_join.event_category.add(cls.cat_5k)


        cls.att_coming = Attendance.objects.create(
            runner=cls.runner,
            event=cls.event_coming,
            status='attending',
            category=cls.cat_5k
        )
        cls.att_finished = Attendance.objects.create(
            runner=cls.runner,
            event=cls.event_finished,
            status='finished',
            category=cls.cat_10k
        )
        Attendance.objects.create(
            runner=cls.other_runner,
            event=cls.event_full,
            status='attending',
            category=cls.cat_5k
        )
        
        Review.objects.create(
            runner=cls.runner,
            event=cls.event_finished,
        )

        cls.main_url = reverse('main:show_main')
        cls.register_url = reverse('main:register')
        cls.login_url = reverse('main:login')
        cls.logout_url = reverse('main:logout')
        cls.user_profile_url = reverse('main:show_user', args=[cls.user.username])
        cls.other_user_profile_url = reverse('main:show_user', args=[cls.other_user.username])
        cls.org_profile_url = reverse('main:show_user', args=[cls.org_user.username])
        cls.edit_profile_url = reverse('main:edit_profile', args=[cls.user.username])
        cls.change_password_url = reverse('main:change_password', args=[cls.user.username])
        cls.cancel_event_url = reverse('main:cancel_event', args=[cls.user.username, cls.event_coming.id])
        cls.participate_event_url = reverse('main:participate_event', args=[cls.user.username, cls.event_to_join.id, cls.cat_5k.category])
        
        try:
            cls.event_detail_url = reverse('event:event_detail', args=[cls.event_to_join.id])
        except Exception:
            cls.event_detail_url = None 


class MainViewTests(BaseTestCase):
    """Tes untuk view utama, registrasi, login, dan logout."""

    def test_show_main_get(self):
        response = self.client.get(self.main_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main.html')
        self.assertIn('events', response.context)
        self.assertEqual(len(response.context['events']), 4)

    def test_show_main_filter_location(self):
        response = self.client.get(self.main_url, {'location': 'jakarta_pusat'})
        self.assertEqual(response.status_code, 200)
        events_in_context = list(response.context['events'])
        self.assertEqual(len(events_in_context), 3)
        self.assertTrue(all(e.location == 'jakarta_pusat' for e in events_in_context))

    def test_show_main_filter_category(self):
        response = self.client.get(self.main_url, {'category': '10k'})
        self.assertEqual(response.status_code, 200)
        events_in_context = list(response.context['events'])
        self.assertEqual(len(events_in_context), 1)
        self.assertEqual(events_in_context[0].name, 'Finished Run')
        
    def test_show_main_filter_status(self):
        response = self.client.get(self.main_url, {'status': 'finished'})
        self.assertEqual(response.status_code, 200)
        events_in_context = list(response.context['events'])
        self.assertEqual(len(events_in_context), 1)
        self.assertEqual(events_in_context[0].name, 'Finished Run')

    def test_register_get(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        self.assertIn('form', response.context)

    def test_register_post_success(self):
        user_count_before = UserModel.objects.count()
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': self.password,
            'password2': self.password,
        })
        user_count_after = UserModel.objects.count()
        self.assertEqual(user_count_after, user_count_before + 1)
        self.assertRedirects(response, self.login_url)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Akun berhasil dibuat! Silakan login.")

    def test_register_post_email_exists(self):
        user_count_before = UserModel.objects.count()
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': self.user.email,
            'password': self.password,
            'password2': self.password,
            'role': 'runner'
        })
        user_count_after = UserModel.objects.count()
        self.assertEqual(user_count_after, user_count_before)
        self.assertRedirects(response, self.register_url)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "User with this Email already exists.")

    def test_login_user_get(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_login_user_post_success(self):
        response = self.client.post(self.login_url, {
            'username': self.user.username,
            'password': self.password
        })
        self.assertRedirects(response, self.main_url)
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(self.client.session['_auth_user_id'], str(self.user.id))
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn(f'Welcome back, {self.user.username}!', str(messages[0]))

    def test_login_user_post_fail(self):
        response = self.client.post(self.login_url, {
            'username': self.user.username,
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200) 
        self.assertTemplateUsed(response, 'login.html')
        self.assertNotIn('_auth_user_id', self.client.session) 

    def test_logout_user(self):
        self.client.login(username=self.user.username, password=self.password)
        self.assertIn('_auth_user_id', self.client.session)
        
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, self.login_url)
        self.assertNotIn('_auth_user_id', self.client.session) 
        
        self.assertEqual(response.cookies['last_login'].value, '')
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn(f'See u later, {self.user.username}!', str(messages[0]))


class UserProfileViewTests(BaseTestCase):
    """Tes untuk view yang terkait dengan profil pengguna: show, edit, change_password."""

    def setUp(self):
        self.client.login(username=self.user.username, password=self.password)

    def test_show_user_self_profile_runner(self):
        response = self.client.get(self.user_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'runner_detail.html')
        self.assertEqual(response.context['user'], self.user)
        self.assertIn('attendance_list', response.context)

    def test_show_user_unauthorized_profile(self):
        # Pengguna mencoba melihat profil pengguna lain
        response = self.client.get(self.other_user_profile_url)
        self.assertRedirects(response, self.main_url)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "You are not authorized to view this profile.")

    def test_show_user_not_logged_in(self):
        self.client.logout()
        response = self.client.get(self.user_profile_url)
        
        self.assertRedirects(response, f'{self.login_url}?next={self.user_profile_url}')

    def test_show_user_profile_not_runner(self):

        self.client.login(username=self.org_user.username, password=self.password)
        response = self.client.get(self.org_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html') 
        self.assertEqual(response.context['user'], self.org_user)
        self.assertNotIn('attendance_list', response.context)

    def test_show_user_updates_event_and_attendance_status(self):
        
        past_event = Event.objects.create(
            name='Past Event',
            event_date=self.now - timedelta(days=1),
            event_status='coming_soon', 
            capacity=10,
            total_participans=1
        )
        past_event.event_category.add(self.cat_5k)
        
        
        past_attendance = Attendance.objects.create(
            runner=self.runner,
            event=past_event,
            status='attending', 
            category=self.cat_5k
        )
        
        self.assertEqual(past_event.event_status, 'coming_soon')
        self.assertEqual(past_attendance.status, 'attending')
        
        
        self.client.get(self.user_profile_url)
        
        past_event.refresh_from_db()
        past_attendance.refresh_from_db()
        
        self.assertEqual(past_event.event_status, 'finished')
        self.assertEqual(past_attendance.status, 'finished')

    def test_edit_profile_runner_success_ajax(self):
        new_username = 'newrunnername'
        new_location = 'bogor'
        
        response = self.client.post(
            self.edit_profile_url,
            data={'username': new_username, 'base_location': new_location},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest' 
        )
        
        self.assertEqual(response.status_code, 200)
        
        
        self.user.refresh_from_db()
        self.runner.refresh_from_db()
        self.assertEqual(self.user.username, new_username)
        self.assertEqual(self.runner.base_location, new_location)

        
        json_response = json.loads(response.content)
        self.assertTrue(json_response['success'])
        self.assertEqual(json_response['username'], new_username)
        self.assertEqual(json_response['base_location'], 'Bogor') 
        self.assertIn('new_urls', json_response)
        
    def test_edit_profile_username_taken_ajax(self):
        response = self.client.post(
            self.edit_profile_url,
            data={'username': self.other_user.username, 'base_location': 'jakarta_pusat'}, 
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        json_response = json.loads(response.content)
        self.assertFalse(json_response.get('success', False))
        self.assertEqual(json_response['error'], 'Username already taken')

    def test_edit_profile_invalid_method_get(self):
        response = self.client.get(self.edit_profile_url)
        self.assertEqual(response.status_code, 405) 
        
    def test_edit_profile_unauthorized_ajax(self):
        
        edit_other_url = reverse('main:edit_profile', args=[self.other_user.username])
        response = self.client.post(
            edit_other_url,
            data={'username': 'hacked', 'base_location': 'jakarta_pusat'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 403)
        
    def test_change_password_get(self):
        response = self.client.get(self.change_password_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'change_password.html')
        self.assertIn('form', response.context)

    def test_change_password_post_success_non_ajax(self):
        new_password = 'NewPassword123!'
        response = self.client.post(self.change_password_url, {
            'old_password': self.password,
            'new_password1': new_password,
            'new_password2': new_password,
        })
        
        
        self.assertRedirects(response, self.logout_url, fetch_redirect_response=False)
        
        
        self.client.logout()
        login_response = self.client.post(self.login_url, {
            'username': self.user.username,
            'password': new_password
        })
        self.assertRedirects(login_response, self.main_url) 

    def test_change_password_post_fail_non_ajax(self):
        response = self.client.post(self.change_password_url, {
            'old_password': 'wrongpassword', 
            'new_password1': 'NewPassword123!',
            'new_password2': 'NewPassword123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'change_password.html')
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)

    def test_change_password_ajax_success(self):
        new_password = 'NewPassword123!'
        response = self.client.post(
            self.change_password_url, 
            {
                'old_password': self.password,
                'new_password1': new_password,
                'new_password2': new_password,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertTrue(json_response['success'])

    def test_change_password_ajax_fail_wrong_old_pass(self):
        response = self.client.post(
            self.change_password_url, 
            {
                'old_password': 'wrongpassword', 
                'new_password1': 'NewPassword123!',
                'new_password2': 'NewPassword123!',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertFalse(json_response['success'])
        self.assertIn('message', json_response)


class EventInteractionViewTests(BaseTestCase):
    """Tes untuk mendaftar (participate) dan membatalkan (cancel) event."""
    
    def setUp(self):
        self.client.login(username=self.user.username, password=self.password)

    
    def test_participate_event_success(self):
        """
        Tes pendaftaran berhasil. 
        Juga menguji bug di view Anda di mana 'else' block
        selalu berjalan, mengirim pesan error setelah pesan sukses.
        """
        event_participants_before = self.event_to_join.total_participans
        attendance_count_before = Attendance.objects.filter(runner=self.runner).count()
        
        response = self.client.get(self.participate_event_url)
        
        self.assertRedirects(response, self.user_profile_url)
        
        
        self.event_to_join.refresh_from_db()
        self.assertEqual(self.event_to_join.total_participans, event_participants_before + 1)
        
        attendance_count_after = Attendance.objects.filter(runner=self.runner).count()
        self.assertEqual(attendance_count_after, attendance_count_before + 1)
        
        new_attendance = Attendance.objects.get(runner=self.runner, event=self.event_to_join)
        self.assertEqual(new_attendance.status, 'attending')
        self.assertEqual(new_attendance.category, self.cat_5k)
        
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn(f"You are now registered for {self.event_to_join.name}", str(messages[0]))

    def test_participate_event_already_registered(self):
        
        url = reverse('main:participate_event', args=[self.user.username, self.event_coming.id, self.cat_5k.category])
        response = self.client.get(url)
        
        self.assertRedirects(response, self.user_profile_url)
        
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn(f"You are already registered for {self.event_coming.name}", str(messages[0]))

    def test_participate_event_full(self):
        url = reverse('main:participate_event', args=[self.user.username, self.event_full.id, self.cat_5k.category])
        response = self.client.get(url)
        
        self.assertRedirects(response, self.user_profile_url) 
        
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn(f"Sorry, {self.event_full.name} is already full.", str(messages[0]))

    def test_participate_event_invalid_category(self):
        if not self.event_detail_url:
            self.skipTest("URL 'event:event_detail' tidak terdefinisi.")
            
        url = reverse('main:participate_event', args=[self.user.username, self.event_to_join.id, 'INVALID_CAT'])
        response = self.client.get(url)
        
        self.assertRedirects(response, self.event_detail_url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("Invalid category selected for this event.", str(messages[0]))

    def test_participate_event_reregister(self):
        
        self.att_coming.status = 'canceled'
        self.att_coming.save()
        self.event_coming.decrement_participans() 
        self.event_coming.refresh_from_db()
        self.assertEqual(self.event_coming.total_participans, 0)
        
        
        url = reverse('main:participate_event', args=[self.user.username, self.event_coming.id, self.cat_5k.category])
        response = self.client.get(url)
        
        self.assertRedirects(response, self.user_profile_url)
        
        self.att_coming.refresh_from_db()
        self.event_coming.refresh_from_db()
        
        self.assertEqual(self.att_coming.status, 'attending') 
        self.assertEqual(self.event_coming.total_participans, 1) 
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1) 
        self.assertIn(f"You have re-registered for {self.event_coming.name}.", str(messages[0]))

    

    def test_cancel_event_success(self):
        event_participants_before = self.event_coming.total_participans
        self.assertEqual(self.att_coming.status, 'attending')
        
        response = self.client.get(self.cancel_event_url)
        
        self.assertRedirects(response, self.user_profile_url)
        
        
        self.att_coming.refresh_from_db()
        self.event_coming.refresh_from_db()
        
        self.assertEqual(self.att_coming.status, 'canceled')
        self.assertEqual(self.event_coming.total_participans, event_participants_before - 1)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn(f"You have successfully canceled your attendance for {self.event_coming.name}.", str(messages[0]))

    def test_cancel_event_already_canceled(self):
        self.att_coming.status = 'canceled'
        self.att_coming.save()
        
        response = self.client.get(self.cancel_event_url)
        self.assertRedirects(response, self.user_profile_url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("You have already canceled this event.", str(messages[0]))

    def test_cancel_event_finished(self):
        url = reverse('main:cancel_event', args=[self.user.username, self.event_finished.id])
        response = self.client.get(url)
        
        self.assertRedirects(response, self.user_profile_url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("You cannot cancel an event that is already finished.", str(messages[0]))
        
        self.att_finished.refresh_from_db()
        self.assertEqual(self.att_finished.status, 'finished')

    def test_cancel_event_not_registered(self):
        
        url = reverse('main:cancel_event', args=[self.user.username, self.event_to_join.id])
        response = self.client.get(url)
        
        self.assertRedirects(response, self.user_profile_url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("You are not registered for this event.", str(messages[0]))

    def test_cancel_event_unauthorized_other_user(self):
        
        url = reverse('main:cancel_event', args=[self.other_user.username, self.event_coming.id])
        response = self.client.get(url)
        
        
        self.assertRedirects(response, self.main_url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("You are not authorized to perform this action.", str(messages[0]))
