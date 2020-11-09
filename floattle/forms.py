from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm, UserCreationForm,
    PasswordChangeForm, PasswordResetForm, SetPasswordForm
)
from django.contrib.auth import get_user_model
from .models import Post
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

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('name',)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class EmailChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data['email']
        User.objects.filter(email=email, is_active=False).delete()
        return email

class MyPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-controll'

class MyPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-controll'

class MySetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-controll'


class PostForm(forms.ModelForm):
    CHOICES = (
        ("0", "ボロボロの紙"),
        ("1", "ふつうのメモ用紙"),
        ("2", "上質な紙")
    )
    
    text = forms.CharField(
        label='メッセージ',
        max_length=200,
        widget=forms.Textarea
    )
    shed_count = forms.ChoiceField(
        label='用紙の種類',
        choices=CHOICES,
        widget=forms.Select
    )

    class Meta:
        model = Post
        fields = ('text', 'shed_count')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

