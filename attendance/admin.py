from django.contrib import admin
from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "school_class", "date", "status", "recorded_by")
    list_filter = ("school", "school_class", "status", "date")
    search_fields = ("student__first_name", "student__last_name")
    date_hierarchy = "date"
