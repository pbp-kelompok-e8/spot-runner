from django.shortcuts import render, redirect, get_object_or_404
from .forms import EventForm
from django.views.decorators.http import require_POST
from .models import Event
from apps.event_organizer.models import EventOrganizer
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from apps.review.models import Review

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
        try:
            event = get_object_or_404(Event, pk=id)
            if event.user_eo != request.user.event_organizer_profile:
                return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
            event.delete()
            return redirect('main:show_main')
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)   
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
            'event_date': event.event_date.isoformat(),
            'regist_deadline': event.regist_deadline.isoformat(),
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

