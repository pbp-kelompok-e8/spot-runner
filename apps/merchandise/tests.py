from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.merchandise.models import Merchandise, Redemption
from apps.event_organizer.models import EventOrganizer
from apps.main.models import Runner
import json
# test
# Create your tests here.
User = get_user_model()

class MerchandiseModelTest(TestCase):
    def setUp(self):
        """Setup test data"""
        # Create test users
        self.organizer_user = User.objects.create_user(
            username='organizer1',
            email='organizer@test.com',
            password='testpass123',
            role='event_organizer'
        )
        
        self.runner_user = User.objects.create_user(
            username='runner1',
            email='runner@test.com',
            password='testpass123',
            role='runner'
        )
        
        # Create profiles
        self.organizer = EventOrganizer.objects.create(
            user=self.organizer_user,
            base_location='Jakarta',
            coin=100
        )
        
        self.runner = Runner.objects.create(
            user=self.runner_user,
            base_location='Jakarta',
            coin=500
        )
        
        # Create test merchandise
        self.merchandise = Merchandise.objects.create(
            name='Test Tote Bag',
            description='A test tote bag',
            price_coins=100,
            organizer=self.organizer,
            image_url='https://example.com/image.jpg',
            category='totebag',
            stock=10
        )
    
    def test_merchandise_creation(self):
        """Test merchandise object creation"""
        self.assertEqual(self.merchandise.name, 'Test Tote Bag')
        self.assertEqual(self.merchandise.price_coins, 100)
        self.assertEqual(self.merchandise.stock, 10)
        self.assertEqual(self.merchandise.category, 'totebag')
        self.assertTrue(self.merchandise.available)
    
    def test_merchandise_available_property(self):
        """Test available property with stock > 0"""
        self.assertTrue(self.merchandise.available)
        
        # Test with stock = 0
        self.merchandise.stock = 0
        self.merchandise.save()
        self.assertFalse(self.merchandise.available)
    
    def test_merchandise_str_method(self):
        """Test merchandise string representation"""
        expected = f"{self.merchandise.name} — {self.organizer}"
        self.assertEqual(str(self.merchandise), expected)
    
    def test_merchandise_default_category(self):
        """Test default category is 'apparel'"""
        merch = Merchandise.objects.create(
            name='Default Category Product',
            description='Test',
            price_coins=50,
            organizer=self.organizer,
            image_url='https://example.com/test.jpg',
            stock=5
        )
        self.assertEqual(merch.category, 'apparel')
    
    def test_redemption_creation(self):
        """Test redemption object creation with explicit values"""
        redemption = Redemption.objects.create(
            user=self.runner,
            merchandise=self.merchandise,
            quantity=2,
            price_per_item=100,
            total_coins=200
        )
        
        self.assertEqual(redemption.quantity, 2)
        self.assertEqual(redemption.price_per_item, 100)
        self.assertEqual(redemption.total_coins, 200)
        self.assertEqual(redemption.user, self.runner)
        self.assertEqual(redemption.merchandise, self.merchandise)
    
    def test_redemption_str_method(self):
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
    
    def test_redemption_with_deleted_product(self):
        """Test redemption string when product is deleted"""
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
        
        self.assertIsNone(redemption.merchandise)
        self.assertIn("[Deleted Product]", str(redemption))


