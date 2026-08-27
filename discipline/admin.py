from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# Register your models here.
admin.site.register(OffenseType)
admin.site.register(DisciplineIncident)
admin.site.register(DisciplineAlert)
