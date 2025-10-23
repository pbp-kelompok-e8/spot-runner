from django import forms
from .models import Event, EventCategory
from django.utils.html import strip_tags
from django.forms import inlineformset_factory

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'name', 
            'description', 
            'location', 
            'image', 
            'image2', 
            'image3',
            'event_date',
            'regist_deadline',
            'contact',
            'capacity',
            'event_status',
            'coin',
            'event_category'
        ]

        widgets = {
                'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter event name'}),
                'description': forms.Textarea(attrs={'class': 'form-textarea', 'placeholder': 'Enter event description...', 'rows': 5}),
                'location': forms.Select(attrs={'class': 'form-select'}),
                'image': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://example.com/image1.png'}),
                'image2': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://example.com/image2.png'}),
                'image3': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://example.com/image3.png'}),
                'event_date': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
                'regist_deadline': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
                'contact': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter phone number'}),
                'capacity': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Enter max participants'}),
                'coin': forms.NumberInput(attrs={'class': 'form-input'}),
                'event_category': forms.CheckboxSelectMultiple, 
            }
    def clean_name(self):
        name = self.cleaned_data["name"]
        return strip_tags(name)

    def clean_description(self):
        description = self.cleaned_data["description"]
        return strip_tags(description)