class MerchandiseViewTest(TestCase):
    def setUp(self):
        """Setup test client and data"""
        self.client = Client()
        
        # Create users
        self.organizer_user = User.objects.create_user(
            username='organizer1',
            email='organizer@test.com',
            password='testpass123',
            role='event_organizer'
        )
        
        self.runner_user = User.objects.create_user(
            username='runner1',
            email='runner@test.com',
            password='testpass123',
            role='runner'
        )
        
        # Create profiles
        self.organizer = EventOrganizer.objects.create(
            user=self.organizer_user,
            base_location='Jakarta',
            coin=100
        )
        
        self.runner = Runner.objects.create(
            user=self.runner_user,
            base_location='Jakarta',
            coin=500
        )
        
        # Create test merchandise
        self.merchandise = Merchandise.objects.create(
            name='Test Product',
            description='Test description',
            price_coins=100,
            organizer=self.organizer,
            image_url='https://example.com/image.jpg',
            category='apparel',
            stock=10
        )
    
    def test_merchandise_main_url_exists(self):
        """Test merchandise main page URL exists"""
        response = self.client.get('/merchandise/')
        self.assertEqual(response.status_code, 200)
    
    def test_merchandise_main_uses_correct_template(self):
        """Test merchandise main page uses correct template"""
        response = self.client.get(reverse('merchandise:show_merchandise'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'merchandise_main.html')
    
    def test_product_detail_url_exists(self):
        """Test product detail page URL exists"""
        response = self.client.get(f'/merchandise/{self.merchandise.id}/')
        self.assertEqual(response.status_code, 200)
    
    def test_product_detail_uses_correct_template(self):
        """Test product detail page uses correct template"""
        response = self.client.get(
            reverse('merchandise:product_detail', args=[self.merchandise.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'product_detail.html')
    
    def test_nonexistent_product_returns_404(self):
        """Test accessing non-existent product returns 404"""
        fake_uuid = '00000000-0000-0000-0000-000000000000'
        response = self.client.get(f'/merchandise/{fake_uuid}/')
        self.assertEqual(response.status_code, 404)
    
    def test_add_merchandise_requires_login(self):
        """Test add merchandise requires authentication"""
        response = self.client.get(reverse('merchandise:add_merchandise'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
    
    def test_add_merchandise_requires_organizer(self):
        """Test add merchandise requires organizer role"""
        # Login as runner
        self.client.login(username='runner1', password='testpass123')
        response = self.client.get(reverse('merchandise:add_merchandise'))
        # Should redirect (not authorized)
        self.assertEqual(response.status_code, 302)
    
    def test_add_merchandise_as_organizer(self):
        """Test organizer can access add merchandise page"""
        self.client.login(username='organizer1', password='testpass123')
        response = self.client.get(reverse('merchandise:add_merchandise'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_merchandise.html')
    
    def test_create_merchandise_post(self):
        """Test creating merchandise via POST"""
        self.client.login(username='organizer1', password='testpass123')
        
        data = {
            'name': 'New Product',
            'description': 'New description',
            'price_coins': 150,
            'image_url': 'https://example.com/new.jpg',
            'category': 'accessories',
            'stock': 20
        }
        
        response = self.client.post(
            reverse('merchandise:add_merchandise'),
            data=data
        )
        
        # Should redirect to merchandise main
        self.assertEqual(response.status_code, 302)
        
        # Check product was created
        self.assertTrue(
            Merchandise.objects.filter(name='New Product').exists()
        )
    
    def test_edit_merchandise_requires_ownership(self):
        """Test only owner can edit merchandise"""
        # Create another organizer
        other_org_user = User.objects.create_user(
            username='organizer2',
            email='org2@test.com',
            password='testpass123',
            role='event_organizer'
        )
        other_org = EventOrganizer.objects.create(
            user=other_org_user,
            base_location='Bandung',
            coin=50
        )
        
        # Login as other organizer
        self.client.login(username='organizer2', password='testpass123')
        response = self.client.get(
            reverse('merchandise:edit_merchandise', args=[self.merchandise.id])
        )
        
        # Should be redirected (not owner)
        self.assertEqual(response.status_code, 302)
    
    def test_delete_merchandise_ajax(self):
        """Test deleting merchandise via AJAX"""
        self.client.login(username='organizer1', password='testpass123')
        
        response = self.client.post(
            reverse('merchandise:delete_merchandise', args=[self.merchandise.id]),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Check product was deleted
        self.assertFalse(
            Merchandise.objects.filter(id=self.merchandise.id).exists()
        )
    
    def test_redeem_merchandise_requires_login(self):
        """Test redeem requires authentication"""
        response = self.client.post(
            reverse('merchandise:redeem_merchandise', args=[self.merchandise.id]),
            content_type='application/json',
            data=json.dumps({'quantity': 1})
        )
        self.assertEqual(response.status_code, 302)
    
    def test_redeem_merchandise_requires_runner(self):
        """Test only runners can redeem"""
        self.client.login(username='organizer1', password='testpass123')
        
        response = self.client.post(
            reverse('merchandise:redeem_merchandise', args=[self.merchandise.id]),
            content_type='application/json',
            data=json.dumps({'quantity': 1})
        )
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_redeem_merchandise_insufficient_coins(self):
        """Test redemption fails with insufficient coins"""
        # Set runner coins to less than price
        self.runner.coin = 50
        self.runner.save()
        
        self.client.login(username='runner1', password='testpass123')
        
        response = self.client.post(
            reverse('merchandise:redeem_merchandise', args=[self.merchandise.id]),
            content_type='application/json',
            data=json.dumps({'quantity': 1})
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Insufficient coins', data['error'])
    
    def test_redeem_merchandise_success(self):
        """Test successful merchandise redemption"""
        self.client.login(username='runner1', password='testpass123')
        
        initial_runner_coins = self.runner.coin
        initial_organizer_coins = self.organizer.coin
        initial_stock = self.merchandise.stock
        
        response = self.client.post(
            reverse('merchandise:redeem_merchandise', args=[self.merchandise.id]),
            content_type='application/json',
            data=json.dumps({'quantity': 2})
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['total_coins'], 200)
        
        # Check runner coins decreased
        self.runner.refresh_from_db()
        self.assertEqual(
            self.runner.coin,
            initial_runner_coins - 200
        )
        
        # Check organizer coins increased
        self.organizer.refresh_from_db()
        self.assertEqual(
            self.organizer.coin,
            initial_organizer_coins + 200
        )
        
        # Check stock decreased
        self.merchandise.refresh_from_db()
        self.assertEqual(
            self.merchandise.stock,
            initial_stock - 2
        )
        
        # Check redemption was created
        self.assertTrue(
            Redemption.objects.filter(
                user=self.runner,
                merchandise=self.merchandise
            ).exists()
        )
    
    def test_history_page_runner(self):
        """Test history page for runner"""
        self.client.login(username='runner1', password='testpass123')
        
        # Create a redemption
        Redemption.objects.create(
            user=self.runner,
            merchandise=self.merchandise,
            quantity=1,
            price_per_item=100,
            total_coins=100
        )
        
        response = self.client.get(reverse('merchandise:history'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'history.html')
        self.assertEqual(response.context['user_type'], 'runner')
        self.assertEqual(len(response.context['redemptions']), 1)
    
    def test_history_page_organizer(self):
        """Test history page for organizer"""
        self.client.login(username='organizer1', password='testpass123')
        
        # Create a redemption
        Redemption.objects.create(
            user=self.runner,
            merchandise=self.merchandise,
            quantity=1,
            price_per_item=100,
            total_coins=100
        )
        
        response = self.client.get(reverse('merchandise:history'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user_type'], 'organizer')
        self.assertEqual(len(response.context['redemptions']), 1)
    
    def test_category_filter(self):
        """Test filtering merchandise by category"""
        # Create merchandise with different categories
        Merchandise.objects.create(
            name='Accessory Product',
            description='Test',
            price_coins=50,
            organizer=self.organizer,
            image_url='https://example.com/acc.jpg',
            category='accessories',
            stock=5
        )
        
        response = self.client.get(
            reverse('merchandise:show_merchandise') + '?category=accessories'
        )
        
        self.assertEqual(response.status_code, 200)
        # Check that filtered products are in context
        products = response.context['products']
        for product in products:
            self.assertEqual(product.category, 'accessories')


class MerchandiseIntegrationTest(TestCase):
    def setUp(self):
        """Setup for integration tests"""
        self.client = Client()
        
        # Create complete user setup
        self.organizer_user = User.objects.create_user(
            username='org_test',
            email='org@test.com',
            password='pass123',
            role='event_organizer'
        )
        
        self.runner_user = User.objects.create_user(
            username='runner_test',
            email='runner@test.com',
            password='pass123',
            role='runner'
        )
        
        self.organizer = EventOrganizer.objects.create(
            user=self.organizer_user,
            base_location='Jakarta',
            coin=0
        )
        
        self.runner = Runner.objects.create(
            user=self.runner_user,
            base_location='Jakarta',
            coin=1000
        )
    
    def test_full_merchandise_lifecycle(self):
        """Test complete merchandise lifecycle: create, list, redeem, history"""
        # 1. Organizer creates merchandise
        self.client.login(username='org_test', password='pass123')
        
        create_response = self.client.post(
            reverse('merchandise:add_merchandise'),
            {
                'name': 'Lifecycle Product',
                'description': 'Test product',
                'price_coins': 100,
                'image_url': 'https://example.com/test.jpg',
                'category': 'apparel',
                'stock': 5
            }
        )
        self.assertEqual(create_response.status_code, 302)
        
        merchandise = Merchandise.objects.get(name='Lifecycle Product')
        
        # 2. Product appears in listing
        list_response = self.client.get(reverse('merchandise:show_merchandise'))
        self.assertContains(list_response, 'Lifecycle Product')
        
        self.client.logout()
        
        # 3. Runner redeems product
        self.client.login(username='runner_test', password='pass123')
        
        redeem_response = self.client.post(
            reverse('merchandise:redeem_merchandise', args=[merchandise.id]),
            content_type='application/json',
            data=json.dumps({'quantity': 2})
        )
        
        self.assertEqual(redeem_response.status_code, 200)
        redeem_data = json.loads(redeem_response.content)
        self.assertTrue(redeem_data['success'])
        
        # 4. Check runner history
        runner_history = self.client.get(reverse('merchandise:history'))
        self.assertEqual(runner_history.status_code, 200)
        self.assertEqual(len(runner_history.context['redemptions']), 1)
        
        self.client.logout()
        
        # 5. Check organizer history
        self.client.login(username='org_test', password='pass123')
        org_history = self.client.get(reverse('merchandise:history'))
        self.assertEqual(org_history.status_code, 200)
        self.assertEqual(len(org_history.context['redemptions']), 1)
        
        # 6. Verify coin transactions
        self.runner.refresh_from_db()
        self.organizer.refresh_from_db()
        self.assertEqual(self.runner.coin, 800)  # 1000 - (100*2)
        self.assertEqual(self.organizer.coin, 200)  # 0 + (100*2)