from django.urls import path
from . import views

app_name = 'floattle'

urlpatterns = [
    # 正規表現でname=topの２つをまとめたいけどうまくいかない
    path('', views.Top.as_view(), name='top'),
    path('top/', views.Top.as_view(), name='top'),
    path('messages_show/', views.MessagesShow.as_view(), name='messages_show'),
    path('keeps_show/', views.KeepsShow.as_view(), name='keeps_show'),
    path('detail/<int:pk>/', views.Detail.as_view(), name='detail'),
    
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.Logout.as_view(), name='logout'),
    
    path('user_create/', views.UserCreate.as_view(), name='user_create'),
    path('user_create/done', views.UserCreateDone.as_view(), name='user_create_done'),
    path('user_create/complete/<token>', views.UserCreateComplete.as_view(), name='user_create_complete'),
    #path('user_show/<int:pk>/', views.UserShow.as_view(), name='user_show'),
    path('user_update/<int:pk>/', views.UserUpdate.as_view(), name='user_update'),
    path('user_delete/<int:pk>/', views.UserDelete.as_view(), name='user_delete'),
    path('user_delete_comlete/', views.UserDeleteComplete.as_view(), name='user_delete_complete'),

    #path('email/change/', views.EmailChange.as_view(), name='email_change'),
    path('email/change/done/', views.EmailChangeDone.as_view(), name='email_change_done'),
    path('email/change/complete/<str:token>/', views.EmailChangeComplete.as_view(), name='email_change_complete'),

    path('password_change/', views.PasswordChange.as_view(), name='password_change'),
    path('password_change/done/', views.PasswordChangeDone.as_view(), name='password_change_done'),
    path('password_reset/', views.PasswordReset.as_view(), name='password_reset'),
    path('password_reset/done/', views.PasswordResetDone.as_view(), name='password_reset_done'),
    path('password_reset/confirm/<uidb64>/<token>/', views.PasswordResetConfirm.as_view(), name='password_reset_confirm'),
    path('password_reset/complete/', views.PasswordResetComplete.as_view(), name='password_reset_complete')

]
