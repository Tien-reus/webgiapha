from django.urls import path

from . import views


urlpatterns = [
    path('', views.about, name='about'),
    path('family-tree/', views.family_tree, name='family_tree'),
    path('manage/', views.manage_members, name='manage_members'),
    path('login/', views.AdminLoginView.as_view(), name='login'),
    path('logout/', views.admin_logout, name='logout'),
]
