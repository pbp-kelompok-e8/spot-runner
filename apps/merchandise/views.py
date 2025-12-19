from django.contrib.auth.decorators import login_required
from apps.merchandise.models import Redemption, Merchandise
from apps.merchandise.forms import MerchandiseForm
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.db.models import Sum, F
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import HttpResponse
import requests
from django.views.decorators.cache import cache_page

# test
# Merchandise landing page
def show_merchandise(request):
    # Initialize default values
    user = request.user
    is_organizer = False
    user_coins = 0
    organizer_coins = 0

    # Get products with optional category filtering
    category = request.GET.get('category', '')
    products = Merchandise.objects.all()
    if category:
        products = products.filter(category=category)

    # Check user role and get relevant data
    if user.is_authenticated:
        # Check if user is an Event Organizer
        # PENTING: Gunakan related_name yang sesuai dengan model
        # Jika model menggunakan related_name='event_organizer_profile'
        # maka gunakan: hasattr(user, 'event_organizer_profile')
        try:
            organizer_profile = user.event_organizer_profile
            is_organizer = True
            
            # Calculate total coins earned from merchandise redemptions
            earned = Redemption.objects.filter(
                merchandise__organizer=organizer_profile
            ).aggregate(
                total=Sum(F('quantity') * F('merchandise__price_coins'))
            )['total']
            organizer_coins = earned or 0
            
        except AttributeError:
            # User is not an organizer
            pass
        
        # Check if user is a Runner (to get their coin balance)
        try:
            runner_profile = user.runner
            user_coins = runner_profile.coin
        except AttributeError:
            # User is not a runner
            pass
    
    context = {
        'user': user,
        'products': products,
        'categories': Merchandise.CATEGORY_CHOICES,
        'selected_category': category,
        'is_organizer': is_organizer,
        'organizer_coins': organizer_coins,
        'user_coins': user_coins,
    }
    
    return render(request, "merchandise_main.html", context)

def product_detail(request, id):
    merchandise = get_object_or_404(Merchandise, id=id)
    
    is_organizer = False
    user_coins = 0
    
    if request.user.is_authenticated:
        # Check if current user is the organizer (to show edit/delete options)
        try:
            organizer_profile = request.user.event_organizer_profile
            is_organizer = merchandise.organizer == organizer_profile
        except AttributeError:
            pass
        
        # Get user coin balance for runners
        try:
            runner_profile = request.user.runner
            user_coins = runner_profile.coin
        except AttributeError:
            pass
    
    context = {
        'merchandise': merchandise,
        'is_organizer': is_organizer,
        'user_coins': user_coins,
    }
    return render(request, "product_detail.html", context)

@login_required(login_url='/login')
def add_merchandise(request):
    """Add new merchandise product - Event Organizer only"""
    # Check if user is event organizer
    try:
        organizer_profile = request.user.event_organizer_profile
    except AttributeError:
        messages.error(request, 'Only event organizers can add merchandise')
        return HttpResponseRedirect('/login')
    
    if request.method == 'POST':
        form = MerchandiseForm(request.POST)
        
        if form.is_valid():
            merchandise = form.save(commit=False)
            merchandise.organizer = organizer_profile
            merchandise.save()
            
            messages.success(request, 'Product added successfully!')
            return HttpResponseRedirect(reverse('merchandise:show_merchandise'))
    else:
        form = MerchandiseForm()
    
    context = {
        'form': form,
        'title': 'Add New Product'
    }
    return render(request, "add_merchandise.html", context)


@login_required(login_url='/login')
def edit_merchandise(request, id):
    """Edit merchandise product - Owner only"""
    merchandise = get_object_or_404(Merchandise, id=id)
    
    # Check ownership
    try:
        organizer_profile = request.user.event_organizer_profile
        if merchandise.organizer != organizer_profile:
            messages.error(request, 'You do not have permission to edit this product')
            return HttpResponseRedirect(reverse('merchandise:show_merchandise'))
    except AttributeError:
        messages.error(request, 'Only event organizers can edit merchandise')
        return HttpResponseRedirect('/login')
    
    if request.method == 'POST':
        form = MerchandiseForm(request.POST, instance=merchandise)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return HttpResponseRedirect(reverse('merchandise:show_merchandise'))
    else:
        form = MerchandiseForm(instance=merchandise)
    
    context = {
        'form': form,
        'merchandise': merchandise,
        'title': 'Edit Product'
    }
    return render(request, "add_merchandise.html", context)


