from django.shortcuts import render, redirect, get_object_or_404

from apps.main.models import User
from .forms import EventForm
from django.views.decorators.http import require_POST
from .models import Event, EventCategory
from apps.event_organizer.models import EventOrganizer
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from apps.review.models import Review
from django.contrib import messages
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import strip_tags
from datetime import datetime

@login_required
def create_event(request):
    try:
        event_organizer = request.user.event_organizer_profile
    except EventOrganizer.DoesNotExist:
        raise PermissionDenied("Anda harus menjadi Event Organizer untuk membuat event.")

    if request.method == 'POST':
        form = EventForm(request.POST)
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        if form.is_valid():
            event_entry = form.save(commit=False)
            event_entry.user_eo = event_organizer 
            event_entry.save()
            form.save_m2m() 
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('event_organizer:dashboard')
                })
            else:
                return redirect('main:show_main')
        else:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors.get_json_data()
                })
            else:
                pass 
    else:
        form = EventForm()

    context = {
        'form': form
    }
    return render(request, "create_event.html", context)

@login_required 
def edit_event(request, id):
    event = get_object_or_404(Event, pk=id)
    if event.user_eo.user != request.user: 
        raise PermissionDenied("Anda tidak diizinkan untuk mengedit event ini.")
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event) 
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        if form.is_valid():
            event_instance = form.save(commit=False) 
            event_instance.save() 
            form.save_m2m() 
            detail_url = reverse('event:show_event', kwargs={'id': event.id})
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'redirect_url': detail_url
                })
            else:
                return redirect('main:show_main')
        else:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors.get_json_data()
                })
            else:
                pass 
    else: 
        form = EventForm(instance=event) 
    context = {
        'form': form,
        'event': event 
    }
    return render(request, "edit_event.html", context)

@login_required
def delete_event(request, id):
    if request.method == 'POST':
        event = get_object_or_404(Event, pk=id)
        if event.user_eo != request.user.event_organizer_profile:
            messages.error(request, 'You are not authorized to delete this event.')
            return redirect('event:show_event', id=id)
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        event.delete()
        
        if is_ajax:
            return JsonResponse({
                'success': True, 
                'message': 'Event deleted successfully.'
            })
        else:
            messages.success(request, 'Event deleted successfully!')
            return redirect('main:show_main') 
    
    return HttpResponseBadRequest("Invalid request method")


@login_required(login_url='/login')
def show_event(request, id):
    event = get_object_or_404(Event, pk=id)
    reviews = Review.objects.filter(event=event).select_related('runner__user').order_by('-created_at')
    context = {
        'event': event,
        'reviews': reviews,
    }
    return render(request, "event_detail.html", context)

def show_xml(request):
    event_list = Event.objects.all()
    xml_data = serializers.serialize("xml", event_list)
    return HttpResponse(xml_data, content_type="application/xml")

def show_json(request):
    event_list = Event.objects.prefetch_related('event_category', 'user_eo').all()
    data = []
    for event in event_list:        
        category_names = [
            category.get_category_display() 
            for category in event.event_category.all()
        ]        
        data.append({
            'id': str(event.id),
            'name': event.name,
            'description': event.description,
            'location': event.get_location_display(), 
            'event_status' : event.event_status,
            'image': event.image,
            'image2': event.image2,
            'image3': event.image3,
            'event_date': event.event_date.isoformat() if event.event_date else None,
            'regist_deadline': event.regist_deadline.isoformat() if event.regist_deadline else None,
            'contact': event.contact,
            'capacity': event.capacity,
            'total_participans': event.total_participans,
            'full': event.full,            
            'coin': event.coin, 
            'user_eo': {
                'id': event.user_eo_id,
                'username': event.user_eo.user.username if event.user_eo else None
                },            
            'event_categories': category_names 
        })
        
    return JsonResponse(data, safe=False)

def show_xml_by_id(request, event_id):
   try:
       event_item = Event.objects.filter(pk=event_id)
       xml_data = serializers.serialize("xml", event_item)
       return HttpResponse(xml_data, content_type="application/xml")
   except Event.DoesNotExist:
       return HttpResponse(status=404)

