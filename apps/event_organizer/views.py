from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Avg, Count
from apps.event.models import Event
from apps.main.models import User
from .models import EventOrganizer
from apps.review.models import Review


@login_required
def dashboard_view(request):
    if request.user.role != 'event_organizer':
        messages.error(request, "Access denied. Only Event Organizers can access this page.")
        return redirect('main:show_main')

    organizer, _ = EventOrganizer.objects.get_or_create(
        user=request.user,
        defaults={'base_location': ''}
    )

    events = Event.objects.filter(user_eo=organizer).order_by('-event_date')
    total_events = events.count()

    # Grouping Status
    ongoing_events = events.filter(event_status='ongoing')
    finished_events = events.filter(event_status='finished')
    cancelled_events = events.filter(event_status='cancelled')

    stats = Review.objects.filter(event__user_eo=organizer).aggregate(
        avg=Avg('rating'),
        count=Count('rating')
    )

    avg_rating = round(stats['avg'] or 0, 2)
    review_count = stats['count'] or 0

    context = {
        'organizer': organizer,
        'events': events,
        'ongoing_events': ongoing_events,
        'finished_events': finished_events,
        'cancelled_events': cancelled_events,
        'total_events': total_events,
        'avg_rating': avg_rating,     
        'review_count': review_count, 
    }
    return render(request, 'event_organizer/dashboard.html', context)


@login_required
def profile_view(request):
    """Profile page for Event Organizer"""
    if request.user.role != 'event_organizer':
        messages.error(request, "Access denied. Only Event Organizers can access this page.")
        return redirect('main:show_main')

    try:
        organizer = request.user.event_organizer_profile
    except EventOrganizer.DoesNotExist:
        messages.error(request, "You don't have an event organizer profile.")
        return redirect('main:show_main')

    context = {
        'organizer': organizer,
        'user': request.user,
        'joined_date': organizer.created_at.strftime('%d %b %Y') if organizer.created_at else '-',
        'last_login': request.user.last_login.strftime('%I:%M %p, %d %b %Y') if request.user.last_login else 'Never',
    }
    return render(request, 'event_organizer/profile.html', context)


@login_required
def edit_profile(request):
    """Edit Event Organizer Profile"""

    try:
        organizer = request.user.event_organizer_profile
    except EventOrganizer.DoesNotExist:
        messages.error(request, "You don't have an event organizer profile.")
        return redirect('event_organizer:profile')

    if request.method == 'POST':
        new_username = request.POST.get('username')
        base_location = request.POST.get('base_location', '')
        image_url = request.POST.get('profile_picture', '')  # ✅ name disamakan dengan form

        # Update username
        if new_username and new_username != request.user.username:
            request.user.username = new_username
            request.user.save()

        # Update EO fields
        organizer.base_location = base_location
        organizer.profile_picture = image_url  # ✅ langsung update
        organizer.save()

        messages.success(request, "Profile updated successfully!")
        return redirect('event_organizer:profile')

    context = {
        'organizer': organizer,
        'user': request.user,
    }
    return render(request, 'event_organizer/edit_profile.html', context)



@login_required
def change_password(request):
    """Change password page"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been updated successfully!')
            return redirect('event_organizer:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'event_organizer/change_password.html', {'form': form})
