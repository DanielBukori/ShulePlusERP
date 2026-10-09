# ShulePlusERP - Documentation Kamili ya Mfumo (Toleo la Kina)

**Aina ya Mfumo:** Django Multi-Tenant School ERP
**Lugha:** Kiswahili (UI/violezo), Kiingereza (code)
**Toleo:** Septemba 2026 - baada ya MVP push + vipengele vya ziada

---

# SEHEMU YA 1: MUUNDO WA JUMLA WA MFUMO

## 1.1 Multi-Tenancy (Shule Nyingi kwa Mfumo Mmoja)

Kila shule ina subdomain yake: `sehisco.localhost:8000`, `mwenge.localhost:8000`, n.k.
Kuna njia mbili za kufikia shule:
1. **Domain-based** - subdomain moja kwa moja (`sehisco.localhost`) - middleware
   inasoma `request.get_host()`, inatafuta `School` yenye subdomain hiyo, na
   kuiweka kwenye `request.school`.
2. **Path-based (`/s/<subdomain>/...`)** - kwa kesi ambapo subdomain routing
   haiwezekani (mfano development bila DNS wildcard) - URL zote muhimu za umma
   (branding) zina toleo la "local" (`post_list_local`, `post_detail_local`,
   `school_home_local`) zinazobeba `subdomain` kama kigezo cha URL badala ya
   kutegemea host header.

**KANUNI MUHIMU:** Kila `view` ya ndani (siyo ya umma) inaanza na:
```python
def _get_school(request):
    return getattr(request, 'school', None)

def some_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")
```
Kila query ya database INA LAZIMA kuchujwa na `school=school` - kukosa hili
kunamaanisha data ya shule moja inaweza kuonekana/kuchanganyika na shule
nyingine (data leak ya hatari sana kwenye multi-tenant system).

## 1.2 Roles na Uidhinishaji (Authorization)

`CustomUser.role` ina thamani: `HEADMASTER`, `SECOND_MASTER`, `ACADEMIC`,
`TEACHER`, `DISCIPLINE`, `ACCOUNTANT`, `PARENT`, `STUDENT`.

Kila app ina **decorator** yake ya ku-restrict role gani inaruhusiwa kuingia
kwenye view fulani - mfano:
```python
def accountant_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in ['HEADMASTER', 'SECOND_MASTER', 'ACCOUNTANT']:
            return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")
        return view_func(request, *args, **kwargs)
    return wrapper
```
Kila app ina decorator yake: `accountant_required`, `fee_manager_required`
(HEADMASTER+SECOND_MASTER pekee kwa mambo ya fedha nyeti), `store_keeper_required`,
`discipline_role_required`, `academic_role_required`, `staff_manager_required`,
`branding_manager_required`.

## 1.3 Login Flow (accounts app)

1. `accounts:login` (`TenantLoginView`) - namba ya simu + password.
2. Kama role inahitaji OTP (HEADMASTER/SECOND_MASTER/ACADEMIC/TEACHER/DISCIPLINE/
   ACCOUNTANT) → `accounts:otp_verify` (SMS + email kupitia Beem Africa).
   PARENT na STUDENT HAWAPITII OTP.
3. Kama ni mara ya kwanza (password ya muda) → `accounts:force_password_change`.
4. `accounts:post_login_redirect_view` - inasoma `request.user.role` **wakati
   halisi wa ombi** (siyo cached) na kumpeleka kwenye dashibodi sahihi:
   ```python
   ROLE_DASHBOARD_URLS = {
       'HEADMASTER': 'academic:academic_dashboard',
       'ACADEMIC': 'academic:academic_dashboard',
       'TEACHER': 'teacher_portal:teacher_dashboard',
       'DISCIPLINE': 'discipline:discipline_dashboard',
       'ACCOUNTANT': 'accountant:accountant_dashboard',
       ...
   }
   ```
   Hii ndiyo maana ukibadilisha cheo cha mtu (tazama 4.1), akiingia tena
   anapelekwa moja kwa moja dashibodi mpya sahihi - HAKUNA kingine cha
   kubadilisha kwa hilo.

---

# SEHEMU YA 2: SHULE_CORE (Models za Msingi)

Hii ndiyo app inayoshikilia models zinazotumiwa na apps zote nyingine.

