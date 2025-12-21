# apps/review/views.py
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import strip_tags
from django.db import IntegrityError
import json
from .models import Review
from apps.event.models import Event
from apps.main.models import Runner, Attendance

@require_http_methods(["GET"])
def get_all_reviews(request):
    """
    Get all reviews atau filter by event_id
    URL: /api/reviews/ atau /api/reviews/?event_id=123
    
    PENTING: Jika user login sebagai Runner, hanya return review milik user tersebut
    untuk keperluan cek review status
    """
    try:
        event_id = request.GET.get('event_id', None)
        
        # Filter by event_id jika ada
        if event_id:
            reviews = Review.objects.filter(event_id=event_id).select_related('runner__user', 'event')
        else:
            # Jika tidak ada event_id, filter by user yang login (untuk cek status)
            if request.user.is_authenticated:
                try:
                    runner = request.user.runner
                    # HANYA RETURN REVIEW MILIK USER INI
                    reviews = Review.objects.filter(runner=runner).select_related('runner__user', 'event')
                    print(f"✅ Found {reviews.count()} reviews for user {request.user.username}")
                except:
                    # Bukan runner, return semua review
                    reviews = Review.objects.all().select_related('runner__user', 'event')
            else:
                reviews = Review.objects.all().select_related('runner__user', 'event')
        
        # Build response data
        reviews_data = []
        for review in reviews:
            reviews_data.append({
                'id': str(review.id),
                'runner_name': review.runner.user.username,
                'event_id': str(review.event.id),
                'event_name': review.event.name,
                'review_text': review.review_text,
                'rating': review.rating,
                'created_at': review.created_at.isoformat(),
                'is_owner': request.user.is_authenticated and request.user == review.runner.user,
            })
        
        return JsonResponse({
            'status': 'success',
            'data': reviews_data,
            'count': len(reviews_data)
        }, status=200)
    
    except Exception as e:
        print(f"❌ Error in get_all_reviews: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_review_detail(request, review_id):
    """
    Get single review by ID
    URL: /api/reviews/<review_id>/
    """
    try:
        review = Review.objects.select_related('runner__user', 'event').get(id=review_id)
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'id': str(review.id),
                'runner_name': review.runner.user.username,
                'event_id': str(review.event.id),
                'event_name': review.event.name,
                'review_text': review.review_text,
                'rating': review.rating,
                'created_at': review.created_at.isoformat(),
                'is_owner': request.user.is_authenticated and request.user == review.runner.user,
            }
        }, status=200)
    
    except Review.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Review not found'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_event_reviews(request, event_id):
    """
    Get all reviews for a specific event
    URL: /api/reviews/event/<event_id>/
    """
    try:
        event = get_object_or_404(Event, id=event_id)
        reviews = Review.objects.filter(event=event).select_related('runner__user')
        
        reviews_data = []
        total_rating = 0
        
        for review in reviews:
            reviews_data.append({
                'id': str(review.id),
                'runner_name': review.runner.user.username,
                'review_text': review.review_text,
                'rating': review.rating,
                'created_at': review.created_at.isoformat(),
                'is_owner': request.user.is_authenticated and request.user == review.runner.user,
            })
            total_rating += review.rating
        
        avg_rating = round(total_rating / len(reviews), 2) if len(reviews) > 0 else 0
        
        return JsonResponse({
            'status': 'success',
            'event': {
                'id': str(event.id),
                'name': event.name,
            },
            'reviews': reviews_data,
            'average_rating': avg_rating,
            'total_reviews': len(reviews_data)
        }, status=200)
    
    except Event.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Event not found'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_POST
