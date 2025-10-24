from django.db import models
import uuid

class EventCategory(models.Model):
    CATEGORY_CHOICES = [
        ('fun_run', 'Fun Run'),
        ('5k', '5K'),
        ('10k', '10K'),
        ('half_marathon', 'Half Marathon'),
        ('full_marathon', 'Full Marathon')
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES,unique=True)
    
    def __str__(self):
        return self.get_category_display()

class Event(models.Model):
    user_eo = models.ForeignKey('event_organizer.EventOrganizer', on_delete=models.CASCADE, null=True)
    cities = [
        ('jakarta_barat', 'Jakarta Barat'),
        ('jakarta_pusat', 'Jakarta Pusat'),
        ('jakarta_selatan', 'Jakarta Selatan'),
        ('jakarta_timur', 'Jakarta Timur'),
        ('jakarta_utara', 'Jakarta Utara'),
        ('bekasi', 'Bekasi'),
        ('bogor', 'Bogor'),
        ('depok', 'Depok'),
        ('tangerang', 'Tangerang')
    ]

    status = [
        ('coming_soon', 'Coming Soon'),
        ('on_going', 'On Going'),
        ('finished', 'Finished'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, default="Untitled Event")
    description = models.TextField(default="No description available", blank=True)
    location = models.CharField(max_length=20, choices=cities, default="jakarta_barat")
    image = models.URLField(blank=True, null=True)
    image2 = models.URLField(blank=True, null=True)
    image3 = models.URLField(blank=True, null=True)
    event_date = models.DateTimeField(null=True, blank=True) 
    regist_deadline = models.DateTimeField(null=True, blank=True) 
    contact = models.CharField(max_length=20, null=True)  
    capacity = models.PositiveIntegerField(default=0)
    total_participans = models.PositiveIntegerField(default=0)
    full = models.BooleanField(default=False)
    event_status = models.CharField(max_length=20, choices=status, default='coming_soon')
    event_category = models.ManyToManyField(EventCategory, related_name= 'events')
    coin = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name
    
    def increment_participans(self):
        if self.total_participans == self.capacity:
            self.full = True
        else:
            self.total_participans += 1
            if self.total_participans == self.capacity:
                self.full = True
        self.save()
        
    def decrement_participans(self):
        if self.total_participans <= self.capacity:
            self.total_participans -= 1
            if self.full:
                self.full = False
        self.save()