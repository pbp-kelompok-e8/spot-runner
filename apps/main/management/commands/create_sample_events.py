from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.event.models import Event, EventCategory
from apps.event_organizer.models import EventOrganizer
from datetime import datetime, timedelta
from django.utils import timezone
import uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample events for testing'

    def handle(self, *args, **options):
        # Create sample categories if they don't exist
        categories_data = [
            ('fun_run', 'Fun Run'),
            ('5k', '5K'),
            ('10k', '10K'),
            ('half_marathon', 'Half Marathon'),
            ('full_marathon', 'Full Marathon'),
        ]
        
        for cat_key, cat_display in categories_data:
            category, created = EventCategory.objects.get_or_create(
                category=cat_key,
                defaults={'category': cat_key}
            )
            if created:
                self.stdout.write(f'Created category: {cat_display}')

        # Create a sample event organizer if it doesn't exist
        organizer_user, created = User.objects.get_or_create(
            username='organizer1',
            defaults={
                'email': 'organizer1@example.com',
                'role': 'event_organizer',
                'first_name': 'John',
                'last_name': 'Organizer'
            }
        )
        
        if created:
            organizer_user.set_password('password123')
            organizer_user.save()
            self.stdout.write('Created organizer user')

        organizer, created = EventOrganizer.objects.get_or_create(
            user=organizer_user,
            defaults={
                'base_location': 'Jakarta Selatan',
                'profile_picture': 'https://via.placeholder.com/150'
            }
        )
        
        if created:
            self.stdout.write('Created event organizer profile')

        # Create sample events
        events_data = [
            {
                'name': 'Jakarta Marathon 2024',
                'description': 'Join thousands of runners in the heart of Jakarta for an unforgettable marathon experience through the city\'s most iconic landmarks.',
                'location': 'jakarta_pusat',
                'event_date': timezone.now() + timedelta(days=30),
                'regist_deadline': timezone.now() + timedelta(days=25),
                'capacity': 1000,
                'distance': 42195,  # 42.195 km in meters
                'contact': '+62-812-3456-7890',
                'coin': 50,
                'categories': ['full_marathon', 'half_marathon'],
                'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=300&fit=crop'
            },
            {
                'name': 'Sunset Fun Run',
                'description': 'A relaxing 5K run along the beach with beautiful sunset views. Perfect for beginners and families.',
                'location': 'jakarta_utara',
                'event_date': timezone.now() + timedelta(days=15),
                'regist_deadline': timezone.now() + timedelta(days=10),
                'capacity': 500,
                'distance': 5000,  # 5 km in meters
                'contact': '+62-813-4567-8901',
                'coin': 25,
                'categories': ['fun_run', '5k'],
                'image': 'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=400&h=300&fit=crop'
            },
            {
                'name': 'City Center 10K Challenge',
                'description': 'Test your speed in this fast-paced 10K race through the business district.',
                'location': 'jakarta_selatan',
                'event_date': timezone.now() + timedelta(days=45),
                'regist_deadline': timezone.now() + timedelta(days=40),
                'capacity': 300,
                'distance': 10000,  # 10 km in meters
                'contact': '+62-814-5678-9012',
                'coin': 30,
                'categories': ['10k'],
                'image': 'https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400&h=300&fit=crop'
            },
            {
                'name': 'Trail Running Adventure',
                'description': 'Experience nature like never before in this challenging trail run through scenic mountain paths.',
                'location': 'bogor',
                'event_date': timezone.now() + timedelta(days=60),
                'regist_deadline': timezone.now() + timedelta(days=55),
                'capacity': 200,
                'distance': 21097,  # 21.097 km in meters
                'contact': '+62-815-6789-0123',
                'coin': 40,
                'categories': ['half_marathon'],
                'image': None  # No image to test placeholder
            }
        ]

        for event_data in events_data:
            event, created = Event.objects.get_or_create(
                name=event_data['name'],
                defaults={
                    'id': uuid.uuid4(),
                    'description': event_data['description'],
                    'location': event_data['location'],
                    'event_date': event_data['event_date'],
                    'regist_deadline': event_data['regist_deadline'],
                    'capacity': event_data['capacity'],
                    'distance': event_data['distance'],
                    'contact': event_data['contact'],
                    'coin': event_data['coin'],
                    'image': event_data['image'],
                    'user_eo': organizer,
                    'event_status': 'coming_soon'
                }
            )
            
            if created:
                # Add categories
                for cat_key in event_data['categories']:
                    try:
                        category = EventCategory.objects.get(category=cat_key)
                        event.event_category.add(category)
                    except EventCategory.DoesNotExist:
                        pass
                
                self.stdout.write(f'Created event: {event.name}')
            else:
                self.stdout.write(f'Event already exists: {event.name}')

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample events!')
        )
