from apps.main.models import User, Runner
from django.contrib.auth.forms import UserCreationForm
from apps.event_organizer.models import EventOrganizer 
from django import forms
from django.db import transaction

class CustomUserCreationForm(UserCreationForm):
    base_location = forms.ChoiceField(choices=Runner.LOCATION_CHOICES, required=True)

    profile_picture = forms.URLField(required=False)



    class Meta(UserCreationForm.Meta):
        model = User
        
        fields = UserCreationForm.Meta.fields + ('role','email', 'base_location', 'profile_picture',)
        widgets = {
            'role': forms.RadioSelect
        }

    

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')

        if role == 'runner':
            base_location = cleaned_data.get('base_location')
            
            if not base_location:
                self.add_error('base_location', 'Base location is required for runners.')

        elif role == 'event_organizer':
            profile_picture = cleaned_data.get('profile_picture')
            base_location = cleaned_data.get('base_location')

            if not base_location:
                self.add_error('base_location', 'Base location is required for event organizers.')

        return cleaned_data
    
    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        user.save()

        if self.cleaned_data['role'] == 'runner':
            Runner.objects.create(
                user=user,
                base_location=self.cleaned_data['base_location']
            )
        elif self.cleaned_data['role'] == 'event_organizer':
            EventOrganizer.objects.create(
                user=user,
                profile_picture=self.cleaned_data['profile_picture'],
                base_location=self.cleaned_data['base_location']
            )
        return user