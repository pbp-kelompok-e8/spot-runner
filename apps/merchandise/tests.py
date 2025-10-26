from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.merchandise.models import Merchandise, Redemption
from apps.event_organizer.models import EventOrganizer
from apps.main.models import Runner
import json

User = get_user_model()
class MerchandiseModelTest(TestCase):
    """Test Merchandise model"""
    
    def setUp(self):
        # Create Event Organizer
        self.eo_user = User.objects.create_user(
            username='testorganizer',
            email='organizer@test.com',
            password='testpass123',
            role='event_organizer'
        )
        self.organizer = EventOrganizer.objects.create(
            user=self.eo_user,
            base_location='jakarta',
            coin=0
        )
        
        # Create Merchandise
        self.merchandise = Merchandise.objects.create(
            name='Test T-Shirt',
            description='A cool test t-shirt',
            category='apparel',
            price_coins=100,
            stock=50,
            organizer=self.organizer,
            image_url='https://example.com/test.jpg'
        )
    
    def test_merchandise_creation(self):
        """Test merchandise is created correctly"""
        self.assertEqual(self.merchandise.name, 'Test T-Shirt')
        self.assertEqual(self.merchandise.price_coins, 100)
        self.assertEqual(self.merchandise.stock, 50)
        self.assertTrue(self.merchandise.available)
    
    def test_merchandise_str(self):
        """Test merchandise string representation"""
        expected = f"{self.merchandise.name} — {self.organizer}"
        self.assertEqual(str(self.merchandise), expected)
    
    def test_merchandise_available_property(self):
        """Test available property"""
        self.assertTrue(self.merchandise.available)
        
        # Set stock to 0
        self.merchandise.stock = 0
        self.merchandise.save()
        self.assertFalse(self.merchandise.available)


class RedemptionModelTest(TestCase):
    """Test Redemption model"""
    
    def setUp(self):
        # Create Event Organizer
        self.eo_user = User.objects.create_user(
            username='testorganizer',
            email='organizer@test.com',
            password='testpass123',
            role='event_organizer'
        )
        self.organizer = EventOrganizer.objects.create(
            user=self.eo_user,
            base_location='jakarta',
            coin=0
        )
        
        # Create Runner
        self.runner_user = User.objects.create_user(
            username='testrunner',
            email='runner@test.com',
            password='testpass123',
            role='runner'
        )
        self.runner = Runner.objects.create(
            user=self.runner_user,
            base_location='jakarta',
            coin=500
        )
        
        # Create Merchandise
        self.merchandise = Merchandise.objects.create(
            name='Test T-Shirt',
            description='A cool test t-shirt',
            category='apparel',
            price_coins=100,
            stock=50,
            organizer=self.organizer,
            image_url='https://example.com/test.jpg'
        )
    
    def test_redemption_creation(self):
        """Test redemption is created correctly"""
        redemption = Redemption.objects.create(
            user=self.runner,
            merchandise=self.merchandise,
            quantity=2,
            price_per_item=100,
            total_coins=200
        )
        
        self.assertEqual(redemption.quantity, 2)
        self.assertEqual(redemption.total_coins, 200)
        self.assertEqual(redemption.user, self.runner)
    
    def test_redemption_str(self):
        """Test redemption string representation"""
        redemption = Redemption.objects.create(
            user=self.runner,
            merchandise=self.merchandise,
            quantity=2,
            price_per_item=100,
            total_coins=200
        )
        
        expected = f"{self.runner.user.username} - {self.merchandise.name} x2"
        self.assertEqual(str(redemption), expected)
    
    def test_redemption_with_deleted_merchandise(self):
        """Test redemption when merchandise is deleted"""
        redemption = Redemption.objects.create(
            user=self.runner,
            merchandise=self.merchandise,
            quantity=1,
            price_per_item=100,
            total_coins=100
        )
        
        # Delete merchandise
        self.merchandise.delete()
        redemption.refresh_from_db()
        
        # Should still exist with null merchandise
        self.assertIsNone(redemption.merchandise)
        self.assertEqual(str(redemption), f"{self.runner.user.username} - [Deleted Product] x1")


