from apps.main.models import User, Runner
from django.contrib.auth.forms import UserCreationForm
from apps.event_organizer.models import EventOrganizer 
from django import forms
from django.db import transaction

class CustomUserCreationForm(UserCreationForm):
    base_location = forms.ChoiceField(choices=Runner.LOCATION_CHOICES, required=False)
    profile_picture = forms.URLField(required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('role','email', 'profile_picture',)
        widgets = {
            'role': forms.RadioSelect
        }

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')

        # Handle base_location dari form data (bisa dari runner atau organizer field)
        if role == 'runner':
            base_location = cleaned_data.get('base_location')
            if not base_location:
                self.add_error('base_location', 'Base location is required for runners.')

        elif role == 'event_organizer':
            # Untuk event organizer, base_location sudah dikirim dengan name="base_location"
            base_location = cleaned_data.get('base_location')
            profile_picture = cleaned_data.get('profile_picture')
            
            if not base_location:
                self.add_error('base_location', 'Base location is required for event organizers.')
            if not profile_picture:
                self.add_error('profile_picture', 'Profile picture is required for event organizers.')

        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        user.save()

        base_location = self.cleaned_data.get('base_location')

        if self.cleaned_data['role'] == 'runner':
            Runner.objects.create(
                user=user,
                base_location=base_location
            )
        elif self.cleaned_data['role'] == 'event_organizer':
            EventOrganizer.objects.create(
                user=user,
                profile_picture=self.cleaned_data.get('profile_picture', ''),
                base_location=base_location
            )
        return user