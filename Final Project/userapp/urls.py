from django.contrib import admin
from django.urls import path,include
from userapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name ='home'),
    path('log_in',views.log_in, name ='log_in'),
    path('signup',views.signup, name='signup'),
    path('feedback',views.feedback,name='feedback'),
    path('stocks',views.stocks,name='stocks'),
    path('market',views.market,name='market'),
    path('profile',views.profile,name='profile'),
    path('editProfile',views.editProfile,name='editProfile'),
    path('log_out',views.log_out,name='log_out'),
    path('users',views.users,name="users"),
]
