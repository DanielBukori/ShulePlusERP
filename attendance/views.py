import calendar
from datetime import date as date_cls

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from shule_core.models import SchoolClass, Student, ConductReport
from .models import Attendance
from .forms import ConductReportForm

STATUS_LETTERS = {
    Attendance.PRESENT: "P",
    Attendance.ABSENT: "A",
    Attendance.LATE: "L",
    Attendance.EXCUSED: "E",
}

MONTHS_SW = [
    "", "Januari", "Februari", "Machi", "Aprili", "Mei", "Juni",
    "Julai", "Agosti", "Septemba", "Oktoba", "Novemba", "Desemba",
]


def _get_class_teacher_classes(user):
    """
    Rudisha queryset ya SchoolClass ambazo user aliyeingia (kama Class Teacher)
    ndiye class_teacher wake. class_teacher ni FK kwa CustomUser moja kwa moja.
    """
    if user.role != "TEACHER":
        return SchoolClass.objects.none()

    return SchoolClass.objects.filter(class_teacher=user).select_related("school")


@login_required
def my_classes_view(request):
    """
    Ukurasa wa kwanza wa mwalimu: orodha ya madarasa anayosimamia kama Class Teacher.
    """
    classes = _get_class_teacher_classes(request.user)

    if not classes.exists():
        messages.warning(
            request,
            "Huna darasa lolote ulilopangiwa kama Mwalimu wa Darasa."
        )

    return render(request, "attendance/my_classes.html", {
        "classes": classes,
    })


@login_required
def mark_attendance_view(request, class_id):
    """
    Register kamili ya mahudhurio ya mwezi mmoja kwa darasa: wanafunzi wote
    (safu) dhidi ya siku zote za shule za mwezi husika (Jumatatu-Ijumaa, columns).
    Mwalimu wa Darasa wa darasa hili hasa ndiye pekee mwenye ruhusa.
    """
    school_class = get_object_or_404(SchoolClass, pk=class_id)

    # --- Permission: lazima awe Class Teacher wa DARASA HILI hasa ---
    if (
        request.user.role != "TEACHER"
        or school_class.class_teacher_id != request.user.id
    ):
        messages.error(
            request,
            "Huna ruhusa ya kuandika mahudhurio ya darasa hili. "
            "Ni Mwalimu wa Darasa pekee ndiye mwenye ruhusa hii."
        )
        return redirect("attendance:my_classes")

    today = date_cls.today()

    # --- Mwezi/Mwaka uliochaguliwa (default: mwezi wa sasa) ---
    try:
        year = int(request.POST.get("year") or request.GET.get("year") or today.year)
        month = int(request.POST.get("month") or request.GET.get("month") or today.month)
    except (TypeError, ValueError):
        year, month = today.year, today.month

    # Zuia miezi isiyo sahihi
    if month < 1:
        month, year = 12, year - 1
    elif month > 12:
        month, year = 1, year + 1

    last_day_num = calendar.monthrange(year, month)[1]
    all_days = [date_cls(year, month, d) for d in range(1, last_day_num + 1)]
    # Siku za shule pekee: Jumatatu(0) hadi Ijumaa(4)
    school_days = [d for d in all_days if d.weekday() < 5]

    students = Student.objects.filter(
        school_class=school_class
    ).order_by("first_name", "last_name")

    # --- POST: hifadhi mabadiliko ya mwezi mzima ---
    if request.method == "POST":
        saved = 0
        for student in students:
            for day in school_days:
                if day > today:
                    continue  # huwezi kumark siku isiyofika bado
                field_name = f"cell_{student.id}_{day.day}"
                val = request.POST.get(field_name, "")
                if val in STATUS_LETTERS:
                    Attendance.objects.update_or_create(
                        student=student,
                        date=day,
                        defaults={
                            "school": school_class.school,
                            "school_class": school_class,
                            "status": val,
                            "recorded_by": request.user,
                        },
                    )
                    saved += 1
                elif val == "":
                    Attendance.objects.filter(student=student, date=day).delete()

        messages.success(
            request,
            f"Mahudhurio ya {school_class} - {MONTHS_SW[month]} {year} yamehifadhiwa."
        )
        return redirect(
            f"{request.path}?year={year}&month={month}"
        )

    # --- GET: pakia rekodi zilizopo za mwezi huu ---
    existing = {
        (a.student_id, a.date.day): a.status
        for a in Attendance.objects.filter(
            school_class=school_class, date__year=year, date__month=month
        )
    }

    student_rows = []
    for s in students:
        present_count = 0
        absent_count = 0
        cells = []
        for day in school_days:
            status = existing.get((s.id, day.day), "")
            if status == Attendance.PRESENT:
                present_count += 1
            elif status == Attendance.ABSENT:
                absent_count += 1
            cells.append({
                "day": day.day,
                "status": status,
                "letter": STATUS_LETTERS.get(status, ""),
                "is_future": day > today,
            })
        student_rows.append({
            "student": s,
            "cells": cells,
            "present_count": present_count,
            "absent_count": absent_count,
        })

    # Prev/next month
    prev_month, prev_year = (12, year - 1) if month == 1 else (month - 1, year)
    next_month, next_year = (1, year + 1) if month == 12 else (month + 1, year)

    return render(request, "attendance/mark_attendance.html", {
        "school_class": school_class,
        "year": year,
        "month": month,
        "month_name": MONTHS_SW[month],
        "school_days": school_days,
        "student_rows": student_rows,
        "prev_month": prev_month,
        "prev_year": prev_year,
        "next_month": next_month,
        "next_year": next_year,
        "today": today,
        "status_choices": Attendance.STATUS_CHOICES,
    })


