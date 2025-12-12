from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, logout
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Avg, Count, Prefetch
from apps.event.models import Event
from apps.main.models import User
from .models import EventOrganizer
from apps.review.models import Review
from datetime import date


@login_required
def dashboard_view(request):
    if request.user.role != 'event_organizer':
        messages.error(request, "Access denied. Only Event Organizers can access this page.")
        return redirect('main:show_main')

    organizer, _ = EventOrganizer.objects.get_or_create(
        user=request.user,
        defaults={'base_location': ''}
    )

    events = Event.objects.filter(user_eo=organizer)
    today = date.today()
    updated_events = []
    
    for event in events:
        if event.event_status not in ['finished', 'cancelled']:
            event_date = event.event_date.date()
            new_status = event.event_status
            if event_date < today:
                new_status = "finished"
            elif event_date == today:
                new_status = "on_going"
            elif event.regist_deadline.date() < today:
                pass
            if new_status != event.event_status:
                event.event_status = new_status
                event.save()
        updated_events.append(event)

    total_events = len(updated_events)
    ongoing_events = [e for e in updated_events if e.event_status == 'on_going'] 
    finished_events = [e for e in updated_events if e.event_status == 'finished']
    cancelled_events = [e for e in updated_events if e.event_status == 'cancelled']
    reviews = Review.objects.filter(
        event__user_eo=organizer
    ).select_related(
        'runner__user',
        'event'
    ).order_by('-created_at')

    stats = reviews.aggregate(
        avg=Avg('rating'),
        count=Count('rating')
    )

    avg_rating = round(stats['avg'] or 0, 2)
    review_count = stats['count'] or 0

    context = {
        'organizer': organizer,
        'events': updated_events,
        'ongoing_events': ongoing_events,
        'finished_events': finished_events,
        'cancelled_events': cancelled_events,
        'total_events': total_events,
        'reviews': reviews,
        'organizer_average_rating': avg_rating,
        'organizer_total_reviews': review_count,
    }
    return render(request, 'event_organizer/dashboard.html', context)

@login_required(login_url='main:login')
def show_profile(request, username=None):
    """Show Event Organizer profile with their events and reviews"""
    
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user
    
    if user.role != 'event_organizer':
        messages.error(request, "Access denied. Only Event Organizers can access this page.")
        return redirect('main:show_main')
    
    try:
        organizer = user.event_organizer_profile
    except AttributeError:
        messages.error(request, "You don't have an event organizer profile.")
        return redirect('main:show_main')
    
    # Ambil semua events dari organizer
    events = Event.objects.filter(
        user_eo=organizer
    ).prefetch_related(
        'event_category'
    ).order_by('-event_date')
    
    # Ambil semua reviews dari semua event organizer (sama seperti event detail)
    reviews = Review.objects.filter(
        event__user_eo=organizer
    ).select_related(
        'runner__user',
        'event'
    ).order_by('-created_at')
    
    # Hitung average rating dan total review count
    review_stats = reviews.aggregate(
        avg_rating=Avg('rating'),
        total_reviews=Count('id')
    )
    
    overall_avg_rating = round(review_stats['avg_rating'] or 0, 1)
    overall_review_count = review_stats['total_reviews'] or 0
    
    context = {
        'organizer': organizer,
        'user': user,
        'events': events,
        'reviews': reviews,  # Menggunakan 'reviews' seperti di event detail
        'overall_avg_rating': overall_avg_rating,
        'overall_review_count': overall_review_count,
        'joined_date': organizer.created_at.strftime('%d %b %Y') if organizer.created_at else '-',
        'last_login': user.last_login.strftime('%I:%M %p, %d %b %Y') if user.last_login else 'Never',
    }
    
    return render(request, 'event_organizer/profile.html', context)


@login_required
def edit_profile(request):
    try:
        organizer = request.user.event_organizer_profile
    except EventOrganizer.DoesNotExist:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "message": "Organizer profile not found."})
        messages.error(request, "You don't have an event organizer profile.")
        return redirect('event_organizer:profile')

    if request.method == 'POST':
        new_username = request.POST.get('username')
        base_location = request.POST.get('base_location', '')
        image_url = request.POST.get('profile_picture', '')

        # Update username
        if new_username and new_username != request.user.username:
            request.user.username = new_username
            request.user.save()

        # Update EO fields
        organizer.base_location = base_location
        organizer.profile_picture = image_url
        organizer.save()

        # ✅ RETURN JSON kalau AJAX
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        # jika bukan AJAX → redirect biasa
        messages.success(request, "Profile updated successfully!")
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

        # Kalau request dari AJAX, balikan JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                return JsonResponse({'success': True, 'message': 'Password updated successfully!'})
            else:
                # Ambil error pertama yang muncul
                error_message = list(form.errors.values())[0][0]
                return JsonResponse({'success': False, 'message': error_message})

        # Kalau request bukan AJAX (misalnya fallback)
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

@login_required
def delete_account(request):
    """Delete Event Organizer account + linked user."""
    
    # Pastikan hanya EO yang bisa delete akunnya
    if request.user.role != 'event_organizer':
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "message": "You are not allowed to delete this account."})
        messages.error(request, "Access denied.")
        return redirect('main:show_main')

    user = request.user

    # Aksi hanya boleh lewat POST (supaya tidak ke-delete via GET)
    if request.method == "POST":
        # Hapus profil Event Organizer
        try:
            if hasattr(user, "event_organizer_profile"):
                user.event_organizer_profile.delete()
        except:
            pass
        
        # Logout dulu untuk mencegah session error
        logout(request)

        # Hapus akun user
        user.delete()

        # Jika request via AJAX → balikan JSON
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({
                "success": True, 
                "message": "Account deleted successfully."
            })

        # Non-AJAX → redirect ke halaman utama
        messages.success(request, "Your account has been deleted.")
        return redirect('main:show_main')

    # Jika GET → tolak
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"success": False, "message": "Invalid request method."})

    messages.error(request, "Invalid request.")
    return redirect('event_organizer:profile')


def show_json(request):
    """Show all Event Organizers data in JSON format"""
    organizers = EventOrganizer.objects.select_related('user').all()
    
    data = []
    for organizer in organizers:
        data.append({
            'user_id': organizer.user.id,
            'username': organizer.user.username,
            'email': organizer.user.email,
            'first_name': organizer.user.first_name,
            'last_name': organizer.user.last_name,
            'name': organizer.name,
            'profile_picture': organizer.profile_picture,
            'base_location': organizer.base_location,
            'total_events': organizer.total_events,
            'rating': organizer.rating,
            'review_count': organizer.review_count,
            'coin': organizer.coin,
            'created_at': organizer.created_at.isoformat(),
            'updated_at': organizer.updated_at.isoformat(),
        })
    
    return JsonResponse({
        'status': 'success',
        'count': len(data),
        'data': data
    })