# Kuweka ShulePlusERP live kwenye Render

Mradi una Blueprint ya kujaribu bila malipo kwenye `render.yaml`: Render
huendesha Django app, na Neon huhifadhi PostgreSQL. UI (HTML templates na
Tailwind CSS) ni sehemu ya Django app hiyo hiyo; **huhitaji Vercel au frontend
service tofauti**.

## Kabla ya kuanza

- Push code yote unayotaka ku-deploy kwenda GitHub; Render haitumii faili
  ambazo hazijacommit/push.
- Hakikisha una repo `Daniel-bukori/ShulePlusERP` kwenye GitHub na ruhusa ya
  kuunganisha Render nayo.
- Render Free inafaa kwa demo/kujifunza, si production: service hulala baada ya
  kutokuwa na traffic na inaweza kuchukua takriban dakika moja kuamka. Filesystem
  yake ni ya muda; uploads zinaweza kupotea baada ya restart, spin-down au deploy.
- Neon Free ina mipaka ya storage/compute. Kagua mipaka na masharti ya sasa ya
  providers kabla ya kutegemea kwa matumizi ya shule.
- Blueprint hii haitengenezi database ya Render yenyewe. Tengeneza Neon project
  kwanza na toa `DATABASE_URL` yake wakati Render itakapokuuliza.
- Kwa kuanza kujaribu URL ya `onrender.com`, domain maalum haihitajiki. Hata
  hivyo, mfumo huu hutambua shule kwa subdomain. Ili shule ziweze kufikiwa kwa
  mfano `shuleyako.example.com`, nunua/unganisha domain yako na tengeneza DNS
  wildcard `*.example.com` kuelekea Render web service.

## Deploy ya kwanza

1. Neon Dashboard → **Create project** → chagua Free plan/region, kisha
   fungua **Connect** na unakili connection string ya PostgreSQL (chagua pooled
   connection ikiwa Neon inaitoa). Ichukulie kama password: usiweke GitHub au
   kuiweka kwenye ujumbe wa umma.
2. Render Dashboard → **Blueprints** → **New Blueprint Instance** → unganisha
   repo `Daniel-bukori/ShulePlusERP` na branch `main`.
3. Render itakuonyesha `DATABASE_URL` wakati wa kuunda Blueprint. Bandika
   connection string ya Neon. Thibitisha kuwa string inaanza na
   `postgresql://` au `postgres://` na ina `sslmode=require`; Neon hutoa SSL
   kwenye connection string yake.
4. Bonyeza **Apply**. Blueprint itasafisha na kujenga upya static files, kisha app itaendesha
   migrations na kuanza Gunicorn. Render itatengeneza `DJANGO_SECRET_KEY`
   yenyewe.
5. Subiri build/deploy ikamilike. Fungua URL iliyoonyeshwa na Render
   (`https://<jina-la-service>.onrender.com/`). `/health/` inapaswa kurudisha
   `{"status":"ok"}`.
6. Tengeneza Django admin. Kama **Shell** haipo kwenye Render Free, tumia
   bootstrap ya mara moja:
   - Web service → **Environment**: ongeza `DJANGO_SUPERUSER_USERNAME`,
     `DJANGO_SUPERUSER_EMAIL`, na `DJANGO_SUPERUSER_PASSWORD`. Weka nywila
     imara; usiiweke kwenye code, Git, au ujumbe.
   - Web service → **Settings** → **Build & Deploy** → **Start Command**:
     badilisha kwa muda kuwa:

     ```bash
     python manage.py migrate --noinput && python manage.py createsuperuser --noinput && gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120
     ```

   - Hifadhi mabadiliko na subiri deploy ifanikiwe. `createsuperuser` itasoma
     credentials hizo kutoka environment. Kama deploy itashindwa au username
     tayari ipo, usiache command hiyo hapo; fuata ujumbe wa deploy na utumie
     username mpya inayopatikana.
   - Mara moja baada ya deploy kufanikiwa, rudisha **Start Command** kuwa:

     ```bash
     python manage.py migrate --noinput && gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120
     ```

     Ondoa `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, na
     `DJANGO_SUPERUSER_PASSWORD` kwenye **Environment**, hifadhi na deploy tena.
     Akaunti iliyoundwa itabaki kwenye Neon database.

   Kama una Shell kwenye service plan yako, njia rahisi ni:

   ```bash
   python manage.py createsuperuser
   ```

7. Ingia `https://<jina-la-service>.onrender.com/admin/` kwa akaunti ya admin.
   Hii ni **admin wa mfumo mzima**. Kutoka **Schools**, ongeza shule moja kwa
   moja; au tumia `/register-school/` kisha admin aidhinishe ombi la Mkuu.