def show_json_by_id(request, event_id):
    event = get_object_or_404(
        Event.objects.prefetch_related('event_category', 'user_eo'), 
        pk=event_id
    )
    category_names = [
        category.get_category_display() 
        for category in event.event_category.all() 
    ]
    data = {
        'id': str(event.id),
        'name': event.name,
        'description': event.description,
        'location': event.get_location_display(), 
        'event_status' : event.status,
        'image': event.image,
        'image2': event.image2,
        'image3': event.image3,
        'event_date': event.event_date.isoformat(),
        'regist_deadline': event.regist_deadline.isoformat(),
        'contact': event.contact,
        'capacity': event.capacity,
        'total_participans': event.total_participans,
        'full': event.full,        
        'coin' : event.coin, 
        'user_eo': {
            'id': event.user_eo_id,
            'username': event.user_eo.user.username if event.user_eo_id else None
            },        
        'event_categories': category_names 
    }
    return JsonResponse(data)

@csrf_exempt
def create_event_flutter(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = request.user
        if not user.is_authenticated:
            user = User.objects.first()
        try:
            eo_profile = EventOrganizer.objects.get(user=user)
        except EventOrganizer.DoesNotExist:
            return JsonResponse({
                "status": "error", 
                "message": f"User {user.username} tidak terdaftar sebagai Event Organizer!"
            }, status=500)
        
        event_date_str = data.get("event_date")
        regist_deadline_str = data.get("regist_deadline")
        
        event_date = None
        regist_deadline = None

        if event_date_str:
            event_date = datetime.fromisoformat(event_date_str)
        
        if regist_deadline_str:
            regist_deadline = datetime.fromisoformat(regist_deadline_str)
        
        new_event = Event(
            name=data.get("name"),
            description=data.get("description"),
            location=data.get("location"),
            image=data.get("image1"),
            image2=data.get("image2"),
            image3=data.get("image3"),
            event_date=event_date,
            regist_deadline=regist_deadline,
            contact=data.get("contact"),
            capacity=int(data.get("capacity", 0)),
            coin=int(data.get("coin", 0)),
            total_participans=0,
            user_eo=eo_profile,
             
        )
        new_event.save()
        categories_data = data.get("categories", []) 
        if categories_data:
            for cat_name in categories_data:
                category_obj = EventCategory.objects.filter(category=cat_name).first()
                
                if category_obj:
                    new_event.event_category.add(category_obj)

        return JsonResponse({"status": "success"}, status=200)

@csrf_exempt
def edit_event_flutter(request, event_id):
    if request.method == 'POST':
        try:
            event = Event.objects.get(pk=event_id)
            data = json.loads(request.body)
            event.name = data.get("name")
            event.description = data.get("description")
            event.location = data.get("location")
            event.image = data.get("image1") 
            event.image2 = data.get("image2")
            event.image3 = data.get("image3")
            event.contact = data.get("contact")
            event.capacity = int(data.get("capacity", 0))
            event.coin = int(data.get("coin", 0))
            if data.get("event_date"):
                event.event_date = datetime.fromisoformat(data.get("event_date"))
            if data.get("regist_deadline"):
                event.regist_deadline = datetime.fromisoformat(data.get("regist_deadline"))
            event.save()
            categories_data = data.get("categories", [])
            if categories_data:
                event.event_category.clear()
                for cat_name in categories_data:
                    cat_obj = EventCategory.objects.filter(category=cat_name).first()
                    if cat_obj:
                        event.event_category.add(cat_obj)

            return JsonResponse({"status": "success"}, status=200)

        except Event.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Event not found"}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid method"}, status=401)

@csrf_exempt
def delete_event_flutter(request, event_id):
    if request.method == 'POST':
        try:
            event = Event.objects.get(pk=event_id)
            event.delete()

            return JsonResponse({"status": "success", "message": "Event deleted successfully"}, status=200)

        except Event.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Event not found"}, status=404)

    return JsonResponse({"status": "error", "message": "Invalid method"}, status=401)