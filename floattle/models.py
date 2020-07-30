from django.db import models
from django.core.mail import send_mail
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.auth.base_user import AbstractBaseUser
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.auth.validators import UnicodeUsernameValidator


'''
・User
認証はメールアドレスのカスタムユーザクラス。
一応nameもあるけど表示用にしか使わない。


・Post
投稿内容。ユーザ１人に対して多数持つ。
キープフィールド（いいね機能的なのに使う）を持っており、ユーザとポストは多対多

'''
class CustomUserManager(UserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


"""カスタムユーザーモデル."""
class User(AbstractBaseUser, PermissionsMixin):

    name_validator = UnicodeUsernameValidator()
    name = models.CharField(
        _('name'),
        max_length=30,
        help_text=
        _('Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.'
          ),
        validators=[name_validator]
    )

    email = models.EmailField(_('email address'), unique=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_(
            'Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    last_login = models.DateTimeField(_('last login'), default=timezone.now)

    objects = CustomUserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')


    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    @property
    def username(self):
        """ username属性getter """
        return self.email

class Post(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    text = models.TextField(max_length=400)
    shed_count = models.IntegerField()
    keep = models.ManyToManyField(User, related_name='keep', blank=True)
    is_active = models.BooleanField(default=True)
    date_published = models.DateTimeField(blank=True, null=True)
    date_deleted = models.DateTimeField(blank=True, null=True)

    ''' 文字数によって紙のデザインが変わるようにそのうちしたいので定義しておいた '''
    def length(self):
        return len(self.text)