## Frontend: iko wapi?

Frontend ya app hii si project tofauti ya React/Vue. Kurasa zake ni Django
templates ndani ya `*/templates/`, na CSS iliyojengwa iko `static/css/`.
Gunicorn inahudumia backend na kurasa hizo kwenye service moja; WhiteNoise
inahudumia static CSS/JS. Kwa hiyo usitengeneze Vercel project kwa sasa.

## Kuingia kwenye shule na kuandaa madarasa/masomo

Kwa sasa Render URL ya kawaida (`https://<jina-la-service>.onrender.com/`)
haiwezi kuwa na subdomain tofauti kwa kila shule. Baada ya admin kuidhinisha
shule na Mkuu kuingia, mfumo hutumia shule iliyounganishwa na akaunti hiyo kama
tenant kwenye base URL. Mtumiaji wa shule nyingine akiingia kwa akaunti yake
ataona shule yake tu; subdomain ya shule nyingine kwenye custom domain bado
inakataa akaunti isiyolingana.

Baada ya kuingia kama HEADMASTER, SECOND_MASTER, au ACADEMIC:

1. Fungua **Madarasa na Masomo** kwenye menyu, au nenda
   `/academic/setup/`.
2. Madarasa ya msingi hutengenezwa kiotomatiki kulingana na `school_level`:
   O-Level = Form I–IV, A-Level = Form V–VI, na shule ya viwango vyote =
   Form I–VI. Ukurasa huu hutengeneza zinazokosekana bila kufuta au kubadili
   madarasa yaliyopo; tumia fomu kuongeza stream kama Science au Arts.
3. Ongeza masomo. Masomo ya O-Level hayahitaji combination; A-Level yanahitaji
   combination inayolingana. Masomo yanafungamanishwa na shule iliyoingia,
   na darasa/somo lililowekwa shule nyingine haliwezi kuchaguliwa.
4. Baada ya hapo madarasa yanaonekana kwenye usajili wa wanafunzi na madarasa
   yanatumika kwenye matokeo. Hakikisha pia walimu wamepangiwa somo/darasa
   sahihi kabla ya kuingiza alama.

Combination kwa sasa ni katalogi ya pamoja kwenye database, si ya shule moja.
Ili shule moja isibadilishe chaguo za nyingine, ni admin wa mfumo pekee ndiye
anayeongeza/kusimamia combination kupitia Django Admin. Mkuu anaweza kuchagua
combination zilizopo wakati wa kusajili masomo ya A-Level.

Huu ni mpangilio wa mpito wa Render, si kubadilisha tenant kuwa wa pamoja:
`TenantMiddleware` hutanguliza subdomain inayotambulika kwenye custom domain na
huzuia mtumiaji wa shule A kufungua subdomain ya shule B. Baadaye, unapokuwa na
domain yako, ongeza domain na wildcard kwenye Render/DNS, weka `BASE_DOMAIN`,
`ALLOWED_HOSTS` na `CSRF_TRUSTED_ORIGINS` kama sehemu ya domain hapo chini.
Base URL ya Render itaendelea kutumia shule ya akaunti iliyoingia; links za
shule maalum zitakuwa `https://<subdomain>.<domain-yako>/`.

## Kupokea barua pepe na SMS

Demo ya ukurasa inaweza kuonekana bila SMS/email credentials, lakini login za
baadhi ya roles zinahitaji OTP. Render Free huzuia outbound SMTP kwenye ports
25, 465 na 587. Hivyo SMTP ya kawaida haiwezi kutegemewa hapo; magic links za
email pia hazitafanya kazi mpaka email ibadilishwe kutumia provider API ya
HTTPS au uhamie kwenye hosting inayoruhusu SMTP.

Kwa OTP za roles, weka credentials za Beem kwenye Render → **Environment**:
`BEEM_API_KEY` na `BEEM_SECRET_KEY`. Beem inahitaji akaunti yenye SMS credits.
Kwa email, ongeza SMTP credentials tu kwenye plan/network inayoruhusu SMTP:
`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`,
`EMAIL_HOST_PASSWORD`, `EMAIL_BACKEND`, na `DEFAULT_FROM_EMAIL`. Hifadhi
secrets kwenye Render Environment, usizi-commit.

## Kuunganisha domain yako (inahitajika kwa shule nyingi)

Kwa mfumo wa subdomain wa kila shule, tumia domain yako badala ya kutegemea
`onrender.com`:

1. Kwenye Render web service, ongeza domain ya msingi, mfano
   `example.co.tz`, na wildcard domain `*.example.co.tz`; fuata maelekezo ya
   Render ya kuthibitisha domain na TLS.
