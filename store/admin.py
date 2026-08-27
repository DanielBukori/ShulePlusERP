from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# Register your models here.
admin.site.register(StoreStock)
admin.site.register(StockMovement)
admin.site.register(StudentContribution)
admin.site.register(ContributionRequirement)