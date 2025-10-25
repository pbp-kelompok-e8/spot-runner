# apps/review/views.py

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Review
from apps.event.models import Event
from apps.main.models import Runner
from apps.event_organizer.models import EventOrganizer

@login_required
def create_review(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        event_id = request.POST.get('event_id')
        rating = request.POST.get('rating')
        review_text = request.POST.get('review_text', '')

        # Validasi rating
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return JsonResponse({'success': False, 'error': 'Rating must be between 1 and 5'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid rating'}, status=400)

        # Get event
        event = get_object_or_404(Event, id=event_id)
        
        # Get runner profile (pastikan user adalah runner)
        try:
            runner = Runner.objects.get(user=request.user)
        except Runner.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Only runners can post reviews'}, status=403)
        
        # Get event organizer
        event_organizer = event.user_eo

        # Create or update review
        review, created = Review.objects.update_or_create(
            runner=runner,
            event=event,
            defaults={
                'rating': rating, 
                'review_text': review_text,
                'event_organizer': event_organizer
            },
        )

        data = {
            'user': request.user.username,
            'event': event.name,
            'rating': review.rating,
            'review_text': review.review_text,
            'created_at': review.created_at.strftime("%d %b %Y"),
        }
        return JsonResponse({'success': True, 'review': data})

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