2. Kwa DNS provider wako, weka records zinazoelekezwa kwenye target ambayo
   Render inaonyesha kwa service, kwa apex na wildcard. Usibuni target ya DNS;
   tumia ile inayoonyeshwa kwenye Render.
3. Kwenye **Environment** ya web service badilisha:
   - `BASE_DOMAIN=example.co.tz`
   - `CSRF_TRUSTED_ORIGINS=https://example.co.tz,https://*.example.co.tz`
   - Ongeza `example.co.tz` na `.example.co.tz` kwenye `ALLOWED_HOSTS`.
4. Deploy upya. Hakikisha admin, usajili, login, na subdomain ya shule
   (mfano `https://jina-la-shule.example.co.tz/`) zinafunguka.

URL ya `onrender.com` inaweza kuonyesha landing page, lakini haiwezi kutumika
kama wildcard subdomain ya tenant kwa shule zako. Bila domain yako, hakuna
`jina-la-shule.onrender.com` inayoweza kuelekezwa kwa app hii kwa default.
Kwa tenant routing tumia domain yako na wildcard subdomain, kisha sasisha
`BASE_DOMAIN`, `ALLOWED_HOSTS`, na `CSRF_TRUSTED_ORIGINS` kama ilivyo chini.

## Weka huduma za SMS na barua pepe

Kabla ya kutumia OTP, magic links, au usajili wa watumiaji:

- Weka `BEEM_API_KEY` na `BEEM_SECRET_KEY` halisi za Beem.
- Weka `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, na
  `DEFAULT_FROM_EMAIL` za SMTP provider wako.
- Hifadhi siri hizi kwenye Render **Environment** pekee, kamwe si Git.

Usiache akaunti zikishindwa kupokea OTP/PIN: fanya login test kwa HEADMASTER,
staff, mwanafunzi na mzazi kabla ya kutangaza mfumo uko tayari kwa watumiaji.

## Muhimu kuhusu mafaili na backups

- Render Free filesystem ni ephemeral. Picha za shule, risiti, ushahidi na
  vifurushi vya kazi pamoja na picha za hero zinazopakiwa kupitia admin zinaweza
  kupotea baada ya service kulala, ku-restart au ku-deploy. **Usiweke nyaraka
  au taarifa halisi za wanafunzi kwenye demo hii.**
- Gunicorn imewekwa worker mmoja na threads mbili ili kupunguza matumizi ya RAM
  kwenye Free instance. Ikiwa bado unaona `WORKER TIMEOUT` au `SIGKILL`, kagua
  Metrics za memory kwenye Render na log za request ndefu; kuongeza timeout
  peke yake hakutatui process inayouawa kwa kukosa RAM.
- Database URL inapaswa kuwa connection string ya Neon yenye SSL. Settings
  hufunga connection baada ya kila request (`CONN_MAX_AGE=0`) ili kuepuka
  kutumia tena connection ambayo Neon imeifunga baada ya inactivity.
- Neon huhifadhi rekodi za database kivyake, lakini database backup haijumuishi
  media uploads. Kabla ya production chagua object storage ya kudumu yenye
  ruhusa za private/download kupitia views; usifungue risiti au nyaraka hadharani.
- Hata ukiwa na media storage, panga backup ya PostgreSQL na ujaribu restore.
- Tailwind CSS tayari imejengwa ndani ya `static/`; build ya Render haitaji
  Node.js.
- Hero slides zinadhibitiwa kwenye Django Admin → **Hero slides**. Maandishi na
  mpangilio wa slides saba vimewekwa tayari; chagua nafasi ya slide na pakia
  picha tu. Nafasi zisizokuwa na picha zitaendelea kuonyesha gradient na
  placeholder zake za sasa. Kwenye Render Free picha zilizopakiwa ni za muda
  tu, hivyo hifadhi ya kudumu ya media inahitajika kabla ya kutumia picha hizo
  kwenye production.
- Baada ya deploy, endesha backfill ya A-Level kupitia Render Shell ikiwa
  database ina rekodi za zamani:

  ```bash
  python manage.py backfill_a_level_result_combinations --dry-run
  python manage.py backfill_a_level_result_combinations
  ```

## Hatua ya baadaye ya production

Free stack ni ya majaribio tu. Kabla ya data halisi: tumia domain yako
(inahitajika kwa shule nyingi), service yenye persistent media storage au
private object storage, backups zilizojaribiwa, email/SMS zinazofanya kazi,
na provider plans zenye uptime/limits zinazokufaa. Render inasema wazi kuwa
Free instances hazikusudiwa production; kagua [Render Free limitations](https://render.com/docs/free)
na [Neon plans](https://neon.com/docs/introduction/plans).
