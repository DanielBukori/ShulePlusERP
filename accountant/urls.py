from django.urls import path
from . import views

app_name = 'accountant'

urlpatterns = [
    path('dashboard/', views.accountant_dashboard_view, name='accountant_dashboard'),
    path('fee-structure/', views.set_fee_structure_view, name='set_fee_structure'),
    path('other-charges/', views.add_other_charge_view, name='add_other_charge'),
    path('assessments/generate/', views.generate_assessments_view, name='generate_assessments'),
    path('payments/record/', views.record_payment_view, name='record_payment'),
    path('payments/<int:payment_id>/receipt/', views.view_receipt_view, name='view_receipt'),
]
