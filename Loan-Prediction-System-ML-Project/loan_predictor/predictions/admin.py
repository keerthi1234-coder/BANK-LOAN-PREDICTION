from django.contrib import admin
from .models import LoanApplication, PredictionResult, LoanApplicationFormData, PredictionConfig

# Admin for LoanApplication
@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'applicant_income', 'coapplicant_income', 'loan_amount', 'loan_amount_term', 'credit_history', 'property_area', 'created_at')
    list_filter = ('property_area', 'credit_history', 'created_at')
    search_fields = ('user__username',)

# Admin for PredictionResult
@admin.register(PredictionResult)
class PredictionResultAdmin(admin.ModelAdmin):
    list_display = ('application', 'predicted_default', 'probability', 'model_version', 'created_at')
    list_filter = ('predicted_default', 'model_version', 'created_at')
    search_fields = ('application__user__username',)

# Admin for LoanApplicationFormData
@admin.register(LoanApplicationFormData)
class LoanApplicationFormDataAdmin(admin.ModelAdmin):
    list_display = ('user', 'loan_amount', 'loan_tenure', 'status', 'remark', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('user__username', 'loan_purpose')




@admin.register(PredictionConfig)
class PredictionConfigAdmin(admin.ModelAdmin):
    list_display = ('threshold',)

