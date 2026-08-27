# ShulePlusERP

Mfumo kamili wa usimamizi wa shule (School ERP) ulioundwa maalum kwa mazingira
ya Tanzania — **multi-tenant**, kila shule ina tovuti/mfumo wake wenye
subdomain yake (`<jina-la-shule>.shulepluserp.co.tz`), ukiwa umejengwa kwa
Django.

## Vipengele

| Idara | Kinachofanya |
|---|---|
| **Academic** | Usajili wa wanafunzi (single + Bulk Excel Import), Marks Entry ya CA (Test1/Test2/Midterm/Terminal/Annual), Broadsheet, Division ya kistaili cha NECTA, Publish matokeo, PDF/Excel export, Global Search, Student Promotion |
| **Teacher Portal** | Spreadsheet moja kwa mwalimu — jaza marks za somo lake, ona "Matokeo ya Sasa" papo hapo |
| **Attendance** | Mahudhurio ya kila siku — Class Teacher anajaza register ya mwezi mzima (Present/Absent/Late/Excused) |
| **Staff** | Usajili wa walimu, subject assignments |
| **Store** | Michango ya wanafunzi (vifaa), stock ya duka la shule, alert za low-stock |
| **Discipline** | Kurekodi makosa ya wanafunzi, alama za nidhamu, alert za moja kwa moja |
| **Accountant** | Ada, tathmini za mwaka, malipo, madeni, risiti (zenye ulinzi wa access) |
| **Branding** | Tovuti ya umma ya kila shule — kuhusu shule, uongozi, michepuo, miundombinu, testimonials, blog/matukio |
| **Marketing** | Landing page ya kampuni yenyewe (hero carousel, bei, FAQ, omba demo) |
| **Family Portal** | Dashboard ya wazazi/wanafunzi — Ripoti Kamili (Academic+Ada+Nidhamu+Duka kwenye PDF moja) |
| **Notifications** | Bell icon (in-app) + SMS pamoja, kwa matukio yote (matokeo, malipo, low-stock, nidhamu) |
| **Audit Log** | Kumbukumbu ya nani-alifanya-nini-lini, kwa Headmaster |

## Muundo wa Kiufundi

- **Backend:** Django 5.2, PostgreSQL
- **Multi-tenancy:** subdomain-based (`TenantMiddleware`), data ya kila shule imetengwa kabisa
- **PDF:** WeasyPrint (broadsheet, risiti, ripoti)
- **Excel:** openpyxl (import/export ya matokeo)
- **SMS:** Beem Africa API
- **Frontend:** Tailwind CSS (sidebar navigation, mobile-friendly)

Angalia [`PROJECT_STRUCTURE.md`](./PROJECT_STRUCTURE.md) kwa muundo kamili wa apps 14 na folders.

## Kuanzisha kwa Maendeleo (Local Development)

```bash
git clone https://github.com/<jina-lako>/shuleplus-erp.git
cd shuleplus-erp
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Nakili .env.example kuwa .env, jaza SECRET_KEY/DB/BEEM keys zako
copy .env.example .env

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

> **Windows:** WeasyPrint (PDF generation) inahitaji MSYS2 + GTK runtime kuwekwa
> kando - tazama https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows

## Deployment (Uzalishaji)

Mradi una scripts tayari kwenye `deploy/`:
- `deploy/shuleplus.service` — systemd unit (self-healing, `Restart=always`)
- `deploy/backup.sh` — pg_dump + media backup ya kila siku (cron), cleanup ya siku 7
- `deploy/restore.sh` — kurudisha backup

Imejaribiwa kwenye **Oracle Cloud Always Free** (Ubuntu 24.04, ARM Ampere A1) +
Nginx + Let's Encrypt (wildcard SSL kwa subdomains).

## Usalama

- `.env` na `media/` **HAZIPO** kwenye repo hii (angalia `.gitignore`) — zina siri
  na taarifa binafsi za wanafunzi/wazazi halisi
- Kila shule ina data iliyotengwa kabisa (multi-tenant isolation)
- Risiti za malipo zina auth-protected view (siyo link ya moja kwa moja)
- Audit log inarekodi kila kitendo muhimu

## Leseni

Haki zote zimehifadhiwa © ShulePlusERP.
