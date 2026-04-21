from django.urls import path

from . import views


urlpatterns = [
    path('', views.about, name='about'),
    path('articles/<int:pk>/', views.article_detail, name='article_detail'),
    path('family-tree/', views.family_tree, name='family_tree'),
    path('branches-outline/', views.branches_outline, name='branches_outline'),
    path('manage/', views.manage_members, name='manage_members'),
    path('manage/articles/', views.manage_articles, name='manage_articles'),
    path('login/', views.AdminLoginView.as_view(), name='login'),
    path('logout/', views.admin_logout, name='logout'),
]
