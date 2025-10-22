from apps.main.models import User
from django.contrib.auth.forms import UserCreationForm

class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = User
        
        fields = UserCreationForm.Meta.fields + ('email', 'base_location', 'poin')

    