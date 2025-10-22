from django.shortcuts import render, redirect, get_object_or_404
from .forms import EventForm
from .models import Event
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags

# Create your views here.
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


@login_required(login_url='/login')
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
    event_list = Event.objects.all()
    data = [
        {
            'id': str(event.id),
            'name': event.name,
            'description': event.description,
            'location': event.location, 
            'event_category': event.event_category,
            'image': event.image,
            'image2': event.image2,
            'image3': event.image3,
            'event_date': event.event_date.isoformat(),
            'regist_deadline': event.regist_deadline.isoformat(),
            'distance': event.distance,
            'contact': event.contact,
            'capacity': event.capacity,
            'total_participans': event.total_participans,
            'full': event.full,
            'event_status' : event.event_status,
            'user_eo_id': event.user_eo_id
        }
        for event in event_list
    ]

    return JsonResponse(data, safe=False)

def show_xml_by_id(request, news_id):
   try:
       event_item = Event.objects.filter(pk=news_id)
       xml_data = serializers.serialize("xml", event_item)
       return HttpResponse(xml_data, content_type="application/xml")
   except Event.DoesNotExist:
       return HttpResponse(status=404)

def show_json_by_id(request, news_id):
    try:
        event = Event.objects.select_related('user').get(pk=news_id)
        data = {
            'id': str(event.id),
            'name': event.name,
            'description': event.description,
            'location': event.location, 
            'event_category': event.event_category,
            'image': event.image,
            'image2': event.image2,
            'image3': event.image3,
            'event_date': event.event_date.isoformat(),
            'regist_deadline': event.regist_deadline.isoformat(),
            'distance': event.distance,
            'contact': event.contact,
            'capacity': event.capacity,
            'total_participans': event.total_participans,
            'full': event.full,
            'event_status' : event.event_status,
            'user_eo_id': event.user_eo_id,
            'user_username': event.user_eo.username if event.user_id else None
        }
        return JsonResponse(data)
    except Event.DoesNotExist:
        return JsonResponse({'detail': 'Not found'}, status=404)


