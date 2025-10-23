from apps.main.models import User, Runner
from apps.event_organizer import EventOrganizer
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.db import transaction

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    base_location = forms.ChoiceField(choices=User.RUNNER_LOCATION_CHOICES, required=True)


    class Meta(UserCreationForm.Meta):
        model = User
        
        fields = UserCreationForm.Meta.fields + ('role','email', 'base_location')
        widgets = {
            'role': forms.RadioSelect
        }

    

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')

        if role == 'runner':
            email = cleaned_data.get('email')
            base_location = cleaned_data.get('base_location')

            if not email:
                self.add_error('email', 'Email is required for runners.')
            if not base_location:
                self.add_error('base_location', 'Base location is required for runners.')

        elif role == 'event_organizer':
            pass

        return cleaned_data
    
    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        
        if self.cleaned_data['role'] == 'runner':
            Runner.objects.create(
                user=user,
                email=self.cleaned_data['email'],
                base_location=self.cleaned_data['base_location']
            )
        elif self.cleaned_data['role'] == 'event_organizer':
            pass
        return user