class ShowMerchandiseViewTest(TestCase):
    """Test show_merchandise view"""
    
    def setUp(self):
        self.client = Client()
        
        # Create Event Organizer
        self.eo_user = User.objects.create_user(
            username='testorganizer',
            email='organizer@test.com',
            password='testpass123',
            role='event_organizer'
        )
        self.organizer = EventOrganizer.objects.create(
            user=self.eo_user,
            base_location='jakarta',
            coin=0
        )
        
        # Create Runner
        self.runner_user = User.objects.create_user(
            username='testrunner',
            email='runner@test.com',
            password='testpass123',
            role='runner'
        )
        self.runner = Runner.objects.create(
            user=self.runner_user,
            base_location='jakarta',
            coin=500
        )
        
        # Create Merchandise
        self.merchandise = Merchandise.objects.create(
            name='Test T-Shirt',
            description='A cool test t-shirt',
            category='apparel',
            price_coins=100,
            stock=50,
            organizer=self.organizer,
            image_url='https://example.com/test.jpg'
        )
    
    def test_show_merchandise_anonymous(self):
        """Test merchandise page for anonymous users"""
        response = self.client.get(reverse('merchandise:show_merchandise'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'merchandise_main.html')
        self.assertContains(response, 'Test T-Shirt')
        self.assertEqual(response.context['user_coins'], 0)
        self.assertEqual(response.context['organizer_coins'], 0)
        self.assertFalse(response.context['is_organizer'])
    
    def test_show_merchandise_runner(self):
        """Test merchandise page for runner"""
        self.client.login(username='testrunner', password='testpass123')
        response = self.client.get(reverse('merchandise:show_merchandise'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user_coins'], 500)
        self.assertFalse(response.context['is_organizer'])
    
    def test_show_merchandise_organizer(self):
        """Test merchandise page for organizer"""
        self.client.login(username='testorganizer', password='testpass123')
        response = self.client.get(reverse('merchandise:show_merchandise'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_organizer'])
        self.assertEqual(response.context['organizer_coins'], 0)
    
    def test_category_filter(self):
        """Test category filtering"""
        # Create another merchandise with different category
        Merchandise.objects.create(
            name='Water Bottle',
            description='A water bottle',
            category='water_bottle',
            price_coins=50,
            stock=30,
            organizer=self.organizer,
            image_url='https://example.com/bottle.jpg'
        )
        
        response = self.client.get(reverse('merchandise:show_merchandise') + '?category=apparel')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['products'].count(), 1)
        self.assertEqual(response.context['products'].first().name, 'Test T-Shirt')


class ProductDetailViewTest(TestCase):
    """Test product_detail view"""
    
    def setUp(self):
        self.client = Client()
        
        # Create Event Organizer
        self.eo_user = User.objects.create_user(
            username='testorganizer',
            email='organizer@test.com',
            password='testpass123',
            role='event_organizer'
        )
        self.organizer = EventOrganizer.objects.create(
            user=self.eo_user,
            base_location='jakarta',
            coin=0
        )
        
        # Create Runner
        self.runner_user = User.objects.create_user(
            username='testrunner',
            email='runner@test.com',
            password='testpass123',
            role='runner'
        )
        self.runner = Runner.objects.create(
            user=self.runner_user,
            base_location='jakarta',
            coin=500
        )
        
        # Create Merchandise
        self.merchandise = Merchandise.objects.create(
            name='Test T-Shirt',
            description='A cool test t-shirt',
            category='apparel',
            price_coins=100,
            stock=50,
            organizer=self.organizer,
            image_url='https://example.com/test.jpg'
        )
    
    def test_product_detail_anonymous(self):
        """Test product detail for anonymous users"""
        response = self.client.get(
            reverse('merchandise:product_detail', args=[self.merchandise.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'product_detail.html')
        self.assertContains(response, 'Test T-Shirt')
        self.assertFalse(response.context['is_organizer'])
    
    def test_product_detail_runner(self):
        """Test product detail for runner"""
        self.client.login(username='testrunner', password='testpass123')
        response = self.client.get(
            reverse('merchandise:product_detail', args=[self.merchandise.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user_coins'], 500)
        self.assertFalse(response.context['is_organizer'])
    
    def test_product_detail_owner(self):
        """Test product detail for owner/organizer"""
        self.client.login(username='testorganizer', password='testpass123')
        response = self.client.get(
            reverse('merchandise:product_detail', args=[self.merchandise.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_organizer'])
    
    def test_product_detail_404(self):
        """Test product detail with invalid ID"""
        import uuid
        fake_id = uuid.uuid4()
        response = self.client.get(
            reverse('merchandise:product_detail', args=[fake_id])
        )
        
        self.assertEqual(response.status_code, 404)


class AddMerchandiseViewTest(TestCase):
    """Test add_merchandise view"""
    
    def setUp(self):
        self.client = Client()
        
        # Create Event Organizer
        self.eo_user = User.objects.create_user(
            username='testorganizer',
            email='organizer@test.com',
            password='testpass123',
            role='event_organizer'
        )
        self.organizer = EventOrganizer.objects.create(
            user=self.eo_user,
            base_location='jakarta',
            coin=0
        )
        
        # Create Runner
        self.runner_user = User.objects.create_user(
            username='testrunner',
            email='runner@test.com',
            password='testpass123',
            role='runner'
        )
        Runner.objects.create(
            user=self.runner_user,
            base_location='jakarta',
            coin=500
        )
    
    def test_add_merchandise_anonymous(self):
        """Test add merchandise redirects for anonymous users"""
        response = self.client.get(reverse('merchandise:add_merchandise'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
    
    def test_add_merchandise_runner_denied(self):
        """Test runners cannot add merchandise"""
        self.client.login(username='testrunner', password='testpass123')
        response = self.client.get(reverse('merchandise:add_merchandise'))
        
        self.assertEqual(response.status_code, 302)
    
    def test_add_merchandise_get_organizer(self):
        """Test GET add merchandise for organizer"""
        self.client.login(username='testorganizer', password='testpass123')
        response = self.client.get(reverse('merchandise:add_merchandise'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_merchandise.html')
    
    def test_add_merchandise_post_valid(self):
        """Test POST add merchandise with valid data"""
        self.client.login(username='testorganizer', password='testpass123')
        
        data = {
            'name': 'New T-Shirt',
            'description': 'Brand new shirt',
            'category': 'apparel',
            'price_coins': 150,
            'stock': 20,
            'image_url': 'https://example.com/new.jpg'
        }
        
        response = self.client.post(reverse('merchandise:add_merchandise'), data)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Merchandise.objects.count(), 1)
        
        merch = Merchandise.objects.first()
        self.assertEqual(merch.name, 'New T-Shirt')
        self.assertEqual(merch.organizer, self.organizer)
    
    def test_add_merchandise_post_invalid(self):
        """Test POST add merchandise with invalid data"""
        self.client.login(username='testorganizer', password='testpass123')
        
        data = {
            'name': '',  # Invalid: empty name
            'description': 'Brand new shirt',
            'category': 'apparel',
            'price_coins': 150,
            'stock': 20,
            'image_url': 'https://example.com/new.jpg'
        }
        
        response = self.client.post(reverse('merchandise:add_merchandise'), data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Merchandise.objects.count(), 0)


class EditMerchandiseViewTest(TestCase):
    """Test edit_merchandise view"""
    
    def setUp(self):
        self.client = Client()
        
        # Create Event Organizer
        self.eo_user = User.objects.create_user(
            username='testorganizer',
            email='organizer@test.com',
            password='testpass123',
            role='event_organizer'
        )
        self.organizer = EventOrganizer.objects.create(
            user=self.eo_user,
            base_location='jakarta',
            coin=0
        )
        
        # Create Another Organizer
        self.other_eo_user = User.objects.create_user(
            username='otherorganizer',
            email='other@test.com',
            password='testpass123',
            role='event_organizer'
        )
        self.other_organizer = EventOrganizer.objects.create(
            user=self.other_eo_user,
            base_location='jakarta',
            coin=0
        )
        
        # Create Merchandise
        self.merchandise = Merchandise.objects.create(
            name='Test T-Shirt',
            description='A cool test t-shirt',
            category='apparel',
            price_coins=100,
            stock=50,
            organizer=self.organizer,
            image_url='https://example.com/test.jpg'
        )
    
    def test_edit_merchandise_owner(self):
        """Test owner can edit merchandise"""
        self.client.login(username='testorganizer', password='testpass123')
        response = self.client.get(
            reverse('merchandise:edit_merchandise', args=[self.merchandise.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_merchandise.html')
    
    def test_edit_merchandise_not_owner(self):
        """Test non-owner cannot edit merchandise"""
        self.client.login(username='otherorganizer', password='testpass123')
        response = self.client.get(
            reverse('merchandise:edit_merchandise', args=[self.merchandise.id])
        )
        
        self.assertEqual(response.status_code, 302)
    
    def test_edit_merchandise_post_valid(self):
        """Test POST edit merchandise with valid data"""
        self.client.login(username='testorganizer', password='testpass123')
        
        data = {
            'name': 'Updated T-Shirt',
            'description': 'Updated description',
            'category': 'apparel',
            'price_coins': 200,
            'stock': 30,
            'image_url': 'https://example.com/updated.jpg'
        }
        
        response = self.client.post(
            reverse('merchandise:edit_merchandise', args=[self.merchandise.id]),
            data
        )
        
        self.assertEqual(response.status_code, 302)
        
        self.merchandise.refresh_from_db()
        self.assertEqual(self.merchandise.name, 'Updated T-Shirt')
        self.assertEqual(self.merchandise.price_coins, 200)


class DeleteMerchandiseViewTest(TestCase):
    """Test delete_merchandise view"""
    
    def setUp(self):
        self.client = Client()
        
        # Create Event Organizer
        self.eo_user = User.objects.create_user(
            username='testorganizer',
            email='organizer@test.com',
            password='testpass123',
            role='event_organizer'
        )
        self.organizer = EventOrganizer.objects.create(
            user=self.eo_user,
            base_location='jakarta',
            coin=0
        )
        
        # Create Merchandise
        self.merchandise = Merchandise.objects.create(
            name='Test T-Shirt',
            description='A cool test t-shirt',
            category='apparel',
            price_coins=100,
            stock=50,
            organizer=self.organizer,
            image_url='https://example.com/test.jpg'
        )
    
    def test_delete_merchandise_owner(self):
        """Test owner can delete merchandise"""
        self.client.login(username='testorganizer', password='testpass123')
        response = self.client.post(
            reverse('merchandise:delete_merchandise', args=[self.merchandise.id])
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(Merchandise.objects.count(), 0)
    
    def test_delete_merchandise_get_not_allowed(self):
        """Test GET method not allowed for delete"""
        self.client.login(username='testorganizer', password='testpass123')
        response = self.client.get(
            reverse('merchandise:delete_merchandise', args=[self.merchandise.id])
        )
        
        # Should return 405 Method Not Allowed
        self.assertEqual(response.status_code, 405)


class RedeemMerchandiseViewTest(TestCase):
    """Test redeem_merchandise view"""
    
    def setUp(self):
        self.client = Client()
        
        # Create Event Organizer
        self.eo_user = User.objects.create_user(
            username='testorganizer',
            email='organizer@test.com',
            password='testpass123',
            role='event_organizer'
        )
        self.organizer = EventOrganizer.objects.create(
            user=self.eo_user,
            base_location='jakarta',
            coin=0
        )
        
        # Create Runner
        self.runner_user = User.objects.create_user(
            username='testrunner',
            email='runner@test.com',
            password='testpass123',
            role='runner'
        )
        self.runner = Runner.objects.create(
            user=self.runner_user,
            base_location='jakarta',
            coin=500
        )
        
        # Create Merchandise
        self.merchandise = Merchandise.objects.create(
            name='Test T-Shirt',
            description='A cool test t-shirt',
            category='apparel',
            price_coins=100,
            stock=50,
            organizer=self.organizer,
            image_url='https://example.com/test.jpg'
        )
    
    def test_redeem_merchandise_success(self):
        """Test successful redemption"""
        self.client.login(username='testrunner', password='testpass123')
        
        data = {'quantity': 2}
        response = self.client.post(
            reverse('merchandise:redeem_merchandise', args=[self.merchandise.id]),
            json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertEqual(result['total_coins'], 200)
        
        # Check runner coins decreased
        self.runner.refresh_from_db()
        self.assertEqual(self.runner.coin, 300)
        
        # Check organizer coins increased
        self.organizer.refresh_from_db()
        self.assertEqual(self.organizer.coin, 200)
        
        # Check stock decreased
        self.merchandise.refresh_from_db()
        self.assertEqual(self.merchandise.stock, 48)
        
        # Check redemption created
        self.assertEqual(Redemption.objects.count(), 1)
    
    def test_redeem_insufficient_coins(self):
        """Test redemption with insufficient coins"""
        self.runner.coin = 50
        self.runner.save()
        
        self.client.login(username='testrunner', password='testpass123')
        
        data = {'quantity': 2}
        response = self.client.post(
            reverse('merchandise:redeem_merchandise', args=[self.merchandise.id]),
            json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertIn('Insufficient coins', result['error'])
    
    def test_redeem_insufficient_stock(self):
        """Test redemption with insufficient stock"""
        self.client.login(username='testrunner', password='testpass123')
        
        data = {'quantity': 100}  # More than stock
        response = self.client.post(
            reverse('merchandise:redeem_merchandise', args=[self.merchandise.id]),
            json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertIn('in stock', result['error'])
    
    def test_redeem_organizer_cannot_redeem(self):
        """Test organizers cannot redeem merchandise"""
        self.client.login(username='testorganizer', password='testpass123')
        
        data = {'quantity': 1}
        response = self.client.post(
            reverse('merchandise:redeem_merchandise', args=[self.merchandise.id]),
            json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)


class HistoryViewTest(TestCase):
    """Test history view"""
    
    def setUp(self):
        self.client = Client()
        
        # Create Event Organizer
        self.eo_user = User.objects.create_user(
            username='testorganizer',
            email='organizer@test.com',
            password='testpass123',
            role='event_organizer'
        )
        self.organizer = EventOrganizer.objects.create(
            user=self.eo_user,
            base_location='jakarta',
            coin=0
        )
        
        # Create Runner
        self.runner_user = User.objects.create_user(
            username='testrunner',
            email='runner@test.com',
            password='testpass123',
            role='runner'
        )
        self.runner = Runner.objects.create(
            user=self.runner_user,
            base_location='jakarta',
            coin=500
        )
        
        # Create Merchandise
        self.merchandise = Merchandise.objects.create(
            name='Test T-Shirt',
            description='A cool test t-shirt',
            category='apparel',
            price_coins=100,
            stock=50,
            organizer=self.organizer,
            image_url='https://example.com/test.jpg'
        )
        
        # Create Redemption
        self.redemption = Redemption.objects.create(
            user=self.runner,
            merchandise=self.merchandise,
            quantity=2,
            price_per_item=100,
            total_coins=200
        )
    
    def test_history_runner(self):
        """Test history for runner"""
        self.client.login(username='testrunner', password='testpass123')
        response = self.client.get(reverse('merchandise:history'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'history.html')
        self.assertEqual(response.context['user_type'], 'runner')
        self.assertEqual(response.context['redemptions'].count(), 1)
    
    def test_history_organizer(self):
        """Test history for organizer"""
        self.client.login(username='testorganizer', password='testpass123')
        response = self.client.get(reverse('merchandise:history'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user_type'], 'organizer')
        self.assertEqual(response.context['redemptions'].count(), 1)
    
    def test_history_anonymous(self):
        """Test history redirects for anonymous users"""
        response = self.client.get(reverse('merchandise:history'))
        
        self.assertEqual(response.status_code, 302)