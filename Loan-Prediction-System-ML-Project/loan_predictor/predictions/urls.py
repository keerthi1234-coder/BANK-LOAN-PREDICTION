from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"), 
    path('predict/', views.predict_view, name='predict'),
    path('apply-loan/', views.apply_loan_view, name='apply_loan'),
    path('register/', views.register_view, name='register'),
    path('login', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('predict/', views.predict_view, name='predict'),
    path('profile/', views.user_profile, name='user_profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('prediction-history/', views.prediction_history, name='prediction_history'),
    path('loan-history/', views.loan_history, name='loan_history'),
   path("user-reset-password", views.user_reset_password, name="user_reset_password"),

]