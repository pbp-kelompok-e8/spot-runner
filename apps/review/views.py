from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Review
from apps.event.models import Event
from apps.main.models import Runner

@login_required
def create_review(request, event_id):
    # Debug logging
    print(f"=== CREATE REVIEW CALLED ===")
    print(f"Method: {request.method}")
    print(f"Event ID: {event_id} (type: {type(event_id)})")
    print(f"Is AJAX: {request.headers.get('X-Requested-With')}")
    print(f"POST data: {request.POST}")
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        rating = request.POST.get('rating')
        review_text = request.POST.get('review_text', '')

        # Validasi rating
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return JsonResponse({
                    'success': False, 
                    'error': 'Rating must be between 1 and 5'
                }, status=400)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False, 
                'error': 'Invalid rating'
            }, status=400)

        # Cari event berdasarkan UUID
        try:
            event = Event.objects.get(id=event_id)
            print(f"✅ Event found: {event.name}")
        except Event.DoesNotExist:
            print(f"❌ Event not found: {event_id}")
            return JsonResponse({
                'success': False, 
                'error': 'Event not found'
            }, status=404)

        # Pastikan user adalah Runner
        try:
            runner = Runner.objects.get(user=request.user)
            print(f"✅ Runner found: {runner.user.username}")
        except Runner.DoesNotExist:
            print(f"❌ Runner not found for user: {request.user.username}")
            return JsonResponse({
                'success': False, 
                'error': 'Only runners can post reviews'
            }, status=403)

        # Ambil EO dari event
        event_organizer = getattr(event, 'user_eo', None)

        # Simpan review (update jika sudah ada)
        review, created = Review.objects.update_or_create(
            runner=runner,
            event=event,
            defaults={
                'rating': rating,
                'review_text': review_text,
                'event_organizer': event_organizer,
            }
        )

        action = "created" if created else "updated"
        print(f"✅ Review {action}: ID={review.id}, Rating={review.rating}")

        # Kirim response JSON
        data = {
            'user': request.user.username,
            'event': event.name,
            'rating': review.rating,
            'review_text': review.review_text,
            'created_at': review.created_at.strftime("%d %b %Y"),
        }
        return JsonResponse({'success': True, 'review': data})

    print(f"❌ Invalid request method or not AJAX")
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request'
    }, status=400)
