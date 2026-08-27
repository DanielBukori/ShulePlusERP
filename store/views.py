from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render

from shule_core.models import Student
from .forms import ContributionRequirementForm, StudentContributionForm, StockAdjustmentForm
from .models import ContributionRequirement, StudentContribution, StoreStock, StockMovement
from audit.utils import log_action


MANAGER_ROLES = ['HEADMASTER', 'SECOND_MASTER', 'ACADEMIC']


def _get_school(request):
    return getattr(request, 'school', None)


def _is_store_keeper(user):
    staff = getattr(user, 'staff_profile', None)
    return bool(staff and staff.is_store_keeper)


def requirement_manager_required(view_func):
    """Kuweka 'kinachotakiwa kuletwa' ni kazi ya Headmaster/Second Master/Academic tu."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in MANAGER_ROLES:
            return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")
        return view_func(request, *args, **kwargs)
    return wrapper


def store_keeper_required(view_func):
    """
    Kurekodi michango na stock ni kazi ya Store Keeper (mwalimu aliyeteuliwa
    - is_store_keeper=True kwenye Staff), au wakuu (Headmaster/Second Master)
    kwa uangalizi.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        allowed = request.user.role in ('HEADMASTER', 'SECOND_MASTER') or _is_store_keeper(request.user)
        if not allowed:
            return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu - wewe si Store Keeper.")
        return view_func(request, *args, **kwargs)
    return wrapper


from notifications.utils import notify
from shule_core.models import CustomUser


def _notify_low_stock(stock):
    """
    Inatuma bell + SMS kwa Headmaster/Second Master wote wa shule,
    kuwajulisha kifaa kimeisha stock.
    """
    heads = CustomUser.objects.filter(
        school=stock.school, role__in=['HEADMASTER', 'SECOND_MASTER']
    ).exclude(phone__isnull=True).exclude(phone='')
    message = (
        f"ShulePlusERP Store: '{stock.item_name}' zimebaki {stock.quantity_in_stock} tu "
        f"(chini ya kiwango cha {stock.low_stock_threshold})."
    )
    for head in heads:
        notify(head, stock.school, message, link='/store/dashboard/')


@store_keeper_required
def store_dashboard_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    stocks = StoreStock.objects.filter(school=school).order_by('item_name')
    low_stock_items = [s for s in stocks if s.is_low]

    requirements = ContributionRequirement.objects.filter(school=school).order_by('-academic_year', 'term')

    context = {
        'school': school,
        'stocks': stocks,
        'low_stock_items': low_stock_items,
        'requirements': requirements,
    }
    return render(request, 'store/store_dashboard.html', context)


@requirement_manager_required
def add_requirement_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    if request.method == 'POST':
        form = ContributionRequirementForm(request.POST, school=school)
        if form.is_valid():
            requirement = form.save(commit=False)
            requirement.school = school
            requirement.created_by = request.user
            requirement.save()

            # Hakikisha StoreStock ya kifaa hiki ipo (hata kama bado ni 0)
            StoreStock.objects.get_or_create(school=school, item_name=requirement.item_name)

            messages.success(request, f"Sharti la '{requirement.item_name}' limewekwa.")
            return redirect('store:add_requirement')
    else:
        form = ContributionRequirementForm(school=school)

    requirements = ContributionRequirement.objects.filter(school=school).order_by('-academic_year', 'term')
    context = {'school': school, 'form': form, 'requirements': requirements}
    return render(request, 'store/add_requirement.html', context)


@store_keeper_required
def record_contribution_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    if request.method == 'POST':
        form = StudentContributionForm(request.POST, school=school)
        if form.is_valid():
            with transaction.atomic():
                contribution, created = StudentContribution.objects.update_or_create(
                    student=form.cleaned_data['student'],
                    requirement=form.cleaned_data['requirement'],
                    defaults={
                        'school': school,
                        'quantity_brought': form.cleaned_data['quantity_brought'],
                        'recorded_by': request.user,
                        'notes': form.cleaned_data.get('notes', ''),
                    },
                )

                # Ongeza kwenye StoreStock + StockMovement kwa kile kilicholetwa
                stock, _ = StoreStock.objects.get_or_create(
                    school=school, item_name=contribution.requirement.item_name
                )
                qty = form.cleaned_data['quantity_brought']
                if qty > 0:
                    stock.quantity_in_stock += qty
                    stock.save()
                    StockMovement.objects.create(
                        school=school, stock=stock, quantity_change=qty,
                        reason='STUDENT_CONTRIBUTION', recorded_by=request.user,
                        notes=f"Kutoka kwa {contribution.student}",
                    )

            if contribution.is_complete:
                messages.success(request, f"{contribution.student} amekamilisha mchango wa {contribution.requirement.item_name}.")
            else:
                messages.success(
                    request,
                    f"{contribution.student} amerekodiwa. Anadaiwa {contribution.quantity_owed} ya "
                    f"{contribution.requirement.item_name} bado."
                )
            return redirect('store:record_contribution')
    else:
        form = StudentContributionForm(school=school)

    # Orodha ya wanafunzi wenye deni (haijakamilika)
    pending = StudentContribution.objects.filter(school=school).select_related('student', 'requirement')
    pending_debts = [c for c in pending if not c.is_complete]

    context = {'school': school, 'form': form, 'pending_debts': pending_debts}
    return render(request, 'store/record_contribution.html', context)


@store_keeper_required
def stock_adjustment_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST, school=school)
        if form.is_valid():
            stock = form.cleaned_data['stock']
            qty = form.cleaned_data['quantity']
            reason = form.cleaned_data['reason']

            with transaction.atomic():
                stock.quantity_in_stock += qty
                stock.save()
                StockMovement.objects.create(
                    school=school, stock=stock, quantity_change=qty, reason=reason,
                    recorded_by=request.user, notes=form.cleaned_data.get('notes', ''),
                )

            if stock.is_low:
                _notify_low_stock(stock)
                messages.warning(request, f"Stock ya '{stock.item_name}' iko chini ({stock.quantity_in_stock}). Wajulishe wakuu.")
            else:
                messages.success(request, f"Stock ya '{stock.item_name}' imesasishwa: sasa ni {stock.quantity_in_stock}.")
            log_action(
                request.user, school, 'STOCK_ADJUSTED',
                f"Amerekebisha stock ya '{stock.item_name}' kwa {qty:+d} ({reason}). Sasa: {stock.quantity_in_stock}."
            )
            return redirect('store:stock_adjustment')
    else:
        form = StockAdjustmentForm(school=school)

    context = {'school': school, 'form': form}
    return render(request, 'store/stock_adjustment.html', context)