@login_required
@require_POST
def delete_merchandise(request, id):
    """Delete merchandise product - Owner only, AJAX endpoint"""
    merchandise = get_object_or_404(Merchandise, id=id)
    
    # Check ownership
    try:
        organizer_profile = request.user.event_organizer_profile
        if merchandise.organizer != organizer_profile:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    except AttributeError:
        return JsonResponse({'success': False, 'error': 'Only event organizers can delete merchandise'}, status=403)
    
    try:
        merchandise.delete()
        return JsonResponse({'success': True, 'message': 'Product deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
@require_POST
def redeem_merchandise(request, id):
    """Redeem merchandise - Runner only, AJAX endpoint"""
    merchandise = get_object_or_404(Merchandise, id=id)
    
    # Check if user is a runner
    try:
        runner_profile = request.user.runner
    except AttributeError:
        return JsonResponse({'success': False, 'error': 'Only runners can redeem merchandise'}, status=403)
    
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid quantity'}, status=400)
    
    # Validate quantity
    if quantity < 1:
        return JsonResponse({'success': False, 'error': 'Quantity must be at least 1'}, status=400)
    
    if quantity > merchandise.stock:
        return JsonResponse({'success': False, 'error': f'Only {merchandise.stock} items in stock'}, status=400)
    
    # Check if user has enough coins
    total_cost = merchandise.price_coins * quantity
    if runner_profile.coin < total_cost:
        return JsonResponse({
            'success': False, 
            'error': f'Insufficient coins. Need {total_cost}, have {runner_profile.coin}'
        }, status=400)
    
    # Create redemption with explicit values
    redemption = Redemption.objects.create(
        user=runner_profile,
        merchandise=merchandise,
        quantity=quantity,
        price_per_item=merchandise.price_coins,
        total_coins=total_cost
    )
    
    # Update runner coins
    runner_profile.coin -= total_cost
    runner_profile.save()
    
    # Update organizer coins
    merchandise.organizer.coin += total_cost
    merchandise.organizer.save()
    
    # Update merchandise stock
    merchandise.stock -= quantity
    merchandise.save()
    
    return JsonResponse({
        'success': True, 
        'redemption_id': str(redemption.id),
        'total_coins': redemption.total_coins,
        'remaining_coins': runner_profile.coin
    })


@login_required
def history(request):
    """Show redemption history for runners and organizers"""
    user = request.user
    context = {}
    
    # Check if user is a runner
    try:
        runner_profile = user.runner
        redemptions = Redemption.objects.filter(user=runner_profile).order_by('-redeemed_at')
        context.update({
            'user_type': 'runner',
            'redemptions': redemptions,
            'user_coins': runner_profile.coin
        })
        return render(request, 'history.html', context)
    except AttributeError:
        pass
    
    # Check if user is an event organizer
    try:
        organizer_profile = user.event_organizer_profile
        redemptions = Redemption.objects.filter(
            merchandise__organizer=organizer_profile
        ).order_by('-redeemed_at')
        context.update({
            'user_type': 'organizer',
            'redemptions': redemptions,
            'organizer_coins': organizer_profile.coin
        })
        return render(request, 'history.html', context)
    except AttributeError:
        pass
    
    # User is neither runner nor organizer
    messages.error(request, 'Access denied')
    return HttpResponseRedirect('/login')

def show_json(request):
    """Get all merchandise in JSON format"""
    merchandise_list = Merchandise.objects.select_related('organizer__user').all()
    
    # Optional: Filter by category
    category = request.GET.get('category', '')
    if category:
        merchandise_list = merchandise_list.filter(category=category)
    
    data = []
    for merch in merchandise_list:
        data.append({
            'id': str(merch.id),
            'name': merch.name,
            'price_coins': merch.price_coins,
            'description': merch.description,
            'image_url': merch.image_url,
            'category': merch.category,
            'category_display': merch.get_category_display(),
            'stock': merch.stock,
            'available': merch.available,
            'created_at': merch.created_at.isoformat(),
            'updated_at': merch.updated_at.isoformat(),
            'organizer': {
                'id': merch.organizer.user_id,  # user_id is the primary key
                'username': merch.organizer.user.username,
                'name': merch.organizer.name,  # Using the @property
                'profile_picture': merch.organizer.profile_picture,
                'base_location': merch.organizer.get_base_location_display(),
                'rating': merch.organizer.rating,
                'total_events': merch.organizer.total_events,
            }
        })
    
    return JsonResponse(data, safe=False)


def show_json_by_id(request, id):
    """Get single merchandise by ID in JSON format"""
    merchandise = get_object_or_404(
        Merchandise.objects.select_related('organizer__user'), 
        pk=id
    )
    
    # Check if current user is the organizer
    is_owner = False
    if request.user.is_authenticated:
        try:
            is_owner = merchandise.organizer.user_id == request.user.id
        except AttributeError:
            pass
    
    data = {
        'id': str(merchandise.id),
        'name': merchandise.name,
        'price_coins': merchandise.price_coins,
        'description': merchandise.description,
        'image_url': merchandise.image_url,
        'category': merchandise.category,
        'category_display': merchandise.get_category_display(),
        'stock': merchandise.stock,
        'available': merchandise.available,
        'created_at': merchandise.created_at.isoformat(),
        'updated_at': merchandise.updated_at.isoformat(),
        'is_owner': is_owner,
        'organizer': {
            'id': merchandise.organizer.user_id,
            'username': merchandise.organizer.user.username,
            'name': merchandise.organizer.name,
            'profile_picture': merchandise.organizer.profile_picture,
            'base_location': merchandise.organizer.get_base_location_display(),
            'rating': merchandise.organizer.rating,
            'total_events': merchandise.organizer.total_events,
            'review_count': merchandise.organizer.review_count,
        }
    }
    
    return JsonResponse(data)

def show_redemption_json(request):
    """Get all redemptions in JSON format (for history page)"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    user = request.user
    redemptions = None
    user_type = None
    
    # Check if user is a runner
    try:
        runner_profile = user.runner
        # FIX: Runner.user adalah primary key, jadi langsung pakai runner_profile
        redemptions = Redemption.objects.filter(
            user=runner_profile  # runner_profile sudah adalah Runner object
        ).select_related('merchandise__organizer__user').order_by('-redeemed_at')
        user_type = 'runner'
    except AttributeError:
        pass
    
    # Check if user is an event organizer
    if not user_type:
        try:
            organizer_profile = user.event_organizer_profile
            redemptions = Redemption.objects.filter(
                merchandise__organizer=organizer_profile
            ).select_related('merchandise', 'user__user').order_by('-redeemed_at')
            user_type = 'organizer'
        except AttributeError:
            pass
    
    if not user_type:
        return JsonResponse({
            'error': 'User type not found',
            'message': 'User must be a runner or event organizer to view redemption history'
        }, status=403)
    
    data = []
    for redemption in redemptions:
        # Handle deleted merchandise
        merch_data = None
        if redemption.merchandise:
            merch_data = {
                'id': str(redemption.merchandise.id),
                'name': redemption.merchandise.name,
                'image_url': redemption.merchandise.image_url,
                'category': redemption.merchandise.category,
                'category_display': redemption.merchandise.get_category_display(),
            }
        
        redemption_data = {
            'id': str(redemption.id),
            'quantity': redemption.quantity,
            'price_per_item': redemption.price_per_item,
            'total_coins': redemption.total_coins,
            'redeemed_at': redemption.redeemed_at.isoformat(),
            'merchandise': merch_data,
        }
        
        # Add user info if organizer is viewing
        if user_type == 'organizer':
            redemption_data['user'] = {
                'username': redemption.user.user.username if redemption.user else 'Unknown',
            }
        
        data.append(redemption_data)
    
    return JsonResponse({
        'user_type': user_type,
        'redemptions': data
    })


def show_redemption_json_by_id(request, id):
    """Get single redemption by ID"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    redemption = get_object_or_404(
        Redemption.objects.select_related('merchandise', 'user__user'), 
        pk=id
    )
    
    # Check authorization
    user = request.user
    is_authorized = False
    
    # Runner can view their own redemptions
    try:
        runner_profile = user.runner
        # FIX: Compare user_id karena Runner.user adalah primary key
        if redemption.user.user_id == user.id:
            is_authorized = True
    except AttributeError:
        pass
    
    # Organizer can view redemptions of their merchandise
    if not is_authorized:
        try:
            organizer_profile = user.event_organizer_profile
            if redemption.merchandise and redemption.merchandise.organizer.user_id == user.id:
                is_authorized = True
        except AttributeError:
            pass
    
    if not is_authorized:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Handle deleted merchandise
    merch_data = None
    if redemption.merchandise:
        merch_data = {
            'id': str(redemption.merchandise.id),
            'name': redemption.merchandise.name,
            'image_url': redemption.merchandise.image_url,
            'category': redemption.merchandise.category,
            'category_display': redemption.merchandise.get_category_display(),
        }
    
    data = {
        'id': str(redemption.id),
        'quantity': redemption.quantity,
        'price_per_item': redemption.price_per_item,
        'total_coins': redemption.total_coins,
        'redeemed_at': redemption.redeemed_at.isoformat(),
        'merchandise': merch_data,
        'user': {
            'username': redemption.user.user.username if redemption.user else 'Unknown',
        }
    }
    
    return JsonResponse(data)


def get_user_coins(request):
    """Get user coin balance and user type"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    user = request.user
    coins = 0
    user_type = 'guest'
    
    # Check if runner
    try:
        runner_profile = user.runner
        coins = runner_profile.coin
        user_type = 'runner'
    except AttributeError:
        pass
    
    # Check if event organizer
    try:
        organizer_profile = user.event_organizer_profile
        coins = organizer_profile.coin  # Use the coin field from EventOrganizer model
        user_type = 'organizer'
    except AttributeError:
        pass
    
    return JsonResponse({
        'coins': coins,
        'user_type': user_type,
        'username': user.username
    })

@csrf_exempt
@login_required
def create_merchandise_flutter(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    # Check if user is event organizer
    try:
        organizer_profile = request.user.event_organizer_profile
    except AttributeError:
        return JsonResponse({
            'success': False,
            'error': 'Only event organizers can add merchandise'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['name', 'price_coins', 'description', 'image_url', 'category', 'stock']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse({
                    'success': False,
                    'error': f'Field {field} is required'
                }, status=400)
        
        # Validate price_coins and stock are positive integers
        try:
            price_coins = int(data['price_coins'])
            stock = int(data['stock'])
            
            if price_coins < 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Price must be a positive number'
                }, status=400)
            
            if stock < 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Stock must be a positive number'
                }, status=400)
                
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Price and stock must be valid numbers'
            }, status=400)
        
        # Validate category
        valid_categories = ['apparel', 'accessories', 'totebag', 'water_bottle', 'other']
        if data['category'] not in valid_categories:
            return JsonResponse({
                'success': False,
                'error': 'Invalid category'
            }, status=400)
        
        # Create merchandise
        merchandise = Merchandise.objects.create(
            name=data['name'].strip(),
            price_coins=price_coins,
            description=data['description'].strip(),
            image_url=data['image_url'].strip(),
            category=data['category'],
            stock=stock,
            organizer=organizer_profile
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Product created successfully',
            'merchandise_id': str(merchandise.id)
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    

@csrf_exempt
@login_required
def edit_merchandise_flutter(request, id):
    """Edit merchandise product - Owner only (Flutter endpoint)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    merchandise = get_object_or_404(Merchandise, id=id)
    
    # Check ownership
    try:
        organizer_profile = request.user.event_organizer_profile
        if merchandise.organizer != organizer_profile:
            return JsonResponse({
                'success': False,
                'error': 'You do not have permission to edit this product'
            }, status=403)
    except AttributeError:
        return JsonResponse({
            'success': False,
            'error': 'Only event organizers can edit merchandise'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['name', 'price_coins', 'description', 'image_url', 'category', 'stock']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Field {field} is required'
                }, status=400)
            
            if isinstance(data[field], str) and not data[field].strip():
                return JsonResponse({
                    'success': False,
                    'error': f'Field {field} cannot be empty'
                }, status=400)
        
        # Validate price_coins and stock
        try:
            price_coins = int(data['price_coins'])
            stock = int(data['stock'])
            
            if price_coins < 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Price must be a positive number'
                }, status=400)
            
            if stock < 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Stock must be a positive number'
                }, status=400)
                
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Price and stock must be valid numbers'
            }, status=400)
        
        # Validate category
        valid_categories = ['apparel', 'accessories', 'totebag', 'water_bottle', 'other']
        if data['category'] not in valid_categories:
            return JsonResponse({
                'success': False,
                'error': 'Invalid category'
            }, status=400)
        
        # Update merchandise
        merchandise.name = data['name'].strip()
        merchandise.price_coins = price_coins
        merchandise.description = data['description'].strip()
        merchandise.image_url = data['image_url'].strip()
        merchandise.category = data['category']
        merchandise.stock = stock
        merchandise.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Product updated successfully',
            'merchandise_id': str(merchandise.id)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
