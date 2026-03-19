from django.db import models
from django.contrib.auth.models import User

class LoanApplication(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    gender = models.CharField(max_length=20)
    married = models.CharField(max_length=10)
    dependents = models.CharField(max_length=10)
    education = models.CharField(max_length=20)
    self_employed = models.CharField(max_length=10)
    applicant_income = models.FloatField()
    coapplicant_income = models.FloatField()
    loan_amount = models.FloatField()
    loan_amount_term = models.FloatField(null=True, blank=True)
    credit_history = models.IntegerField(null=True, blank=True)
    property_area = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

class PredictionResult(models.Model):
    application = models.OneToOneField(LoanApplication, on_delete=models.CASCADE, related_name='prediction')
    predicted_default = models.BooleanField()
    probability = models.FloatField()
    model_version = models.CharField(max_length=20, default='v1')
    created_at = models.DateTimeField(auto_now_add=True)

class LoanApplicationFormData(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    prediction = models.ForeignKey('PredictionResult', on_delete=models.SET_NULL, null=True, blank=True)
    loan_amount = models.FloatField()
    loan_tenure = models.IntegerField(help_text="Tenure in months")
    loan_purpose = models.CharField(max_length=200)
    applied_at = models.DateTimeField(auto_now_add=True)

    # Admin fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    remark = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user} - ₹{self.loan_amount} - {self.status}"

class PredictionConfig(models.Model):
    threshold = models.FloatField(default=0.65, help_text="Probability above which applicant is classified as defaulter")

    def __str__(self):
        return f"Prediction Threshold: {self.threshold}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile_number = models.CharField(max_length=15)
    address = models.TextField()

    def __str__(self):
      return f"{self.user.username} - Application {self.id}"