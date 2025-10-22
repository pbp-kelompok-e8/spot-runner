from django.db import models
import uuid

# Create your models here.git

class EventCategory(models.Model):
    category = [
        ('fun_run', 'Fun Run'),
        ('5k', '5K'),
        ('10k', '10K'),
        ('half_marathon', 'Half Marathon'),
        ('full_marathon', 'Full Marathon')
    ]
    category = models.CharField(max_length=20, choices=category,unique=True)

    def __str__(self):
        return self.get_category_display()

class Event(models.Model):
    user_eo = models.ForeignKey('event_organizer.EventOrganizer', on_delete=models.CASCADE)

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
    name = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=20, choices=cities)
    event_category = models.ManyToManyField(EventCategory, related_name= 'events')
    image = models.URLField(blank=True, null=True)
    image2 = models.URLField(blank=True, null=True)
    image3 = models.URLField(blank=True, null=True)
    event_date = models.DateTimeField()
    regist_deadline = models.DateTimeField()
    distance = models.PositiveIntegerField(default=0)
    contact = models.CharField(max_length=20)
    capacity = models.PositiveIntegerField(default=0)
    total_participans = models.PositiveIntegerField(default=0)
    full = models.BooleanField(default=False)
    event_status = models.CharField(max_length=20, choices=status, default='coming_soon')
    coin = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name
    
    def increment_participans(self):
        if self.total_participans >= self.capacity:
            self.total_participans += 0
            self.full = True
        else:
            self.total_participans += 1
        self.save()