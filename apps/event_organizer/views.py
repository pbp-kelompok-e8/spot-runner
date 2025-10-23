# apps/event_organizer/views.py (atau lokasi view profile EO)

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from apps.event_organizer.models import EventOrganizer
from apps.event.models import Event
from apps.review.models import Review

@login_required
def event_organizer_profile(request):
    # Get event organizer profile
    try:
        organizer = EventOrganizer.objects.get(user=request.user)
    except EventOrganizer.DoesNotExist:
        # Handle jika user bukan event organizer
        return render(request, 'error.html', {
            'message': 'You are not registered as an event organizer.'
        })
    
    # Get all events created by this organizer
    events = Event.objects.filter(user_eo=organizer).order_by('-date')
    
    # Get all reviews for this event organizer
    reviews = Review.objects.filter(event_organizer=organizer).select_related(
        'runner__user', 'event'
    ).order_by('-created_at')
    
    # Calculate average rating
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    if avg_rating:
        avg_rating = round(avg_rating, 1)
    
    context = {
        'organizer': organizer,
        'events': events,
        'reviews': reviews,
        'avg_rating': avg_rating,
    }
    
    return render(request, 'event_organizer/profile.html', context)