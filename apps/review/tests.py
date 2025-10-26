# apps/review/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import json

from apps.review.models import Review
from apps.event.models import Event, EventCategory
from apps.main.models import Runner, Attendance
from apps.event_organizer.models import EventOrganizer

User = get_user_model()


class ReviewViewsTestCase(TestCase):
    """Test cases for review views"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.runner_user = User.objects.create_user(
            username='testrunner',
            email='runner@test.com',
            password='testpass123',
            role='runner'
        )
        
        self.eo_user = User.objects.create_user(
            username='testeo',
            email='eo@test.com',
            password='testpass123',
            role='event_organizer'
        )
        
        self.other_runner_user = User.objects.create_user(
            username='otherrunner',
            email='other@test.com',
            password='testpass123',
            role='runner'
        )
        
        # Create runner profiles
        self.runner = Runner.objects.create(
            user=self.runner_user,
            base_location='jakarta_selatan'
        )
        
        self.other_runner = Runner.objects.create(
            user=self.other_runner_user,
            base_location='jakarta_pusat'
        )
        
        # Create event organizer profile
        self.eo = EventOrganizer.objects.create(
            user=self.eo_user,
            base_location='jakarta_selatan'
        )
        
        # Create event category
        self.category = EventCategory.objects.create(
            category='5k'
        )
        
        # Create event
        self.event = Event.objects.create(
            user_eo=self.eo,
            name='Test Marathon',
            description='Test Description',
            event_date=timezone.now() + timedelta(days=30),
            regist_deadline=timezone.now() + timedelta(days=20),
            location='jakarta_selatan',
            capacity=100,
            contact='08123456789'
        )
        self.event.event_category.add(self.category)
        
        # Create attendance
        self.attendance = Attendance.objects.create(
            runner=self.runner,
            event=self.event,
            category=self.category,
            status='finished'
        )
        
        # Set up client
        self.client = Client()
    
    # ==================== CREATE REVIEW TESTS ====================
    
    def test_create_review_success(self):
        """Test successful review creation"""
        self.client.login(username='testrunner', password='testpass123')
        
        data = {
            'rating': 5,
            'review_text': 'Great event! Well organized.'
        }
        
        response = self.client.post(
            reverse('review:create_review', args=[self.event.id]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['message'], 'Review posted successfully')
        
        # Verify review was created
        review = Review.objects.filter(runner=self.runner, event=self.event).first()
        self.assertIsNotNone(review)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.review_text, 'Great event! Well organized.')
    
    def test_create_review_without_attendance(self):
        """Test creating review without attending event"""
        self.client.login(username='otherrunner', password='testpass123')
        
        data = {
            'rating': 4,
            'review_text': 'Good event'
        }
        
        response = self.client.post(
            reverse('review:create_review', args=[self.event.id]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('must attend this event', response_data['message'])
    
    def test_create_review_duplicate(self):
        """Test creating duplicate review"""
        Review.objects.create(
            runner=self.runner,
            event=self.event,
            event_organizer=self.eo,
            rating=5,
            review_text='First review'
        )
        
        self.client.login(username='testrunner', password='testpass123')
        
        data = {
            'rating': 4,
            'review_text': 'Second review'
        }
        
        response = self.client.post(
            reverse('review:create_review', args=[self.event.id]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('already reviewed', response_data['message'])
    
    def test_create_review_invalid_rating_high(self):
        """Test creating review with rating > 5"""
        self.client.login(username='testrunner', password='testpass123')
        
        data = {'rating': 6, 'review_text': 'Test'}
        response = self.client.post(
            reverse('review:create_review', args=[self.event.id]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Rating must be between 1 and 5', response_data['message'])
    
    def test_create_review_invalid_rating_low(self):
        """Test creating review with rating < 1"""
        self.client.login(username='testrunner', password='testpass123')
        
        data = {'rating': 0, 'review_text': 'Test'}
        response = self.client.post(
            reverse('review:create_review', args=[self.event.id]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
    
    def test_create_review_no_rating(self):
        """Test creating review without rating"""
        self.client.login(username='testrunner', password='testpass123')
        
        data = {'review_text': 'Test without rating'}
        response = self.client.post(
            reverse('review:create_review', args=[self.event.id]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Rating must be between 1 and 5', response_data['message'])
    
    def test_create_review_without_login(self):
        """Test creating review without login"""
        data = {
            'rating': 5,
            'review_text': 'Test'
        }
        
        response = self.client.post(
            reverse('review:create_review', args=[self.event.id]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_create_review_with_attending_status(self):
        """Test creating review with 'attending' status"""
        attendance2 = Attendance.objects.create(
            runner=self.other_runner,
            event=self.event,
            category=self.category,
            status='attending'
        )
        
        self.client.login(username='otherrunner', password='testpass123')
        
        data = {
            'rating': 5,
            'review_text': 'Looking forward to it!'
        }
        
        response = self.client.post(
            reverse('review:create_review', args=[self.event.id]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
    
    def test_create_review_invalid_json(self):
        """Test creating review with invalid JSON"""
        self.client.login(username='testrunner', password='testpass123')
        
        response = self.client.post(
            reverse('review:create_review', args=[self.event.id]),
            data='invalid json{',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Invalid JSON', response_data['message'])
    
    def test_create_review_runner_does_not_exist(self):
        """Test creating review when runner profile doesn't exist"""
        # Create user without runner profile
        user_without_runner = User.objects.create_user(
            username='norunner',
            email='norunner@test.com',
            password='testpass123',
            role='runner'
        )
        
        self.client.login(username='norunner', password='testpass123')
        
        data = {
            'rating': 5,
            'review_text': 'Test'
        }
        
        response = self.client.post(
            reverse('review:create_review', args=[self.event.id]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Runner profile not found', response_data['message'])
    
    def test_create_review_event_not_found(self):
        """Test creating review for non-existent event"""
        self.client.login(username='testrunner', password='testpass123')
        
        data = {
            'rating': 5,
            'review_text': 'Test'
        }
        
        # Use a random UUID
        import uuid
        fake_uuid = uuid.uuid4()
        
        response = self.client.post(
            reverse('review:create_review', args=[fake_uuid]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_create_review_empty_review_text(self):
        """Test creating review with empty review text"""
        self.client.login(username='testrunner', password='testpass123')
        
        data = {
            'rating': 5,
            'review_text': '   '  # Only whitespace
        }
        
        response = self.client.post(
            reverse('review:create_review', args=[self.event.id]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        # Verify whitespace was stripped
        self.assertEqual(response_data['review']['review_text'], '')
    
    # ==================== EDIT REVIEW TESTS ====================
    
    def test_edit_review_success(self):
        """Test successful review edit"""
        review = Review.objects.create(
            runner=self.runner,
            event=self.event,
            event_organizer=self.eo,
            rating=4,
            review_text='Original review'
        )
        
        self.client.login(username='testrunner', password='testpass123')
        
        data = {
            'rating': 5,
            'review_text': 'Updated review'
        }
        
        response = self.client.post(
            reverse('review:edit_review', args=[review.id]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['message'], 'Review updated successfully')
        
        # Verify review was updated
        review.refresh_from_db()
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.review_text, 'Updated review')
    
    def test_edit_review_unauthorized(self):
        """Test editing review by different user"""
        review = Review.objects.create(
            runner=self.runner,
            event=self.event,
            event_organizer=self.eo,
            rating=4,
            review_text='Original review'
        )
        
        self.client.login(username='otherrunner', password='testpass123')
        
        data = {
            'rating': 5,
            'review_text': 'Hacked review'
        }
        
        response = self.client.post(
            reverse('review:edit_review', args=[review.id]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('not authorized', response_data['message'])
    
    def test_edit_review_invalid_rating_high(self):
        """Test editing review with rating > 5"""
        review = Review.objects.create(
            runner=self.runner,
            event=self.event,
            event_organizer=self.eo,
            rating=4,
            review_text='Original review'
        )
        
        self.client.login(username='testrunner', password='testpass123')
        
        data = {
            'rating': 10,
            'review_text': 'Updated review'
        }
        
        response = self.client.post(
            reverse('review:edit_review', args=[review.id]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
    
    def test_edit_review_invalid_rating_low(self):
        """Test editing review with rating < 1"""
        review = Review.objects.create(
            runner=self.runner,
            event=self.event,
            event_organizer=self.eo,
            rating=4,
            review_text='Original review'
        )
        
        self.client.login(username='testrunner', password='testpass123')
        
        data = {
            'rating': -1,
            'review_text': 'Updated review'
        }
        
        response = self.client.post(
            reverse('review:edit_review', args=[review.id]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_edit_review_no_rating(self):
        """Test editing review without rating"""
        review = Review.objects.create(
            runner=self.runner,
            event=self.event,
            event_organizer=self.eo,
            rating=4,
            review_text='Original review'
        )
        
        self.client.login(username='testrunner', password='testpass123')
        
        data = {
            'review_text': 'Updated without rating'
        }
        
        response = self.client.post(
            reverse('review:edit_review', args=[review.id]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
    
    def test_edit_review_invalid_json(self):
        """Test editing review with invalid JSON"""
        review = Review.objects.create(
            runner=self.runner,
            event=self.event,
            event_organizer=self.eo,
            rating=4,
            review_text='Original review'
        )
        
        self.client.login(username='testrunner', password='testpass123')
        
        response = self.client.post(
            reverse('review:edit_review', args=[review.id]),
            data='invalid json{',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Invalid JSON', response_data['message'])
    
    def test_edit_review_not_found(self):
        """Test editing non-existent review"""
        self.client.login(username='testrunner', password='testpass123')
        
        data = {
            'rating': 5,
            'review_text': 'Test'
        }
        
        response = self.client.post(
            reverse('review:edit_review', args=[99999]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_edit_review_without_login(self):
        """Test editing review without login"""
        review = Review.objects.create(
            runner=self.runner,
            event=self.event,
            event_organizer=self.eo,
            rating=4,
            review_text='Original review'
        )
        
        data = {
            'rating': 5,
            'review_text': 'Updated'
        }
        
        response = self.client.post(
            reverse('review:edit_review', args=[review.id]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    # ==================== DELETE REVIEW TESTS ====================
    
    def test_delete_review_success(self):
        """Test successful review deletion"""
        review = Review.objects.create(
            runner=self.runner,
            event=self.event,
            event_organizer=self.eo,
            rating=4,
            review_text='Review to delete'
        )
        
        self.client.login(username='testrunner', password='testpass123')
        
        response = self.client.post(
            reverse('review:delete_review', args=[review.id])
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['message'], 'Review deleted successfully')
        
        # Verify review was deleted
        self.assertFalse(Review.objects.filter(id=review.id).exists())
    
    def test_delete_review_unauthorized(self):
        """Test deleting review by different user"""
        review = Review.objects.create(
            runner=self.runner,
            event=self.event,
            event_organizer=self.eo,
            rating=4,
            review_text='Review to delete'
        )
        
        self.client.login(username='otherrunner', password='testpass123')
        
        response = self.client.post(
            reverse('review:delete_review', args=[review.id])
        )
        
        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('not authorized', response_data['message'])
        
        # Verify review still exists
        self.assertTrue(Review.objects.filter(id=review.id).exists())
    
    def test_delete_review_not_found(self):
        """Test deleting non-existent review"""
        self.client.login(username='testrunner', password='testpass123')
        
        response = self.client.post(
            reverse('review:delete_review', args=[99999])
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_delete_review_without_login(self):
        """Test deleting review without login"""
        review = Review.objects.create(
            runner=self.runner,
            event=self.event,
            event_organizer=self.eo,
            rating=4,
            review_text='Review to delete'
        )
        
        response = self.client.post(
            reverse('review:delete_review', args=[review.id])
        )
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)


class ReviewModelTestCase(TestCase):
    """Test cases for Review model"""
    
    def setUp(self):
        """Set up test data"""
        self.runner_user = User.objects.create_user(
            username='testrunner',
            email='runner@test.com',
            password='testpass123',
            role='runner'
        )
        
        self.eo_user = User.objects.create_user(
            username='testeo',
            email='eo@test.com',
            password='testpass123',
            role='event_organizer'
        )
        
        self.runner = Runner.objects.create(
            user=self.runner_user,
            base_location='jakarta_selatan'
        )
        
        self.eo = EventOrganizer.objects.create(
            user=self.eo_user,
            base_location='jakarta_selatan'
        )
        
        self.category = EventCategory.objects.create(
            category='5k'
        )
        
        self.event = Event.objects.create(
            user_eo=self.eo,
            name='Test Marathon',
            description='Test Description',
            event_date=timezone.now() + timedelta(days=30),
            regist_deadline=timezone.now() + timedelta(days=20),
            location='jakarta_selatan',
            capacity=100,
            contact='08123456789'
        )
    
    def test_review_creation(self):
        """Test review model creation"""
        review = Review.objects.create(
            runner=self.runner,
            event=self.event,
            event_organizer=self.eo,
            rating=5,
            review_text='Great event!'
        )
        
        self.assertIsNotNone(review.id)
        self.assertEqual(review.runner, self.runner)
        self.assertEqual(review.event, self.event)
        self.assertEqual(review.event_organizer, self.eo)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.review_text, 'Great event!')
        self.assertIsNotNone(review.created_at)
    
    def test_review_str_method(self):
        """Test review __str__ method"""
        review = Review.objects.create(
            runner=self.runner,
            event=self.event,
            event_organizer=self.eo,
            rating=5,
            review_text='Great event!'
        )
        
        expected = f"Review by {self.runner.user.username} for {self.event.name}"
        self.assertEqual(str(review), expected)