from django.conf import settings
from django.contrib.auth import (
    get_user_model, logout as auth_logout
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import (
    LoginView, LogoutView,
    PasswordChangeView, PasswordChangeDoneView,
    PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
)
from django.contrib.sites.shortcuts import get_current_site
from django.core.signing import BadSignature, SignatureExpired, loads, dumps
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import (
    redirect, resolve_url, render, get_object_or_404
)
from django.template.loader import render_to_string
from django.views import generic
from django.urls import reverse_lazy
from django.core.mail import send_mail
from .forms import (
    LoginForm, UserCreateForm, UserUpdateForm, MyPasswordChangeForm,
    MyPasswordResetForm, MySetPasswordForm, PostForm, #EmailChangeForm
)
from . import forms
from .models import (
    Post
)
import random
from datetime import datetime
from django.core.mail import send_mail
import os


# カスタムユーザをインポート
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
        content = render_to_string('floattle/mail_template/create/message.txt', context)
        from_email = 'floattleDevelopper@gmail.com'
        to_email = user.email

        # ここからsendgrid
        #sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
        #mail = Mail(from_email, to_email, subject, content)
        #message = sendgrid.Mail()
        #response = sg.client.mail.send.post(request_body=mail.get())
        send_mail(
            subject,
            content,
            from_email,
            [to_email],
            fail_silently=False,
        )
        # ここまで
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


class Top(generic.TemplateView):

    # getにcontext渡すための準備
    def preparation(self):
        form_class = PostForm()
        post_list = Post.objects.all()
        if post_list.exists():
            post_count = len(post_list)
            post_id_list = [random.randint(0, post_count - 1) for i in range(1)]
            pickup_post_list = [post_list[i] for i in post_id_list]

            context = {
                'pickup_post_list': pickup_post_list,
                'form': form_class
            }
            return context

        context = {
            'form': form_class
        }
        return context

    def get(self, request, *args, **kwargs):
        context = self.preparation()
        # そのうちkeep数が上限に達していないpostの中からランダムなidのものだけを表示
        return render(request, 'floattle/top.html', context)
   
    def post(self, request, *args, **kwargs):
        context = self.preparation()
        form = forms.PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.date_published = datetime.now()
            form.save()
            return redirect('/top/')
        return render(request, 'floattle/top.html', context)


class MessagesShow(LoginRequiredMixin, generic.TemplateView):
    def get(self, request, *args, **kwargs):
        user = request.user
        post_list = Post.objects.all()
        userself_post_list = [p for p in post_list if p.user == user]
        context = {
            'userself_post_list': userself_post_list
        }
        return render(request, 'floattle/messages_show.html', context)


class KeepsShow(LoginRequiredMixin, generic.TemplateView):
    def get(self, request, *args, **kwargs):
        keep_user = request.user
        keep_list = Post.objects.filter(keep=keep_user)
        context = {
            'keep_list': keep_list
        }
        return render(request, 'floattle/keeps_show.html', context)

class Detail(generic.DetailView):
    model = Post
    template_name = 'floattle/detail.html'

    def get(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        keeped = False

        if post.keep.filter(id=request.user.id).exists():
            keeped = True

        context = {
            'post': post,
            'keeped': keeped
        }
        return render(request, 'floattle/detail.html', context)

    def post(self, request, pk):
        user = request.user
        post = get_object_or_404(Post, pk=pk)

        if post.keep.filter(id=request.user.id).exists():
            post.keep.remove(request.user)
            post.save()
            keeped = True
        else:
            post.keep.add(user)
            post.save()
            keeped = False
        return redirect('floattle:detail', post.pk)

class Login(LoginView):
    form_class = LoginForm
    template_name = 'floattle/login.html'

class Logout(LogoutView):
    template_name = 'floattle/top.html'

# UserPassesTestMixinを継承して、ログインユーザ本人のみアクセスできるように
class MyView(UserPassesTestMixin):
    raise_exception = True
    def test_func(self):
        user = self.request.user
        return user.pk == self.kwargs['pk'] or user.is_superuser


class UserUpdate(MyView, generic.UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'floattle/user_update.html'

    def get_success_url(self):
        return resolve_url('floattle:user_update', pk=self.kwargs['pk'])

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

        subject = render_to_string('floattle/mail_template/email_change/subject.txt', context)
        content = render_to_string('floattle/mail_template/email_change/message.txt', context)
        from_email = 'floattleDevelopper@gmail.com'
        to_email = new_email

        # ここからsendgrid
        #sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
        #mail = Mail(from_email, to_email, subject, content)
        #message = sendgrid.Mail()
        #response = sg.client.mail.send.post(request_body=mail.get())

        send_mail(
            subject,
            content,
            from_email,
            [to_email],
            fail_silently=False,
        )
        # ここまで

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

class UserDelete(generic.TemplateView):
    template_name = 'floattle/user_delete.html'
    success_url = reverse_lazy('floattle:user_delete_complete')
    model = User

    def post(self, request, *args, **kwargs):
        user = User.objects.get(email=self.request.user.email)
        user.is_active = False
        user.save()
        auth_logout(self.request)
        return render(self.request, 'floattle/user_delete_complete.html')

class UserDeleteComplete(LoginRequiredMixin, generic.View):
    template_name = 'floattle/user_delete_complete.html'
