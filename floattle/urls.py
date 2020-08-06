from django.urls import path
from . import views

app_name = 'floattle'

urlpatterns = [
    # 正規表現でname=topの２つをまとめたいけどうまくいかない
    path('', views.Top.as_view(), name='top'),
    path('top/', views.Top.as_view(), name='top'),
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.Logout.as_view(), name='logout'),
]
