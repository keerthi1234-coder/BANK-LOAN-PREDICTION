from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from .forms import LoanApplicationForm, UserRegisterForm
from django.contrib.auth.forms import AuthenticationForm
from .models import PredictionResult, PredictionConfig, UserProfile, LoanApplicationFormData,LoanApplication
from .predictor import get_model
from django.contrib.auth.decorators import login_required
import pandas as pd
from django.contrib.auth import update_session_auth_hash
from .forms import UserUpdateForm, CustomPasswordChangeForm
from django.contrib import messages
from .forms import UserUpdateForm, UserProfileUpdateForm
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User


def home(request):
    return render(request, "predictions/home.html")

@login_required(login_url='login')
def predict_view(request):
    if request.method == 'POST':
        form = LoanApplicationForm(request.POST)
        if form.is_valid():
            app = form.save(commit=False)
            app.user = request.user   # user always logged in
            app.save()

            # Prepare features
            input_data = {
                'Gender': app.gender,
                'Married': app.married,
                'Dependents': app.dependents,
                'Education': app.education,
                'Self_Employed': app.self_employed,
                'ApplicantIncome': app.applicant_income,
                'CoapplicantIncome': app.coapplicant_income,
                'LoanAmount': app.loan_amount,
                'Loan_Amount_Term': app.loan_amount_term,
                'Credit_History': app.credit_history,
                'Property_Area': app.property_area
            }
            df = pd.DataFrame([input_data])

            # Get threshold from config
            config = PredictionConfig.objects.first()
            threshold = config.threshold if config else 0.65

            # Predict
            model = get_model()
            proba = model.predict_proba(df)[:, 1][0]
            predicted = bool(proba > threshold)

            # Save prediction
            pred = PredictionResult.objects.create(
                application=app,
                predicted_default=predicted,
                probability=proba
            )

            return render(request, 'predictions/result.html', {
                'prediction': pred,
                'application': app
            })
    else:
        form = LoanApplicationForm()

    return render(request, 'predictions/form.html', {'form': form})


@login_required(login_url='login')
def apply_loan_view(request):
    prediction_id = request.GET.get('prediction')
    prediction = get_object_or_404(PredictionResult, id=prediction_id, application__user=request.user)
    loan_app = prediction.application
    # Ensure prediction exists
    if not hasattr(loan_app, 'prediction'):
        messages.error(request, "Prediction not found for this application.")
        return redirect('prediction_history')

    prediction = loan_app.prediction  # PredictionResult instance

    # Prevent duplicate loan applications
    if LoanApplicationFormData.objects.filter(user=request.user, prediction=prediction).exists():
        return render(request, "predictions/apply_loan.html", {
            "already_applied": True,
            "prediction": prediction
        })

    if request.method == 'POST':
        loan_amount = request.POST.get('loan_amount')
        loan_tenure = request.POST.get('loan_tenure')
        loan_purpose = request.POST.get('loan_purpose')

        LoanApplicationFormData.objects.create(
            user=request.user,
            prediction=prediction,
            loan_amount=loan_amount,
            loan_tenure=loan_tenure,
            loan_purpose=loan_purpose
        )

        return render(request, 'predictions/apply_loan.html', {
            'success': True,
            'loan_amount': loan_amount,
            'prediction': prediction
        })

    return render(request, 'predictions/apply_loan.html', {"prediction": prediction})




def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Save additional profile data
            mobile = form.cleaned_data['mobile_number']
            address = form.cleaned_data['address']
            UserProfile.objects.create(user=user, mobile_number=mobile, address=address)

            # Show success message
            messages.success(request, "🎉 Your account has been created successfully! Please log in.")

            # Redirect to login page
            return redirect('login')
        else:
            messages.error(request, "⚠️ Please correct the errors below and try again.")
    else:
        form = UserRegisterForm()

    return render(request, 'predictions/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")  # ✅ success message
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")  # ✅ error message
    else:
        form = AuthenticationForm()
    
    return render(request, 'predictions/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')




@login_required
def user_profile(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileUpdateForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect("user_profile")
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileUpdateForm(instance=profile)

    return render(request, "predictions/profile.html", {
        "user_form": user_form,
        "profile_form": profile_form,
    })



@login_required
def change_password(request):
    if request.method == "POST":
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, "Your password has been changed successfully.")
            return redirect("change_password")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomPasswordChangeForm(user=request.user)

    return render(request, "predictions/change_password.html", {"form": form})




@login_required
def prediction_history(request):
    predictions = LoanApplication.objects.filter(user=request.user)
    config = PredictionConfig.objects.first()
    threshold = config.threshold if config else 0.65

    # Annotate each prediction with dynamic status
    for p in predictions:
        if hasattr(p, 'prediction') and p.prediction is not None:
            p.predicted_status = "Defaulter" if p.prediction.probability > threshold else "Non-defaulter"
        else:
            p.predicted_status = "No Prediction"

    return render(request, "predictions/prediction_history.html", {"predictions": predictions})


@login_required
def loan_history(request):
    loans = LoanApplicationFormData.objects.filter(user=request.user)
    return render(request, "predictions/loan_history.html", {"loans": loans})



def user_reset_password(request):
    if request.method == "POST":
        email = request.POST.get('email')
        new_password = request.POST.get('newpassword')
        confirm_password = request.POST.get('confirmpassword')

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('user_reset_password')

        try:
            user = User.objects.get(email=email, is_staff=False)  # only normal users
            user.password = make_password(new_password)
            user.save()
            messages.success(request, "Password changed successfully.")
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, "Invalid email.")
    
    return render(request, "predictions/user_reset_password.html")