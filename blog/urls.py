from django.conf import settings
"""
URL configuration for blog project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from pov import views 
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views #password change

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'), #Home Page
    path('category/', include('pov.urls')), #Category Filter 
    path('blogs/search/', views.search, name='search'), #Search
    path('blogs/<slug:slug>/', views.blogs, name='blogs'), #Blogs Url
    path('register/', views.register, name='register'), #Register
    path('login/', views.login, name='login'), #Login
    path('logout/', views.logout, name='logout'), #Logout
    path('dashboard/', views.dashboard, name='dashboard'), #Dashboard
    path('category/create/', views.create_category, name='create_category'), #Create Category
    path('category/delete/<int:id>/', views.delete_category, name='delete_category'), #Delete Category
    path('category/edit/<int:id>/', views.edit_category, name='edit_category'), #Edit Category
    path('blog/create/', views.create_blog, name='create_blog'), #Create Blog
    path('blog/edit/<int:id>/', views.edit_blog, name='edit_blog'), #Edit Blog
    path('blog/delete/<int:id>/', views.delete_blog, name='delete_blog'), #Delete Blog
    path('members/create/', views.create_staff, name='create_staff'), #Create Staff
    path('members/edit/<int:id>/', views.edit_staff, name='edit_staff'), #Edit Staff
    path('members/delete/<int:id>/', views.delete_staff, name='delete_staff'), #Delete Staff
    path('my-account/', views.account_redirect, name='account_redirect'), #Redirect to Profile
    path('profile/', views.user_profile, name='user_profile'), #Profile
    path('profile/update-security/', views.update_profile_password, name='update_profile_password'), #Update Profile Password
    path('comment/edit/<int:id>/', views.edit_comment, name='edit_comment'), #Edit Comment
    path('comment/delete/<int:id>/', views.delete_comment, name='delete_comment'), #Delete Comment
    path('comment/like/<int:id>/', views.like_comment, name='like_comment'), #Like Comment
    path('blog/react/<int:blog_id>/<str:reaction_type>/', views.react_to_blog, name='react_to_blog'), #Reaction
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'), #Mark all notifications as read
    path('notification/read/<int:pk>/', views.notification_redirect, name='notification_redirect'), #Notification Redirect
    path('subscribe/', views.subscribe, name='subscribe'), #Subscribe to Newsletter
    path('subscriber/delete/<int:id>/', views.delete_subscriber, name='delete_subscriber'), #Delete Subscriber (Registered User)
    path('', include('pwa.urls')), #PWA
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)+static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


