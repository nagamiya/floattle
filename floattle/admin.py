from django.contrib import admin
from .models import User, Post

# Register your models here.

# Authority: make user
admin.site.register(User)
# Authority: make post, Edit post...
admin.site.register(Post)