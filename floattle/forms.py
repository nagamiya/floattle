from django.contrib.auth.forms import (
    AuthenticationForm, UserCreationForm
)
from django.contrib.auth import get_user_model

User = get_user_model()

class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label

class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email',)
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
    
    # 本登録を忘れたり、メールアドレスの入力間違いで登録済みになってしまったデータを戻す
    def clean_email(self):
        email = self.cleaned_data['email']
        User.objects.filter(email=email, is_active=False).delete()
        return email
