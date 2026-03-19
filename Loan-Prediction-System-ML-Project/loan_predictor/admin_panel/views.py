from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from predictions.models import LoanApplicationFormData, UserProfile, LoanApplication, PredictionConfig
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from django.contrib.auth.hashers import make_password
from django.db.models import Q

def admin_required(view_func):
    return user_passes_test(lambda u: u.is_staff, login_url='login')(view_func)


def admin_required(user):
    return user.is_authenticated and user.is_staff

def admin_login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid credentials or you are not an admin!")

    return render(request, 'login.html')

def admin_logout_view(request):
    logout(request)
    return redirect('admin_login')

@user_passes_test(admin_required, login_url='admin_login')
def dashboard_view(request):
    total_loans = LoanApplicationFormData.objects.count()
    pending = LoanApplicationFormData.objects.filter(status='Pending').count()
    approved = LoanApplicationFormData.objects.filter(status='Approved').count()
    rejected = LoanApplicationFormData.objects.filter(status='Rejected').count()
    context = {
        'total_loans': total_loans,
        'pending': pending,
        'approved': approved,
        'rejected': rejected
    }
    return render(request, 'dashboard.html', context)



@user_passes_test(admin_required, login_url='admin_login')
def loan_applications_view(request):
    status = request.GET.get('status')
    if status:
        loans = LoanApplicationFormData.objects.filter(status=status)
    else:
        loans = LoanApplicationFormData.objects.all()
    return render(request, 'loan_list.html', {'loans': loans})

@user_passes_test(admin_required, login_url='admin_login')
def loan_detail_view(request, id):
    loan = get_object_or_404(LoanApplicationFormData, id=id)

    if request.method == 'POST':
        loan.status = request.POST.get('status')
        loan.remark = request.POST.get('remark')
        loan.save()
        return redirect('admin_loan_list')

    return render(request, 'loan_detail.html', {'loan': loan})

@user_passes_test(admin_required, login_url='admin_login')
def user_list_view(request):
    users = User.objects.filter(is_staff=False).order_by('-date_joined')  # Only non-staff users
    return render(request, 'user_list.html', {'users': users})


@user_passes_test(admin_required, login_url='admin_login')
def admin_user_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(UserProfile, user=user)
    return render(request, 'user_profile.html', {'user': user, 'profile': profile})

@user_passes_test(admin_required, login_url='admin_login')
def admin_user_loans(request, user_id):
    user = get_object_or_404(User, id=user_id)
    loans = LoanApplicationFormData.objects.filter(user=user)
    return render(request, 'user_loans.html', {'user': user, 'loans': loans})

@user_passes_test(admin_required, login_url='admin_login')
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    return redirect('user_list')


# Form to update only name and email
class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

@user_passes_test(admin_required, login_url='admin_login')
def admin_profile_view(request):
    user = request.user
    if request.method == 'POST':
        form = AdminProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('admin_profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminProfileForm(instance=user)

    return render(request, 'admin_profile.html', {
        'form': form,
        'user': user
    })


@user_passes_test(admin_required, login_url='admin_login')
def admin_change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important! Keeps user logged in
            messages.success(request, 'Password changed successfully!')
            return redirect('admin_change_password')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(user=request.user)
    
    return render(request, 'admin_change_password.html', {'form': form})

@user_passes_test(admin_required, login_url='admin_login')
def admin_predictions_view(request):
    applications = LoanApplication.objects.select_related('prediction').all()
    return render(request, 'admin_predictions.html', {'applications': applications})

@user_passes_test(admin_required, login_url='admin_login')
def delete_prediction(request, app_id):
    application = get_object_or_404(LoanApplication, id=app_id)

    if hasattr(application, 'prediction'):
        application.delete()
        messages.success(request, "Prediction deleted successfully!")
    else:
        messages.warning(request, "No prediction found for this application.")

    return redirect('admin_predictions')

@user_passes_test(admin_required, login_url='admin_login')
def admin_user_predictions(request, user_id):
    user = get_object_or_404(User, id=user_id)
    predictions = LoanApplication.objects.filter(user=user).select_related('prediction').order_by('-created_at')

    # Get threshold
    config = PredictionConfig.objects.first()
    threshold = config.threshold if config else 0.65

    # Pagination
    paginator = Paginator(predictions, 5)  # Show 5 predictions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Build list for page only
    prediction_data = []
    for app in page_obj:
        loans = LoanApplicationFormData.objects.filter(user=user, prediction=app.prediction)
        prediction_data.append({
            'application': app,
            'loans': loans
        })

    return render(request, 'admin_user_predictions.html', {
        'user': user,
        'prediction_data': prediction_data,
        'threshold': threshold,
        'page_obj': page_obj
    })

@user_passes_test(admin_required, login_url='admin_login')
def search_users_view(request):
    query = request.GET.get('q', '')  # Get search query
    users = User.objects.filter(is_staff=False)  # Only non-staff users

    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )

    return render(request, 'search_users.html', {'users': users, 'query': query})


@user_passes_test(admin_required, login_url='admin_login')
def bd_users_reports(request):
    fdate = request.GET.get('fdate')
    tdate = request.GET.get('tdate')
    users = User.objects.filter(is_staff=False)  # only non-staff

    # Apply date filter if both dates are provided
    if fdate and tdate:
        fdate_parsed = parse_date(fdate)
        tdate_parsed = parse_date(tdate)

        if fdate_parsed and tdate_parsed:
            users = users.filter(date_joined__date__range=[fdate_parsed, tdate_parsed])

    return render(request, 'users_reports.html', {
        'users': users,
        'fdate': fdate,
        'tdate': tdate
    })


def admin_reset_password(request):
    if request.method == "POST":
        email = request.POST.get('email')
        new_password = request.POST.get('newpassword')
        confirm_password = request.POST.get('confirmpassword')

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('admin_reset_password')

        try:
            user = User.objects.get(email=email, is_staff=True)  # only staff/admin
            user.password = make_password(new_password)
            user.save()
            messages.success(request, "Password changed successfully.")
            return redirect('admin_login')
        except User.DoesNotExist:
            messages.error(request, "Invalid email or not an admin.")
    
    return render(request, "reset_password.html")