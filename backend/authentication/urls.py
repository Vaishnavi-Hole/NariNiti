from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='auth-register'),
    path('login/', views.LoginView.as_view(), name='auth-login'),
    path('logout/', views.LogoutView.as_view(), name='auth-logout'),
    path('refresh/', views.TokenRefreshView.as_view(), name='auth-refresh'),
    path('me/', views.CurrentUserView.as_view(), name='auth-me'),
]
