# ShulePlusERP — Muundo wa Mradi (Project Structure)

## Kanuni kuu
`shule_core` ndio "chanzo cha models zote" (School, CustomUser, Staff, Student, n.k.).
App nyingine zote (academic, accounts, store, discipline, accountant, branding, audit)
HAZINA models zake — zinaingiza (import) models kutoka `shule_core` na kuwa
na forms/views/urls/templates zake tu. Hii inaepusha mkanganyiko wa "somo hili
liko kwenye app gani" na kuzuia circular imports.

```
shuleplus_erp/                      <- ROOT ya project
│
├── manage.py
├── requirements.txt
│
├── shuleplus_erp/                  <- config package ya Django (jina la project)
│   ├── settings.py
│   ├── urls.py                     <- root urls, ina-include app zote
│   ├── wsgi.py
│   └── asgi.py
│
├── shule_core/                     <- ✅ CHANZO CHA MODELS ZOTE
│   ├── models.py                   <- School, CustomUser, Staff, SchoolClass,
│   │                                  Combination, Subject, Student,
│   │                                  SubjectAssignment, AcademicResult, Payment
│   ├── admin.py
│   ├── middleware.py                <- TenantMiddleware
│   ├── upload_paths.py              <- functions za upload_to (multi-tenant files)
│   ├── forms.py                     <- SchoolRegistrationForm
│   ├── views.py                     <- register_school
│   ├── urls.py
│   └── templates/shule_core/
│        ├── base.html               <- base template ya jumla (public pages)
│        └── register_school.html
│
├── accounts/                        <- ✅ tumeshajenga (login redirect)
│   ├── views.py                     <- post_login_redirect_view
│   ├── urls.py
│   └── templates/accounts/
│        └── dashboard_coming_soon.html
│
├── academic/                        <- ✅ tumeshajenga (matokeo, broadsheet, publish)
│   ├── forms.py                     <- ResultFilterForm, SubjectScoreFilterForm,
│   │                                  ReportPublishForm, StudentRegistrationForm
│   ├── views.py                     <- dashboard, class_results, subject_analysis,
│   │                                  publish_results, register_student
│   ├── urls.py
│   └── templates/academic/
│        ├── base_academic.html
│        ├── academic_dashboard.html
│        ├── class_results.html
│        ├── subject_analysis.html
│        ├── publish_results.html
│        └── register_student.html
│
├── store/                           <- 🔜 INAYOFUATA (michango ya wanafunzi, stock)
│   ├── models.py                    <- ContributionRequirement, StudentContribution,
│   │                                  StoreStock, StockMovement
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   └── templates/store/
│
├── discipline/                      <- 🔜 (makosa, alama, alert)
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   └── templates/discipline/
│
├── accountant/                      <- 🔜 (ada, madeni, risiti - Payment tayari ipo shule_core)
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   └── templates/accountant/
│
├── branding/                        <- 🔜 (tovuti ya umma ya shule)
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── templates/branding/
│
├── audit/                           <- 🔜 (audit log ya jumla - nani/nini/lini)
│   ├── models.py                    <- AuditLog
│   ├── signals.py
│   └── apps.py
│
├── static/
│   └── (CSS/JS/picha za pamoja - siyo za shule maalum)
│
└── media/
    └── schools/
         └── <subdomain-la-shule>/
              ├── logo/
              ├── receipts/<mwaka>/<mwezi>/
              ├── home_packages/<darasa>/<somo>/
              ├── result_reports/<mwaka>/<term>/
              ├── discipline/
              ├── store/
              └── branding/
```

## MUHIMU: Rekebisho la haraka kwenye files ulizonazo tayari

`academic/forms.py` na `academic/views.py` nilizokuandikia ziliandikwa
zikitegemea kuwa na `models.py` yake yenyewe (`from .models import ...`).
Kwa kuwa umeniambia una app moja tu (`shule_core`) yenye models zote,
BADILISHA import kwenye files hizo mbili kutoka:

```python
from .models import SchoolClass, Subject, AcademicResult, Student, Combination
```

kuwa:

```python
from shule_core.models import SchoolClass, Subject, AcademicResult, Student, Combination
```

Vivyo hivyo kwa `views.py` (mstari wenye `from .models import ...`).