# ============================================================
# TABIA/MWENENDO (ConductReport) - Class Teacher pekee, kwa
# darasa lake mwenyewe, kama sehemu ya 'PUPILS CONDUCT' ya
# ripoti halisi. Kila field ni hiari.
# ============================================================

@login_required
def conduct_list_view(request, class_id):
    """Class Teacher anaona wanafunzi wa darasa lake, achague term/mwaka, na aone
    nani tayari amejazwa tabia na nani bado."""
    school_class = get_object_or_404(SchoolClass, pk=class_id)

    if (
        request.user.role != "TEACHER"
        or school_class.class_teacher_id != request.user.id
    ):
        messages.error(
            request,
            "Huna ruhusa ya kujaza tabia ya darasa hili. "
            "Ni Mwalimu wa Darasa pekee ndiye mwenye ruhusa hii."
        )
        return redirect("attendance:my_classes")

    today = date_cls.today()
    try:
        academic_year = int(request.GET.get("academic_year") or today.year)
    except (TypeError, ValueError):
        academic_year = today.year
    term = request.GET.get("term") or "TERM_1"

    students = Student.objects.filter(school_class=school_class).order_by("first_name", "last_name")
    existing = {
        c.student_id: c for c in
        ConductReport.objects.filter(student__in=students, term=term, academic_year=academic_year)
    }

    rows = [{"student": s, "filled": s.id in existing and existing[s.id].has_any_data()} for s in students]

    return render(request, "attendance/conduct_list.html", {
        "school_class": school_class, "students": rows, "term": term,
        "academic_year": academic_year, "today": today,
    })


@login_required
def edit_conduct_view(request, student_id):
    """Fomu ya kujaza/kuhariri tabia ya mwanafunzi MMOJA kwa term/mwaka fulani."""
    student = get_object_or_404(Student, pk=student_id)
    school_class = student.school_class

    if (
        not school_class
        or request.user.role != "TEACHER"
        or school_class.class_teacher_id != request.user.id
    ):
        messages.error(request, "Huna ruhusa ya kujaza tabia ya mwanafunzi huyu.")
        return redirect("attendance:my_classes")

    today = date_cls.today()
    try:
        academic_year = int(request.GET.get("academic_year") or request.POST.get("academic_year") or today.year)
    except (TypeError, ValueError):
        academic_year = today.year
    term = request.GET.get("term") or request.POST.get("term") or "TERM_1"

    conduct, _ = ConductReport.objects.get_or_create(
        student=student, term=term, academic_year=academic_year,
        defaults={"school": school_class.school},
    )

    if request.method == "POST":
        form = ConductReportForm(request.POST, instance=conduct)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.school = school_class.school
            obj.student = student
            obj.term = term
            obj.academic_year = academic_year
            obj.recorded_by = request.user
            obj.save()
            messages.success(request, f"Tabia ya {student} imehifadhiwa.")
            return redirect(f"{request.path}?term={term}&academic_year={academic_year}")
    else:
        form = ConductReportForm(instance=conduct)

    return render(request, "attendance/edit_conduct.html", {
        "student": student, "school_class": school_class, "form": form,
        "term": term, "academic_year": academic_year,
    })
