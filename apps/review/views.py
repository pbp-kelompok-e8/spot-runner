from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Review
from apps.event.models import Event

@login_required
def create_review(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        event_id = request.POST.get('event_id')
        rating = request.POST.get('rating')
        review_text = request.POST.get('review_text', '')

        event = get_object_or_404(Event, id=event_id)

        review, created = Review.objects.update_or_create(
            user=request.user,
            event=event,
            defaults={'rating': rating, 'review_text': review_text},
        )

        data = {
            'user': request.user.username,
            'event': event.name,
            'rating': review.rating,
            'review_text': review.review_text,
            'created_at': review.created_at.strftime("%d %b %Y"),
        }
        return JsonResponse({'success': True, 'review': data})

    return JsonResponse({'success': False}, status=400)
