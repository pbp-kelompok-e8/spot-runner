from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponse
from django.db.models import Avg, Count
from .models import EventOrganizer
from apps.event.models import Event
# from apps.review.models import Review

# Create your views here.
@login_required
def index(request):
    # Check if user has event_organizer role
    if request.user.role != 'event_organizer':
        messages.error(request, "Access denied. You need an Event Organizer account to view this page.")
        return redirect('main:show_main')
    
    # Get or create event organizer profile
    organizer, created = EventOrganizer.objects.get_or_create(
        user=request.user,
        defaults={
            'base_location': ''  # Default empty location
        }
    )
    
    if created:
        messages.info(request, "Welcome! Your Event Organizer profile has been created.")
    
    # Get events for this organizer
    events = Event.objects.filter(user_eo=organizer).order_by('-event_date')
    
    # Calculate statistics
    total_events = events.count()
    reviews = Review.objects.filter(event_organizer=organizer)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    total_reviews = reviews.count()
    
    context = {
        'organizer': organizer,
        'events': events,
        'total_events': total_events,
        'avg_rating': avg_rating,
        'total_reviews': total_reviews,
    }
    return render(request, 'event_organizer/dashboard.html', context)

@login_required
def profile_view(request):
    try:
        organizer = request.user.event_organizer_profile
    except EventOrganizer.DoesNotExist:
        # Handle case where user is not an event organizer
        messages.error(request, "You don't have an event organizer profile")
        return redirect('home')  # or wherever you want to redirect
    
    context = {
        'organizer': organizer,
        'user': request.user,
    }
    return render(request, 'event_organizer/profile.html', context)

@login_required
def edit_profile(request):
    try:
        organizer = request.user.event_organizer_profile
    except EventOrganizer.DoesNotExist:
        messages.error(request, "You don't have an event organizer profile")
        return redirect('home')

    if request.method == 'POST':
        # Handle profile picture update
        if request.FILES.get('profile_picture'):
            organizer.profile_picture = request.FILES['profile_picture']
        
        # Update base location
        organizer.base_location = request.POST.get('base_location', '')
        
        # Update username if changed
        new_username = request.POST.get('username')
        if new_username and new_username != request.user.username:
            request.user.username = new_username
            request.user.save()
        
        organizer.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('event_organizer:profile')

    context = {
        'organizer': organizer,
        'user': request.user,
    }
    return render(request, 'event_organizer/edit_profile.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('event_organizer:profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'event_organizer/change_password.html', {'form': form})
