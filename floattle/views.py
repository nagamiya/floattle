from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView, LogoutView
)
from django.contrib.sites.shortcuts import get_current_site
from django.core.signing import BadSignature, SignatureExpired, loads, dumps
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.views import generic
from .forms import (
    LoginForm, UserCreateForm
)

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
            'protocol': self.request.scheme,
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
def index(request):
    return HttpResponse('Hello, This is top page.')

class Top(generic.TemplateView):
    template_name = 'floattle/top.html'

class Login(LoginView):
    form_class = LoginForm
    template_name = 'floattle/login.html'

class Logout(LogoutView):
    template_name = 'floattle/top.html'
