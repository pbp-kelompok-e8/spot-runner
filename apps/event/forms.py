from django import forms
from .models import Event, EventCategory
from django.utils.html import strip_tags
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError 
from django.utils import timezone

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
            # 'event_status',
            'coin',
            'event_category'
        ]
        now_iso = timezone.now().strftime('%Y-%m-%dT%H:%M')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter event name'}),
            'description': forms.Textarea(attrs={'placeholder': 'Enter event description...', 'rows': 5}),
            'location': forms.Select(),
            'image': forms.URLInput(attrs={'placeholder': 'https://example.com/image1.png'}),
            'image2': forms.URLInput(attrs={'placeholder': 'https://example.com/image2.png'}),
            'image3': forms.URLInput(attrs={'placeholder': 'https://example.com/image3.png'}),
            'event_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'min': now_iso}),
            'regist_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local', 'min': now_iso}),
            'contact': forms.TextInput(attrs={'placeholder': 'Enter phone number'}),
            'capacity': forms.NumberInput(attrs={'placeholder': 'Enter max participants'}),
            'coin': forms.NumberInput(attrs={'placeholder': 'Enter coin reward'}), 
            'event_category': forms.CheckboxSelectMultiple, 
            'event_status': forms.RadioSelect,
        }     

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        underline_style = (
            "block w-full px-1 py-2 bg-transparent border-0 border-b border-gray-300 "
            "placeholder-gray-400 focus:outline-none focus:ring-0 "
            "focus:border-blue-600 sm:text-sm"
        )
        boxed_style = (
            "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm "
            "placeholder-gray-400 focus:outline-none focus:ring-blue-500 "
            "focus:border-blue-500 sm:text-sm"
        )
        
        textarea_style = f"{underline_style} min-h-[80px]"
        underline_fields = [
            'name', 'contact', 'image', 'image2', 'image3'
        ]
        
        boxed_fields = [
            'location', 'capacity', 'coin', 'event_date', 'regist_deadline'
        ]
        for field_name in underline_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({'class': underline_style})
        
        for field_name in boxed_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({'class': boxed_style})

        if 'description' in self.fields:
            self.fields['description'].widget.attrs.update({'class': textarea_style})
            
    def clean_name(self):
        name = self.cleaned_data["name"]
        return strip_tags(name)

    def clean_description(self):
        description = self.cleaned_data["description"]
        return strip_tags(description)
    
    # def clean_event_date(self):
    #     event_date = self.cleaned_data.get('event_date')
    #     now = timezone.now()
        
    #     if event_date and event_date < now:
    #         raise ValidationError(
    #             "Event date and time cannot be in the past!"
    #         )
        
    #     return event_date

    # def clean_regist_deadline(self):
    #     regist_deadline = self.cleaned_data.get('regist_deadline')
    #     now = timezone.now()
        
    #     if regist_deadline and regist_deadline < now:
    #         raise ValidationError(
    #             "Registration deadline cannot be in the past!"
    #         )
    #     event_date = self.cleaned_data.get('event_date')
    #     if event_date and regist_deadline and regist_deadline >= event_date:
    #         raise ValidationError(
    #             "Registration deadline must be before the event date/time."
    #         )
    #     return regist_deadline
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.pk and not instance.event_status:
             instance.event_status = 'coming_soon' 
        if commit:
            instance.save()
        return instance