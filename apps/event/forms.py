from django import forms
from .models import Event 
from django.utils.html import strip_tags

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'name', 
            'description', 
            'location', 
            'event_category',
            'image', 
            'image2', 
            'image3',
            'event_date',
            'regist_deadline',
            'distance',
            'contact',
            'capacity',
        ]
        
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'event_category': forms.CheckboxSelectMultiple,
            'event_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'regist_deadline': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
        }
    def clean_name(self):
        name = self.cleaned_data["name"]
        return strip_tags(name)

    def clean_description(self):
        description = self.cleaned_data["description"]
        return strip_tags(description)