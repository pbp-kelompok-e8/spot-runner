# apss/review/views.py
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json
from .models import Review
from apps.event.models import Event
from apps.main.models import Runner, Attendance


@login_required
@require_POST
def create_review(request, event_id):
    """
    Create a new review for an event.
    Only runners who attended the event can review.
    """
    try:
        event = get_object_or_404(Event, id=event_id)
        runner = request.user.runner
        
        # Check if runner attended the event
        attendance = Attendance.objects.filter(
            runner=runner, 
            event=event,
            status__in=['attending', 'finished']
        ).first()
        
        if not attendance:
            return JsonResponse({
                'success': False,
                'message': 'You must attend this event to leave a review'
            }, status=403)
        
        # Check if review already exists
        if Review.objects.filter(runner=runner, event=event).exists():
            return JsonResponse({
                'success': False,
                'message': 'You have already reviewed this event'
            }, status=400)
        
        # Parse JSON data
        data = json.loads(request.body)
        rating = data.get('rating')
        review_text = data.get('review_text', '').strip()
        
        # Validate rating
        if not rating or not (1 <= int(rating) <= 5):
            return JsonResponse({
                'success': False,
                'message': 'Rating must be between 1 and 5'
            }, status=400)
        
        # Create review
        review = Review.objects.create(
            runner=runner,
            event=event,
            event_organizer=event.user_eo,
            rating=int(rating),
            review_text=review_text
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Review posted successfully',
            'review': {
                'id': str(review.id),
                'rating': review.rating,
                'review_text': review.review_text
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Runner.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Runner profile not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def edit_review(request, review_id):
    """
    Edit an existing review.
    Only the review owner can edit.
    """
    review = get_object_or_404(Review, id=review_id)
    
    # Check authorization
    if request.user != review.runner.user:
        return JsonResponse({
            'success': False,
            'message': 'You are not authorized to edit this review'
        }, status=403)
    
    try:
        # Parse JSON data
        data = json.loads(request.body)
        rating = data.get('rating')
        review_text = data.get('review_text', '').strip()
        
        # Validate rating
        if not rating or not (1 <= int(rating) <= 5):
            return JsonResponse({
                'success': False,
                'message': 'Rating must be between 1 and 5'
            }, status=400)
        
        # Update review
        review.rating = int(rating)
        review.review_text = review_text
        review.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Review updated successfully',
            'review': {
                'id': str(review.id),
                'rating': review.rating,
                'review_text': review.review_text
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def delete_review(request, review_id):
    """
    Delete a review.
    Only the review owner can delete.
    """
    review = get_object_or_404(Review, id=review_id)
    
    # Check authorization
    if request.user != review.runner.user:
        return JsonResponse({
            'success': False,
            'message': 'You are not authorized to delete this review'
        }, status=403)
    
    try:
        review.delete()
        return JsonResponse({
            'success': True,
            'message': 'Review deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)