def create_review(request, event_id):
    """
    Create a new review for an event.
    Only runners who attended the event can review.
    URL: /api/reviews/create/<event_id>/
    """
    # Manual auth check karena @login_required tidak bekerja dengan @csrf_exempt
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)
    
    try:
        event = get_object_or_404(Event, id=event_id)
        
        # Get runner profile
        try:
            runner = request.user.runner
        except Runner.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Runner profile not found'
            }, status=404)
        
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
        
        # Check if review already exists (PENTING!)
        existing_review = Review.objects.filter(runner=runner, event=event).first()
        if existing_review:
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
                'review_text': review.review_text,
                'runner_name': runner.user.username,
                'event_name': event.name,
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except IntegrityError as e:
        # Tangkap duplicate review error
        return JsonResponse({
            'success': False,
            'message': 'You have already reviewed this event'
        }, status=409)
    except Exception as e:
        print(f"Create review error: {e}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@csrf_exempt 
@require_POST
def edit_review(request, review_id):
    """
    Edit an existing review.
    Only the review owner can edit.
    URL: /api/reviews/edit/<review_id>/
    """
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)
    
    try:
        review = Review.objects.get(id=review_id)
    except Review.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Review not found'
        }, status=404)
    
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
        print(f"Edit review error: {e}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@csrf_exempt 
@require_POST
def delete_review(request, review_id):
    """
    Delete a review (HARD DELETE).
    Only the review owner can delete.
    URL: /api/reviews/delete/<review_id>/
    """
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)
    
    try:
        review = Review.objects.get(id=review_id)
    except Review.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Review not found'
        }, status=404)
    
    # Check authorization
    if request.user != review.runner.user:
        return JsonResponse({
            'success': False,
            'message': 'You are not authorized to delete this review'
        }, status=403)
    
    try:
        # HARD DELETE - review benar-benar dihapus dari database
        review.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Review deleted successfully'
        })
    except Exception as e:
        print(f"Delete review error: {e}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


# ============================================
# DEPRECATED: create_review_flutter
# Gunakan create_review() saja
# ============================================
@csrf_exempt
def create_review_flutter(request):
    """
    DEPRECATED: Gunakan create_review() saja
    Tetap ada untuk backward compatibility
    """
    if request.method != 'POST':
        return JsonResponse({
            "status": "error", 
            "message": "Method not allowed"
        }, status=405)
    
    if not request.user.is_authenticated:
        return JsonResponse({
            "status": "error", 
            "message": "Authentication required"
        }, status=401)
    
    try:
        data = json.loads(request.body)
        review_text = strip_tags(data.get("review_text", "")) 
        rating = data.get("rating")
        event_id = data.get("event_id")
        
        if not review_text or rating is None or not event_id:
            return JsonResponse({
                "status": "error", 
                "message": "Missing required fields: review_text, rating, or event_id"
            }, status=400)

        if not (1 <= int(rating) <= 5):
            return JsonResponse({
                "status": "error", 
                "message": "Rating must be between 1 and 5"
            }, status=400)

        try:
            runner_instance = Runner.objects.get(user=request.user)
        except Runner.DoesNotExist:
            return JsonResponse({
                "status": "error", 
                "message": "Runner profile not found"
            }, status=404)

        try:
            event_instance = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            return JsonResponse({
                "status": "error", 
                "message": f"Event with ID {event_id} not found"
            }, status=404)
        
        # Check if review already exists
        if Review.objects.filter(runner=runner_instance, event=event_instance).exists():
            return JsonResponse({
                "status": "error", 
                "message": "You have already reviewed this event"
            }, status=409)
        
        new_review = Review.objects.create(
            runner=runner_instance,
            event=event_instance,
            event_organizer=event_instance.user_eo,
            review_text=review_text,
            rating=rating,
        )
        
        return JsonResponse({
            "status": "success", 
            "message": "Review created successfully",
            "review_id": str(new_review.id)
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({
            "status": "error", 
            "message": "Invalid JSON format"
        }, status=400)
    
    except IntegrityError:
        return JsonResponse({
            "status": "error", 
            "message": "You have already reviewed this event"
        }, status=409)
        
    except Exception as e:
        print(f"Server Error: {e}")
        return JsonResponse({
            "status": "error", 
            "message": "An internal server error occurred"
        }, status=500)


@csrf_exempt
def edit_review_flutter(request, review_id):
    """
    Edit review - Flutter specific endpoint
    URL: /api/reviews/edit-flutter/<review_id>/
    """
    if request.method != 'POST':
        return JsonResponse({
            "status": "error",
            "message": "Method not allowed"
        }, status=405)
    
    if not request.user.is_authenticated:
        return JsonResponse({
            "status": "error",
            "message": "Authentication required"
        }, status=401)
    
    try:
        review = Review.objects.get(id=review_id)
    except Review.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": "Review not found"
        }, status=404)
    
    # Check authorization
    if request.user != review.runner.user:
        return JsonResponse({
            "status": "error",
            "message": "You are not authorized to edit this review"
        }, status=403)
    
    try:
        data = json.loads(request.body)
        review_text = strip_tags(data.get("review_text", ""))
        rating = data.get("rating")
        
        if not review_text or rating is None:
            return JsonResponse({
                "status": "error",
                "message": "Missing required fields: review_text or rating"
            }, status=400)
        
        if not (1 <= int(rating) <= 5):
            return JsonResponse({
                "status": "error",
                "message": "Rating must be between 1 and 5"
            }, status=400)
        
        # Update review
        review.rating = int(rating)
        review.review_text = review_text
        review.save()
        
        return JsonResponse({
            "status": "success",
            "message": "Review updated successfully",
            "review": {
                "id": str(review.id),
                "rating": review.rating,
                "review_text": review.review_text
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "status": "error",
            "message": "Invalid JSON format"
        }, status=400)
    except Exception as e:
        print(f"Edit review flutter error: {e}")
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)


@csrf_exempt
def delete_review_flutter(request, review_id):
    """
    Delete review - Flutter specific endpoint
    URL: /api/reviews/delete-flutter/<review_id>/
    """
    if request.method != 'POST':
        return JsonResponse({
            "status": "error",
            "message": "Method not allowed"
        }, status=405)
    
    if not request.user.is_authenticated:
        return JsonResponse({
            "status": "error",
            "message": "Authentication required"
        }, status=401)
    
    try:
        review = Review.objects.get(id=review_id)
    except Review.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": "Review not found"
        }, status=404)
    
    # Check authorization
    if request.user != review.runner.user:
        return JsonResponse({
            "status": "error",
            "message": "You are not authorized to delete this review"
        }, status=403)
    
    try:
        # HARD DELETE
        review.delete()
        
        return JsonResponse({
            "status": "success",
            "message": "Review deleted successfully"
        })
    except Exception as e:
        print(f"Delete review flutter error: {e}")
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)