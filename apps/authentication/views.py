import json
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth import get_user_model # Gunakan ini agar kompatibel dengan Custom User
from apps.main.models import Runner # Import model Runner
from apps.event_organizer.models import EventOrganizer # Import model EventOrganizer (sesuaikan path jika beda)

@csrf_exempt
def login(request):
    if request.method == 'POST':
        # Gunakan .get() agar tidak error 500 jika key tidak ada
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        
        if user is not None:
            if user.is_active:
                auth_login(request, user)
                return JsonResponse({
                    "username": user.username,
                    "status": True,
                    "message": "Login successful!",
                    "role": getattr(user, 'role', 'runner') # Kirim role ke flutter jika perlu
                }, status=200)
            else:
                return JsonResponse({
                    "status": False,
                    "message": "Login failed, account is disabled."
                }, status=401)
        else:
            return JsonResponse({
                "status": False,
                "message": "Login failed, please check your username or password."
            }, status=401)
            
    return JsonResponse({"status": False, "message": "Method not allowed"}, status=405)

@csrf_exempt
def register(request):
    User = get_user_model() # Ambil model user yang aktif di settings

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            username = data.get('username')
            password1 = data.get('password') # Sesuaikan key dengan map di Flutter
            password2 = data.get('password_confirm') # Sesuaikan key dengan map di Flutter
            email = data.get('email', '')
            role = data.get('role', 'runner') # Default runner
            base_location = data.get('base_location', '')
            profile_picture = data.get('profile_picture', '')

            # Validasi input dasar
            if not username or not password1 or not password2:
                return JsonResponse({"status": False, "message": "Fields cannot be empty."}, status=400)

            if password1 != password2:
                return JsonResponse({"status": False, "message": "Passwords do not match."}, status=400)
            
            if User.objects.filter(username=username).exists():
                return JsonResponse({"status": False, "message": "Username already exists."}, status=400)
            
            # 1. Buat User Baru
            user = User.objects.create_user(username=username, password=password1, email=email)
            
            # Set Role jika User model punya field role
            if hasattr(user, 'role'):
                user.role = role
                user.save()

            # 2. Buat Profile Berdasarkan Role (PENTING!)
            if role == 'runner':
                # Pastikan field 'base_location' ada di model Runner Anda
                Runner.objects.create(user=user, base_location=base_location)
                
            elif role == 'event_organizer':
                # Pastikan model EventOrganizer sesuai
                EventOrganizer.objects.create(
                    user=user, 
                    base_location=base_location,
                    profile_picture=profile_picture
                )

            return JsonResponse({
                "username": user.username,
                "status": 'success',
                "message": "User created successfully!"
            }, status=200)
            
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"An error occurred: {str(e)}"
            }, status=500)
    
    else:
        return JsonResponse({
            "status": False,
            "message": "Invalid request method."
        }, status=405)

@csrf_exempt
def logout(request):
    # Cek apakah user terautentikasi sebelum akses username
    if not request.user.is_authenticated:
        return JsonResponse({
            "status": False,
            "message": "User not logged in."
        }, status=401)

    username = request.user.username
    try:
        auth_logout(request)
        return JsonResponse({
            "username": username,
            "status": True,
            "message": "Logged out successfully!"
        }, status=200)
    except:
        return JsonResponse({
            "status": False,
            "message": "Logout failed."
        }, status=500)