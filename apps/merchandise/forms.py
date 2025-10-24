from django import forms
from django.forms import ModelForm
from apps.merchandise.models import Merchandise
from django.utils.html import strip_tags
# test
class MerchandiseForm(ModelForm):
    class Meta:
        model = Merchandise
        fields = ["image_url", 'name', 'description', 'category', 'price_coins', 'description', 'stock']
        
    def clean_price(self):
        price = self.cleaned_data.get('price_coins')
        if price <= 0:
            raise forms.ValidationError("Price cannot be negative or zero")
        return price
    
    def clean_name(self):
        name = self.cleaned_data["name"]
        return strip_tags(name)

    def clean_description(self):
        description = self.cleaned_data["description"]
        return strip_tags(description)