## 2.1 Models Muhimu

- **`School`** - jina, subdomain, phone, email, `discipline_starting_score`,
  `discipline_alert_score`, logo/branding fields.
- **`CustomUser`** - AbstractUser iliyoongezwa `role`, `phone`, `school` (FK).
  ⚠️ `email` LAZIMA iwe `null=True` (tazama Sehemu ya 10, kosa #9).
- **`SchoolClass`** - jina la darasa, `level` ('O' au 'A'), `class_teacher`
  (FK CustomUser, hiari).
- **`Student`** - `reg_number`, `first_name`, `last_name`, `school_class` (FK),
  `combination` (FK Combination, `null=True` - kwa A-Level tu), `parent` (FK
  CustomUser). ⚠️ **HAINA field ya `is_active`** - kama unahitaji "wanafunzi
  wanaoendelea", tumia `school_class__isnull=False`.
  `unique_together = ('reg_number', 'school', 'school_class')` - reg_number
  INAWEZA kurudia kati ya madarasa tofauti (siyo unique shule nzima).
- **`Subject`** - jina, `level` ('O'/'A'), `combination` (FK, `null=True` -
  masomo ya O-Level hayana combination).
- **`Combination`** - kwa A-Level (mfano PCM, HGE) - `name`.
- **`AcademicResult`** - `student`, `subject`, `combination` (nullable),
  `school_class`, `exam_type`, `term`, `academic_year`, `score` (decimal
  0-100), `is_published`, **`is_auto_absent`** (mpya - tazama 3.3),
  `recorded_by`. `unique_together = ('student', 'subject', 'exam_type',
  'term', 'academic_year')`.
- **`Payment`** - `student`, `amount`, `date_paid`, `bank_name`,
  `receipt_number` (unique ndani ya shule, inaweza kurudiwa shule nyingine),
  `receipt_file`, `recorded_by`. Hii ni **ledger** - kila malipo ni safu
  mpya, HAKUNA "jumla inayosasishwa" hapa.

## 2.2 `base_tailwind.html`
Template ya msingi (Tailwind CSS) inayorithiwa na kurasa zote za ndani
(siyo za umma za branding - zile zina `public_base.html` yake). Ina sidebar
inayobadilika kutegemea `request.user.role`, search bar, notification bell.

---

# SEHEMU YA 3: ACADEMIC APP (Elimu/Matokeo)

## 3.1 Usajili wa Wanafunzi
- Mmoja mmoja (`register_student_view`) au kwa wingi (`bulk_register_view` -
  Excel via `openpyxl`).
- Reg number lazima iwe ya kipekee KATIKA darasa lake (siyo shule nzima).

## 3.2 Uingizaji wa Alama (CA Cascading) - `grading.py`
Mwalimu anaingiza alama za vipengele (Test 1/2 A/B, Midterm/Terminal/Annual
Exam) kupitia `teacher_portal:enter_marks` (spreadsheet). `grading.py` kisha
inakokotoa (`recompute_derived_results()`) wastani wa vipengele vilivyopo
(si jumla yake), ikipuuza vipengele ambavyo havijaingizwa:

```
MID_TERM   = wastani(Test1_A, Test2_A, MidtermExam)
Robo-2     = wastani(Test1_B, Test2_B, TerminalExam)
TERMINAL   = wastani(MID_TERM, Robo-2)
ANNUAL     = wastani(TERMINAL ya Muhula 1, AnnualExam ya Muhula 2)
```

Hizi tatu (`MID_TERM`, `TERMINAL`, `ANNUAL`) ndizo AcademicResult zenye
`exam_type` hizo - zinatumika kwenye broadsheet, ripoti za wazazi, na
takwimu. Series 1-5 ni tofauti kabisa - hazishiriki kwenye hesabu hii,
zinaonekana kwa mzazi kama "maendeleo" tu (formative, siyo summative).

## 3.3 Kuchapisha Matokeo + "Auto-F" (mpya)
`academic:publish_results` (`academic_publish_results_view`):

**HATUA (kwa POST):**
1. Kwa kila somo la darasa/combination: angalia kama LIPO alama moja au zaidi
   iliyorekodiwa (`AcademicResult.objects.filter(subject=..., school_class=...,
   term=..., exam_type=..., academic_year=..., combination=...).exists()`).
2. **KAMA LIPO** (mtihani ulifanyika): wanafunzi wote wa darasa wasio na alama
   ya somo hilo wanapewa `score=0` na `is_auto_absent=True` kiotomatiki.
3. **KAMA HALIPO** (mtihani wa somo hilo haukufanyika kabisa mzunguko huu):
   halifanyiwi lolote - halionekani kwenye ripoti yoyote, kama kwamba mtihani
   haukuwepo.
4. Baada ya hapo, `AcademicResult.objects.filter(...).update(is_published=True)`
   kwa rekodi zote za darasa/mtihani huo (zikiwemo hizo auto-F mpya).
5. SMS/bell inatumwa kwa wazazi wote wa darasa hilo.
6. Audit log inaandikwa, ikitaja idadi ya auto-F kama zipo.

**Kwa nini hii ilihitajika:** bila hivi, mwanafunzi asiyefanya mtihani
(alikuwa hayupo, au mwalimu alisahau kumjaza) angeonekana kwenye broadsheet
kama `-` (Division haiwezi kukokotolewa), na hangehesabika kwenye takwimu
kabisa - jambo linalofanya "kufuatilia waliokosa" kuwa vigumu. Sasa
wanaonekana kama F wazi, na wanaweza kufuatiliwa (tazama 3.5).

## 3.4 Broadsheet / Division (NECTA-style)
`academic:class_results` - inaonyesha jedwali la darasa zima na Division
(I/II/III/IV/0) ya kila mwanafunzi. Division inahesabiwa TU ikiwa mwanafunzi
ana alama za masomo YOTE yanayotakiwa - la sivyo `-` (siyo error).

## 3.5 Ripoti za Ufuatiliaji (Takwimu)

### a) Missing Marks Report (`academic:missing_marks_report`)
**KABLA ya publish** - unachagua Muhula+Mtihani+Mwaka(+Darasa la hiari),
inaorodhesha kila (Mwanafunzi, Somo) ambayo bado HAINA alama kabisa - kwa
ajili ya kumfuatilia mwalimu amalize kuingiza.

### b) Auto-Absent Report (`academic:auto_absent_report`)
**BAADA ya publish** - inaorodhesha wale walioishia kupewa F kiotomatiki
(`is_auto_absent=True`). Tofauti muhimu na Missing Marks: hawa TAYARI wana
rekodi (F), kwa hiyo Missing Marks Report haiwaoni tena - hii ndiyo ripoti
pekee inayowatambua kwa jina, somo, na tarehe ya publish, kwa ajili ya
kuhakiki (mgonjwa? kosa la kuandika?).

### c) Statistics (`academic:statistics`)
Unachagua Muhula+Mtihani+Mwaka(+Darasa la hiari), unapata:
- **Pie Chart** - jumla ya madaraja A/B/C/D/(E/S kwa A-Level)/F - shule
  nzima au darasa moja.
- **Bar Chart ya Grouped** - kila SOMO kwenye x-axis, na bar tofauti kwa
  kila daraja ndani ya somo hilo (siyo zimepandana - grouped, siyo stacked).

Grade ya kila jibu inakokotolewa na `_score_to_grade(score, subject.level)` -
helper ile ile inayotumiwa na broadsheet, hivyo daima ni sawa kila mahali.

Chart.js inapakiwa kutoka CDN (`cdn.jsdelivr.net/npm/chart.js`) - data
zinapitishwa salama kupitia Django `{{ variable|json_script:"id" }}` (siyo
`|safe` ya moja kwa moja - inaepuka XSS).

**Kumbuka:** Division Pie (I/II/III/IV/0) ni KITU TOFAUTI, kipo kwenye
Academic Dashboard yenyewe (siyo ukurasa huu wa Statistics) - inaonyesha
Division ya MWANAFUNZI MZIMA (jumla ya masomo yake yote), wakati Statistics
hapa inahesabu kwa KILA JIBU LA SOMO moja moja.

---

# SEHEMU YA 4: STAFF APP (Wafanyakazi)

## 4.1 Usajili
`staff:register_teacher` - kila mfanyakazi anasajiliwa kama **TEACHER** kwa
default (hakuna dropdown ya role wakati wa usajili - hii ni ya makusudi).
`is_teaching_staff` na `is_store_keeper` ni flags tofauti kwenye `Staff`
(model tofauti na `CustomUser`, ina `OneToOneField(CustomUser)`).

## 4.2 Kubadilisha Cheo (mpya)
`staff:edit_staff_role` - Headmaster/Second Master pekee. Fomu ina:
- **Dropdown ya role** - Mwalimu/Academic Master/Second Master/Discipline/
  Accountant. Kuchagua "Mwalimu" ni njia ya "kumvua" cheo maalum.
- **Checkbox huru ya Store Keeper** - haihusiani na role field, inaweza
  kuwashwa/kuzimwa wakati wowote pamoja na role yoyote.

Kwenye `staff:teacher_list`, kila mstari una kitufe "Badilisha Cheo"
(kinachopelekea ukurasa huu) - **muhimu:** hakiwekwi ndani ya `<a>` ile
inayopeleka `manage_assignments`, ni kipengele tofauti (sibling), kuepuka
tatizo la nested anchors (tazama Sehemu 10, kosa #2).

## 4.3 Class Teacher & Subject Assignments
`staff:assign_class_teacher` - kumteua mwalimu kuwa class teacher wa darasa.
`staff:manage_assignments` - kumpangia mwalimu masomo ya kufundisha (dropdown
ya somo sasa inaonyesha `{{ choice.name }}` badala ya default object repr).

---

# SEHEMU YA 5: STORE APP (Vifaa vya Wanafunzi)

## 5.1 Models
- **`ContributionRequirement`** - `school_class` (nullable = shule nzima),
  `term`, `academic_year`, `item_name`, `quantity_required`, **`is_published`**,
  **`published_at`** (mpya - fields hizi mbili zinahitaji migration).
- **`StudentContribution`** - `student`, `requirement`, `quantity_brought`
  (JUMLA, siyo ledger), `recorded_by`, `notes`. `unique_together = (student,
  requirement)`.
- **`StoreStock`** - `item_name`, `quantity_in_stock` (jumla ya shule nzima
  ya kifaa hicho).
- **`StockMovement`** - historia ya kila mabadiliko ya stock (ledger).

## 5.2 Mtiririko Kamili
1. Academic/Second Master anaweka **Sharti** (`store:add_requirement`) -
   mfano "Ream 2 - Form 1 - Muhula wa Kwanza - 2026".
2. Anabonyeza **"Chapisha"** (`store:publish_requirement`) - hii inatengeneza
   `StudentContribution(quantity_brought=0)` kwa **wanafunzi WOTE** wa darasa
   husika kwa mpigo mmoja. Bila hatua hii, mwanafunzi asiyeguswa na Store
   Keeper HAONEKANI popote kama "anadaiwa" - baada ya "Chapisha", wote
   wanaonekana mara moja kwenye ripoti ya mzazi na dashibodi ya Store Keeper.
3. Store Keeper anarekodi vifaa vilivyoletwa - njia mbili:
   - **Mmoja mmoja** (`store:record_contribution`) - na notes.
   - **Kwa Wingi** (`store:record_contribution_spreadsheet`) - chagua Sharti
     moja, jedwali la wanafunzi wote wa darasa hilo linaonekana, jaza
     "Kiasi Kipya" kwa waliolete tu.
4. **MUHIMU:** kiasi kinachoingizwa (kwenye njia zote mbili) kina**ONGEZEKA**
   juu ya kilichopo (`existing.quantity_brought + qty_now`), SIYO
   kubadilishwa (overwrite). Hii ilikuwa BUG kubwa iliyorekebishwa - awali
   deni "halikupungua kamwe" kwa sababu kila "kurekodi" kulifuta jumla ya
   nyuma.
5. `StudentContributionForm.validate_unique()` **imezimwa kwa makusudi**
   (`pass`) - kwa sababu baada ya "Chapisha", kila mwanafunzi TAYARI ana
   rekodi (quantity_brought=0), na Django ModelForm ingezuia UPDATE yoyote
   ikidai "already exists". Hii ni tabia ya KAWAIDA kwenye muundo huu.

---

# SEHEMU YA 6: DISCIPLINE APP (Nidhamu)

## 6.1 Models
- **`OffenseType`** - `name`, `points_deducted`, `description`.
- **`DisciplineIncident`** - `student`, `offense_type`, `academic_year`,
  `date_occurred`, `notes`, `evidence_file`, `recorded_by`. HII NI LEDGER
  (hakuna unique_together - kosa moja linaweza kutokea mara nyingi).
- **`DisciplineAlert`** - inaundwa kiotomatiki alama zikishuka chini ya
  `school.discipline_alert_score`. `unique_together = (student,
  academic_year)` - alert MOJA tu kwa mwaka (haiandikiwi mara mbili).

## 6.2 Alama (Score)
Kila mwanafunzi anaanza na `school.discipline_starting_score` (mfano 100).
Kila `DisciplineIncident` inapunguza `offense_type.points_deducted`. Alama
za sasa zinakokotolewa kwa `get_student_discipline_score(student,
academic_year)` - jumla ya alama za mwanzo - jumla ya makato yote ya mwaka
huo.

## 6.3 Kurekodi
- **Mmoja mmoja** (`discipline:record_incident`) - kwa makosa yenye ushahidi
  (picha/PDF) au maelezo marefu.
- **Kwa Wingi** (`discipline:record_incident_spreadsheet`) - chagua
  Darasa+Tarehe+Mwaka, jedwali linaonekana na **safu = Aina za Makosa**
  (siyo namba - tofauti na Store/Accountant), **kiini = checkbox**. Tiki tu
  boksi la kosa alilofanya mwanafunzi siku hiyo.
- Kila tiki inatengeneza `DisciplineIncident` MOJA kwa (mwanafunzi, kosa,
  tarehe) kupitia `get_or_create` - kuepuka kuandika mara mbili ukitembelea
  ukurasa huo huo tena kwa siku ile ile.
- Alama zikishuka chini ya threshold wakati wa kurekodi (njia zote mbili),
  `DisciplineAlert` inaundwa na mzazi anatumiwa SMS/bell papo hapo.

---

# SEHEMU YA 7: ACCOUNTANT APP (Fedha/Ada)

## 7.1 Models
- **`FeeStructure`** - `school_class`, `academic_year`, `amount` (ada ya
  MWAKA MZIMA - hakuna muhula).
- **`OtherCharge`** - michango ya ziada (mfano Mahafali) - `school_class`
  (nullable = shule nzima), `academic_year`, `amount`, `authorized_by`
  (LAZIMA kama muundaji ni ACCOUNTANT - Headmaster/Second Master ndiye
  anayeidhinisha; kama muundaji NI Headmaster/Second Master mwenyewe,
  haihitajiki - yeye mwenyewe ndiye mamlaka).
- **`StudentFeeAssessment`** - "invoice" ya mwaka - `student`,
  `academic_year`, `amount_required` (FeeStructure + OtherCharge zote za
  mwaka huo zikijumuishwa). `unique_together = (student, academic_year)`.
- **`Payment`** (kwenye `shule_core`) - ledger, tazama 2.1.

## 7.2 Mtiririko Kamili
1. Headmaster/Second Master anaweka **FeeStructure** (`accountant:
   set_fee_structure`) kwa kila darasa+mwaka.
2. Anabonyeza **"Tengeneza Tathmini"** (`accountant:generate_assessments`) -
   hii ndiyo "Publish" ya ada: inatengeneza au inasasisha
   `StudentFeeAssessment` kwa kila mwanafunzi mwenye FeeStructure ya mwaka
   huo, ikichanganya FeeStructure + OtherCharge zote zinazomhusu. Kuendesha
   tena baada ya kubadilisha ada/michango husasisha kiasi cha assessment
   iliyopo. Wanafunzi wasio na FeeStructure ya darasa lao mwaka huo
   wanaripotiwa kama "wameruka".
3. Accountant anarekodi malipo - njia mbili:
   - **Mmoja mmoja** (`accountant:record_payment`) - na picha ya risiti.
   - **Kwa Wingi** (`accountant:record_payment_spreadsheet`) - chagua
     Darasa+Mwaka, jedwali la wanafunzi wote, safu 4 kwa kila mmoja: Kiasi
     Kipya, Namba ya Risiti (LAZIMA, ya kipekee ndani ya shule husika), Benki, Picha
     ya Risiti (hiari).
4. **MUHIMU (tofauti na Store):** `Payment` ni LEDGER kamili - kila malipo
   ni rekodi MPYA kabisa, SIYO update ya jumla iliyopo. Deni linahesabiwa
   moja kwa moja: `get_student_debt = jumla_ya_assessment - jumla_ya_
   malipo_yote`. Kwa hiyo HAKUNA hatari ya "malipo kufutana" kama
   iliyokuwepo Store - muundo huu ulikuwa SAHIHI tangu awali.
5. Namba za risiti zinazojirudia ndani ya shule (ndani ya wingi mmoja au
   dhidi ya zilizopo tayari) zinarukwa na kuripotiwa bila kuharibu
   zilizofanikiwa; shule tofauti zinaweza kutumia namba ileile.
6. `view_receipt_view` - risiti (faili) inapatikana TU na Accountant/
   Headmaster/Second Master, AU mzazi wa mwanafunzi husika mwenyewe -
   haipatikani kwa `MEDIA_URL` ya wazi.

---

# SEHEMU YA 8: BRANDING APP (Tovuti ya Umma ya Shule)

## 8.1 Muundo
Kila shule ina tovuti yake ya umma (`school_home`, `post_list`, `post_detail`,
n.k.) - `BrandingPost` (machapisho/habari/gallery), `SchoolProfile` (wasifu,
dhamira, dira), `PostImage` (picha za ziada za post moja).

## 8.2 Machapisho (Posts)
- `branding:manage_posts` - orodha ya machapisho, na kitufe **"Chapisha
  Sasa" / "Rudisha Rasimu"** (`toggle_publish_post`) - click moja
  kubadilisha `is_published` bila kufungua fomu nzima.
- `branding:edit_post` - kuhariri post moja + kuongeza/kufuta picha za
  ziada.

## 8.3 Dashibodi (`branding:branding_dashboard`)
Inafikiwa kutoka sidebar ya ndani ("Tovuti ya Shule") - sasa inaonekana kwa
**HEADMASTER na SECOND_MASTER wote wawili** (awali ilikuwa HEADMASTER pekee
- kosa lililorekebishwa, kwani `branding_manager_required` tayari iliruhusu
wote wawili).

---

# SEHEMU YA 9: FAMILY_PORTAL (Dashibodi ya Mzazi)

Inaunganisha data kutoka apps zote: `academic` (matokeo), `accountant`
(madeni), `discipline` (nidhamu), `store` (michango/deni la vifaa),
`teacher_portal` (Series - "maendeleo tu"), `attendance` (ConductReport -
tabia/mwenendo).

`consolidated_report_preview.html` ina **selector ya "Ripoti za Nyuma"**
(term/exam_type/academic_year) - mzazi anaweza kuchagua kipindi chochote
kilichokwishachapishwa, siyo "cha sasa" tu. Ina PDF export yenye watermark
+ sahihi.

---

# SEHEMU YA 10: MAKOSA MAKUBWA YA KIMFUMO (Ili Yasijirudie)

## Kosa #1: `<form>` ndani ya `<form>`
**Dalili:** Kitufe cha submit "hakifanyi lolote" - hakuna error, hakuna
kitu kinachotokea, ukurasa unabaki palepale.
**Chanzo:** HTML HAIRUHUSU form ndani ya form - browser inavunja muundo
kimya kimya, ikimwacha submit button nje ya form halisi.
**Ilipopatikana:** `edit_post.html` (branding) - mini-form ya kufuta picha
ilikuwa ndani ya form kuu ya kuhariri post.
**Suluhisho:** Hamisha form ndogo NJE ya form kuu kabisa (kabla au baada).

## Kosa #2: `<a>` ndani ya `<a>`
**Dalili:** Kubonyeza sehemu fulani ya kadi/mstari kunafungua link isiyo
sahihi, au inayotarajiwa haifanyi kazi kabisa.
**Suluhisho:** Viungo viwili vinavyohitajika kwenye eneo moja (mfano jina
la mwanafunzi → maelezo, na kitufe cha "Badilisha") lazima viwe VIPENGELE
SAMBAMBA (siblings), siyo kimoja ndani ya kingine.

## Kosa #3: URL route ya `<str:x>` KABLA ya `<int:x>`
**Dalili:** `/news/4/` (ilipaswa kuwa post detail) badala yake inaonyesha
ukurasa wa orodha tupu.
**Chanzo:** Django inasoma `urlpatterns` juu chini; `<str:category>`
inakubali NAMBA PIA (ni string halali), kwa hiyo `news/<str:category>/`
ikiwa KABLA ya `news/<int:post_id>/` inashika ombi la `/news/4/` KWANZA.
**Suluhisho:** Weka pattern za `<int:...>` KABLA ya `<str:...>` zenye
muundo unaofanana.

## Kosa #4: ModelForm `unique_together` + `update_or_create` pattern
**Dalili:** "Tayari ipo" (already exists) error kila unapojaribu ku-update
rekodi iliyopo kihalali.
**Chanzo:** Django ModelForm inakagua `unique_together` KIOTOMATIKO wakati
wa `is_valid()` - hata kama view yako inatumia `update_or_create` (ambayo
ingeshughulikia hali hiyo sawa sawa).
**Suluhisho:** Override `validate_unique(self): pass` kwenye form husika,
ukiwa na maelezo ya wazi kwenye docstring KWANINI umezima.

## Kosa #5: Fomu isiyoonyesha `field.errors` kwa fields zote
**Dalili:** "Nimejaza kila kitu, kitufe hakifanyi lolote" - lakini kumbe
kuna kosa la validation halionekani popote.
**Suluhisho:** KILA field kwenye template LAZIMA iwe na
`{% for e in field.errors %}...{% endfor %}` - siyo baadhi tu ya fields.

## Kosa #6: Jina la faili lenye `__1_` au `(1)`
**Dalili:** `TemplateDoesNotExist`.
**Chanzo:** Browser inapakua faili mara ya pili na kuliongezea jina la
ziada kiotomatiki - jina hilo halilingani na linalotafutwa na Django.
**Suluhisho:** Hakikisha jina la faili kwenye folda ni SAWA KABISA na
jinsi `render()` inavyoliita.

## Kosa #7: "Kiasi" kinachobadilishwa (overwrite) badala ya kuongezwa
**Dalili:** Deni "halipungui" hata baada ya kurekodi malipo/mchango mara
kadhaa.
**Chanzo:** `update_or_create(..., defaults={'quantity_brought': kiasi_
kipya})` INABADILISHA kabisa thamani ya zamani, siyo kuongeza juu yake.
**Ilipopatikana:** Store (`record_contribution_view`).
**Suluhisho:** Soma kilichopo KWANZA (`existing.quantity_brought`), ongeza
kiasi kipya juu yake, ndipo uhifadhi jumla mpya.
**Kumbuka:** Payment (Accountant) HAIKUWA na tatizo hili tangu awali kwa
sababu kila malipo ni rekodi MPYA (ledger), siyo "jumla moja
inayosasishwa" - muundo tofauti kabisa na Store.

## Kosa #8: Dropdown inayotumia `{{ choice }}` badala ya field mahususi
**Dalili:** Dropdown inaonyesha "Subject object (1)" badala ya jina la
somo.
**Chanzo:** `{{ choice }}` kwenye template inaita `__str__()` ya default
ya Python/Django (siyo lazima iwe na jina zuri).
**Suluhisho:** Tumia `{{ choice.name }}` (au field mahususi ya jina) badala
ya `{{ choice }}` peke yake.

## Kosa #9: `CustomUser.email` bila `null=True`
**Chanzo:** Django `normalize_email()` inageuza `None` kuwa `""` kimya
kimya wakati wa `create_user()`.
**Suluhisho:** `email` field LAZIMA iwe na `null=True`; baada ya
`create_user()`, kagua: `if not user.email: user.email = None;
user.save(update_fields=['email'])`.

## Kosa #10: ModelForm yenye custom widget - mpangilio wa code
**Chanzo:** Widget (mfano `forms.Select(attrs={...})`) ikiwekwa BAADA ya
kuweka `queryset` kwenye `__init__`, choices zinapotea (dropdown inabaki
tupu).
**Suluhisho:** Weka widget kwenye `Meta.widgets` (au field definition)
KABLA, kisha rekebisha `queryset` kwenye `__init__` baadaye - siyo
kinyume chake.

## Kosa #11: `grading.py` haipitishi `school_class`
**Chanzo:** `recompute_derived_results()` ilikuwa haipitishi `school_class`
kwenye `AcademicResult.update_or_create(defaults={...})`, ikivunja
NOT NULL constraint.
**Suluhisho:** Hakikisha `defaults` dict ya `update_or_create` ina FIELDS
ZOTE zinazohitajika na NOT NULL constraints za model - siyo tu zile
"muhimu" kimantiki.

---

# SEHEMU YA 11: MIGRATIONS ZINAZOHITAJIKA

```bash
# Field mpya kwenye ContributionRequirement (store): is_published, published_at
python manage.py makemigrations store

python manage.py migrate
```

`AcademicResult.is_auto_absent` ipo kwenye migration `0020`; usitengeneze
migration nyingine kwa field hiyo.

---

# SEHEMU YA 12: VITU AMBAVYO BADO HAVIJAANZA

1. **Notifications wiring kamili** - `notify()` haijawekwa sehemu zote
   (mfano low-stock alert ya Store bado haijaunganishwa na `notify()`).
2. **Password change flow** kamili.
3. **Ukaguzi wa media** - Nginx inazuia ufikiaji wa moja kwa moja kwa
   `/media/`; faili za branding, risiti na vifurushi vya kazi zinatolewa
   kupitia views zenye ukaguzi wa ruhusa.
4. **Backups + self-healing**.
5. **Idara (Departments)** - uhusiano wake na Store/Class Teacher (mtumiaji
   amesema "baadaye tutaweka idara") - bado haijaanza kabisa.

---

# SEHEMU YA 13: MABADILIKO YA SEPTEMBA 2026

- Usajili wa shule unasubiri idhini ya msimamizi; shule na akaunti ya Mkuu
  huwashwa baada ya idhini.
- PIN za mwanafunzi/staff ni za nasibu na hutumwa kwa SMS; akaunti mpya
  huwashwa baada ya SMS kufanikiwa, na PIN haionyeshwi kwenye ukurasa.
- Jaribio la kuingia limewekewa kikomo; tenant middleware hukataa mtumiaji
  wa shule tofauti.
- Namba ya risiti ni ya kipekee kwa kila shule; madeni na ripoti huchuja
  malipo kwa shule.
- A-Level derived results huhifadhi combination, na matokeo yanayokosekana
  baada ya kuchapisha huwekewa `is_auto_absent` kwa Auto-Absent Report.
- `discipline_alert_score` ndiyo jina sahihi la threshold ya tahadhari.
- Production hutumia mazingira (`.env`), Gunicorn/systemd, CSS ya Tailwind
  iliyojengwa ndani, na Nginx huzuia `/media/` ya moja kwa moja.

# SEHEMU YA 14: MAAGIZO YA KIUFUNDI YA HARAKA (Quick Reference)

| Kitu | Sheria |
|---|---|
| `School` | Inahitaji `phone`, `email`, `discipline_starting_score`, `discipline_alert_score` |
| `Staff` | Inahitaji `is_store_keeper` |
| `CustomUser.email` | LAZIMA `null=True` |
| `Student` | HAINA `is_active` - tumia `school_class__isnull=False` |
| `Student` unique | `(reg_number, school, school_class)` - siyo school peke yake |
| ModelForm + custom widget | Widget KABLA ya queryset override |
| POST view | `form = SomeForm(request.POST,...)` LAZIMA itengenezwe KWANZA |
| WeasyPrint (Windows) | Inahitaji MSYS2 (Linux/Oracle salama) |
| Excel | `openpyxl` |
| PDF | `weasyprint` |
| SMS | `requests` (Beem Africa) |
| Charts (Statistics) | Chart.js kupitia CDN (`cdn.jsdelivr.net`) |
| Ledger models (Payment, DisciplineIncident, StockMovement) | Kila tukio ni rekodi MPYA, hazibadilishwi |
| "Jumla" models (StudentContribution) | update_or_create + ONGEZA juu ya kilichopo, siyo overwrite |

---

*Waraka huu unabeba KILA kitu kilichojengwa na kurekebishwa kwenye
ShulePlusERP hadi Septemba 2026 - muundo, mantiki ya biashara, workflows
kamili, na makosa ya kimfumo ya kuepuka. Kwa msimbo halisi wa kila
faili, rejea kwenye repo yako - waraka huu ni ramani ya jinsi kila
kipande kinavyounganika, siyo nakala ya code yenyewe.*
