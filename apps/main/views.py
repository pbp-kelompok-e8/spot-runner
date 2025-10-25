from datetime import date
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from apps.main.models import User
from apps.event.models import Event
from apps.review.models import Review
from django.http import JsonResponse
from apps.main.forms import CustomUserCreationForm
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, logout

# Create your views here.

def show_main(request):
    return render(request, 'main.html')

def register(request):
    form = CustomUserCreationForm()

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been successfully created!')
            return redirect('main:login')
    context = {'form':form}
    return render(request, 'register.html', context)

def login_user(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('main:show_main')

    else:
        form = AuthenticationForm(request)
    context = {'form': form}
    return render(request, 'login.html', context)

@login_required(login_url='main:login')
def show_user(request, username):
    user = get_object_or_404(User, username=username)
    if user != request.user:
        messages.error(request, "You are not authorized to view this profile.")
        return redirect('main:show_main')
    if user.role != 'runner':
        context = {
            'user': user,
        }
        return render(request, "profile.html", context)

    event_list = user.runner.attended_events.all()
    today = date.today()
    
    review_list = user.runner.reviews.all()

    # Update event statuses based on dates
    for event in event_list:
        event_date = event.event_date.date() # Convert datetime to date if needed
        
        if event_date == today:
            event.status = "on_going"
        elif event_date < today:
            event.status = "finished"
        else:  # event_date > today
            event.status = "coming_soon"
        event.save()

    context = {
        'user': user,
        'event_list': event_list,  # Use the updated event_list
        'review_list': review_list
    }

    return render(request, "runner_detail.html", context)

def logout_user(request):
    username = request.user.username
    logout(request)
    response = HttpResponseRedirect(reverse('main:login'))
    messages.success(request, f'See u later, {username}!')
    response.delete_cookie('last_login')
    return response


@login_required
def edit_profile_runner(request, username):
    user = get_object_or_404(User, username=username)
    if user != request.user or user.role != 'runner':
        messages.error(request, "You are not authorized to edit this profile.")
        return redirect('main:show_main')

    if request.method == 'POST':
        try:
            new_username = request.POST.get('username')
            base_location = request.POST.get('base_location', '')

            # Update username
            if new_username and new_username != request.user.username:
                if User.objects.filter(username=new_username).exists():
                    return JsonResponse({"error": "Username already taken"}, status=400)
                request.user.username = new_username
                request.user.save()

            # Update fields
            user.runner.base_location = base_location
            user.runner.save()

            return JsonResponse({
                    "success": True,
                    "username": user.username,
                    "base_location": user.runner.get_base_location_display(),
                    "message": "Profile updated successfully!"
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)

    context = {
        'user': user,
    }
    return render(request, 'edit_profile.html', context)

def cancel_event(request, username, id):
    user = get_object_or_404(User, username=username)
    if user != request.user or user.role != 'runner':
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('main:show_main')
    event = get_object_or_404(Event, pk=id)
    event.event_status = "canceled"
    event.save()
    messages.success(request, f"You have successfully canceled your attendance for {event.name}.")
    return redirect('main:show_user', username=username)

def participate_in_event(request, username, id):
    user = get_object_or_404(User, username=username)
    if user != request.user or user.role != 'runner':
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('main:show_main')
    event = get_object_or_404(Event, pk=id)
    user.runner.attended_events.add(event)
    messages.success(request, f"You are now registered to attend {event.name}.")
    return redirect('main:show_user', username=username)
