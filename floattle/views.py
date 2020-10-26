from django.conf import settings
from django.contrib.auth import (
    get_user_model, logout as auth_logout
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView,
    PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
)
from django.contrib.sites.shortcuts import get_current_site
from django.core.signing import BadSignature, SignatureExpired, loads, dumps
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import (
    redirect, resolve_url, render
)
from django.template.loader import render_to_string
from django.views import generic
from django.urls import reverse_lazy
from django.core.mail import send_mail
from .forms import (
    LoginForm, UserCreateForm, UserUpdateForm, MyPasswordChangeForm,
    MyPasswordResetForm, MySetPasswordForm, EmailChangeForm
)
from .models import (
    Post
)
import logging
import random

logger = logging.getLogger(__name__)

# カスタムしたユーザをインポート
User = get_user_model()

# Create User
class UserCreate(generic.CreateView):
    # 仮登録
    template_name = 'floattle/user_create.html'
    form_class = UserCreateForm

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        # is_Active = TrueにするURLをメールで送信する準備
        # dumpで推測しづらい文字列を生成、loadsで復号可能
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol': 'https' if self.request.is_secure() else 'http',
            'domain': domain,
            'token': dumps(user.pk),
            'user': user,
        }

        subject = render_to_string('floattle/mail_template/create/subject.txt', context)
        message = render_to_string('floattle/mail_template/create/message.txt', context)

        user.email_user(subject, message)
        return redirect('floattle:user_create_done')

# 仮登録したら
class UserCreateDone(generic.TemplateView):
    template_name = 'floattle/user_create_done.html'

# メールのURLにアクセスしてもらって本登録する（is_Active = Trueにする）
class UserCreateComplete(generic.TemplateView):
    template_name = 'floattle/user_create_complete.html'
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60 * 60 * 24)
    
    def get(self, request, **kwargs):
        token = kwargs.get('token')
        # 復号した結果によって処理が変わる
        try:
            user_pk = loads(token, max_age=self.timeout_seconds)
        
        # tokenの期限切れ
        except SignatureExpired:
            return HttpResponseBadRequest()
        # token間違え
        except BadSignature:
            return HttpResponseBadRequest()

        # token問題なし
        else:
            try:
                user = User.objects.get(pk=user_pk)
            except User.DoesNotExist:
                return HttpResponseBadRequest()
            else:
                # 何も問題がなければ本登録して保存
                if not user.is_active:
                    user.is_active = True
                    user.save()
                    return super().get(request, **kwargs)

        return HttpResponseBadRequest()

        
# Create your views here.

class Top(generic.TemplateView):
    def get(self, *args, **kwargs):
        # そのうちkeep数が上限に達していないpostの中からランダムなidのものだけを表示
        post_list = Post.objects.all()
        post_count = len(post_list)
        post_id_list = [random.randint(0, post_count - 1) for i in range(3)]

        pickup_post_list = [post_list[i] for i in post_id_list]

        context = {
            'pickup_post_list': pickup_post_list,
        }
        return render(self.request, 'floattle/top.html', context)
   
  

class Login(LoginView):
    form_class = LoginForm
    template_name = 'floattle/login.html'

class Logout(LogoutView):
    template_name = 'floattle/top.html'

class MyView(UserPassesTestMixin):
    raise_exception = True
    def test_func(self):
        user = self.request.user
        return user.pk == self.kwargs['pk'] or user.is_superuser

class UserShow(MyView, generic.DetailView):
    model = User
    template_name = 'floattle/user_show.html'

class UserUpdate(MyView, generic.UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'floattle/user_form.html'

    def get_success_url(self):
        return resolve_url('floattle:user_show', pk=self.kwargs['pk'])


class EmailChange(LoginRequiredMixin, generic.FormView):
    template_name = 'floattle/email_change_form.html'
    form_class = EmailChangeForm

    def form_valid(self, form):
        user = self.request.user
        new_email = form.cleaned_data['email']

        # URLの送付
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol': 'https' if self.request.is_secure() else 'http',
            'domain': domain,
            'token': dumps(new_email),
            'user': user,
        }

        subject = render_to_string(
            'floattle/mail_template/email_change/subject.txt', context)
        message = render_to_string(
            'floattle/mail_template/email_change/message.txt', context)
        send_mail(subject, message, None, [new_email])

        return redirect('floattle:email_change_done')


class EmailChangeDone(LoginRequiredMixin, generic.TemplateView):
    template_name = 'floattle/email_change_done.html'

class EmailChangeComplete(LoginRequiredMixin, generic.TemplateView):
    template_name = 'floattle/email_change_complete.html'
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)
    
    def get(self, request, **kwargs):
        token = kwargs.get('token')
        try:
            new_email = loads(token, max_age=self.timeout_seconds)
        
        # 期限切れ
        except SignatureExpired:
            return HttpResponseBadRequest()
        
        # token間違え
        except BadSignature:
            return HttpResponseBadRequest()

        # token問題なし
        else:
            User.objects.filter(email=new_email, is_active=False).delete()
            request.user.email = new_email
            request.user.save()
            return super().get(request, **kwargs)

class PasswordChange(PasswordChangeView):
    form_class = MyPasswordChangeForm
    success_url = reverse_lazy('floattle:password_change_done')
    template_name = 'floattle/password_change.html'

class PasswordChangeDone(PasswordChangeDoneView):
    template_name = 'floattle/password_change_done.html'

class PasswordReset(PasswordResetView):
    subject_template_name = 'floattle/mail_template/password_reset/subject.txt'
    email_template_name = 'floattle/mail_template/password_reset/message.txt'
    template_name = 'floattle/password_reset_form.html'
    form_class = MyPasswordResetForm
    success_url = reverse_lazy('floattle:password_reset_done')

class PasswordResetDone(PasswordResetDoneView):
    template_name = 'floattle/password_reset_done.html'

class PasswordResetConfirm(PasswordResetConfirmView):
    form_class = MySetPasswordForm
    success_url = reverse_lazy('floattle:password_reset_complete')
    template_name = 'floattle/password_reset_confirm.html'

class PasswordResetComplete(PasswordResetCompleteView):
    template_name = 'floattle/password_reset_complete.html'

class UserDestroy(LoginRequiredMixin, generic.View):
   
    def get(self, *args, **kwargs):
        user = User.objects.get(email=self.request.user.email)
        user.is_active = False
        user.save()
        auth_logout(self.request)
        return render(self.request, 'floattle/user_destroy_complete.html')
