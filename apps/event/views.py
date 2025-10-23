from django.shortcuts import render, redirect, get_object_or_404
from .forms import EventForm
from .models import Event
# from event_organizer.models import EventOrganizer
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.urls import reverse

# Create your views here.
# @login_required(login_url='/login')
def create_event(request):
    form = EventForm(request.POST or None)

    if form.is_valid() and request.method == 'POST':
        event_entry = form.save(commit = False)
        event_entry.user = request.user
        event_entry.save()
        return redirect('main:show_main')

    context = {
        'form': form
    }

    return render(request, "create_event.html", context)


def edit_event(request, id):
    event = get_object_or_404(Event, pk=id)
    form = EventForm(request.POST or None, instance=event)
    if form.is_valid() and request.method == 'POST':
        form.save()
        return redirect('main:show_main')
    context = {
        'form': form
    }
    return render(request, "edit_event.html", context)

def delete_event(request, id):
    event = get_object_or_404(Event, pk=id)
    event.delete()
    return HttpResponseRedirect(reverse('main:show_main'))


# @login_required(login_url='/login')
def show_event(request, id):
    event = get_object_or_404(Event, pk=id)
    context = {
        'event': event
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
            'event_status' : event.get_event_status_display(),
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
                'username': event.user_eo.username if event.user_eo else None
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
        'event_status' : event.get_event_status_display(),
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
            'username': event.user_eo.username if event.user_eo_id else None
            },        
        'event_categories': category_names 
    }
    return JsonResponse(data)


