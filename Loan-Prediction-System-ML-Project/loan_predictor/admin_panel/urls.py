# admin_panel/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('admin/login/', views.admin_login_view, name='admin_login'),
    path('admin/logout/', views.admin_logout_view, name='admin_logout'),
    path('dashboard/', views.dashboard_view, name='admin_dashboard'),
    path('loan-applications/', views.loan_applications_view, name='admin_loan_list'),
    path('loan-application/<int:id>/', views.loan_detail_view, name='admin_loan_detail'),
    path('admin/users/', views.user_list_view, name='user_list'),
    path('admin/users/<int:user_id>/profile/', views.admin_user_profile, name='admin_user_profile'),
    path('admin/users/<int:user_id>/loans/', views.admin_user_loans, name='admin_user_loans'),
    path('admin/users/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
    path('admin/profile/', views.admin_profile_view, name='admin_profile'),
    path('admin/change-password/', views.admin_change_password_view, name='admin_change_password'),
    path('admin/predictions/', views.admin_predictions_view, name='admin_predictions'),
    path('admin/predictions/delete/<int:app_id>/', views.delete_prediction, name='delete_prediction'),
    path('admin/users/<int:user_id>/predictions/', views.admin_user_predictions, name='admin_user_predictions'),
    path('admin/search-users/', views.search_users_view, name='search_users'),
    path('admin/bd_users_reports/', views.bd_users_reports, name='bd_users_reports'),
    path("reset-password", views.admin_reset_password, name="admin_reset_password"),
]