def delete_merchandise_flutter(request, id):
    """Delete merchandise product - Owner only (Flutter endpoint)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    merchandise = get_object_or_404(Merchandise, id=id)
    
    # Check ownership
    try:
        organizer_profile = request.user.event_organizer_profile
        if merchandise.organizer != organizer_profile:
            return JsonResponse({
                'success': False,
                'error': 'You do not have permission to delete this product'
            }, status=403)
    except AttributeError:
        return JsonResponse({
            'success': False,
            'error': 'Only event organizers can delete merchandise'
        }, status=403)
    
    try:
        merchandise_name = merchandise.name
        merchandise.delete()
        return JsonResponse({
            'success': True,
            'message': f'Product "{merchandise_name}" deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    
@cache_page(60 * 60 * 24)  # Cache 24 jam
def proxy_image(request):
    """Proxy external images to avoid CORS issues"""
    image_url = request.GET.get('url', '')
    
    if not image_url:
        return HttpResponse('No URL provided', status=400)
    
    try:
        # Fetch image from external URL
        response = requests.get(
            image_url, 
            timeout=10,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        if response.status_code == 200:
            # Return image with correct content type
            content_type = response.headers.get('content-type', 'image/jpeg')
            return HttpResponse(response.content, content_type=content_type)
        else:
            return HttpResponse('Image not found', status=404)
            
    except requests.exceptions.RequestException as e:
        return HttpResponse(f'Error fetching image: {str(e)}', status=500)

