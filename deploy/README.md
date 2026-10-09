# Deployment ya ShulePlusERP (Ubuntu 24.04)

Mwongozo huu unatumia Ubuntu VPS (ikiwemo Oracle Cloud), PostgreSQL, systemd,
Nginx na domain yenye wildcard subdomains. Badilisha `example.co.tz` na domain
yako halisi. Usipakie `.env`, database, au `media/` kwenye Git.

## 1. Andaa server na DNS

1. Tengeneza Ubuntu 24.04 VPS yenye public IP isiyobadilika. Fungua TCP 22
   kutoka IP yako tu, na TCP 80/443 kutoka mtandao mzima kwenye firewall/NSG.
   **Usifungue port 5432 ya PostgreSQL kwa umma.**
2. Kwenye DNS ya domain, weka `A` records za `@`, `www`, na `*` zielekee
   public IP ya server. Subiri DNS propagation.
3. Kutoka PowerShell, unganisha kwa SSH:

   ```powershell
   ssh -i C:\path\to\your-key.pem ubuntu@SERVER_IP
   ```

## 2. Sakinisha mahitaji ya server

Ukiwa SSH ndani ya Ubuntu:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git python3-venv python3-dev build-essential libpq-dev \
  postgresql postgresql-contrib nginx libpango-1.0-0 libpangoft2-1.0-0 \
  libharfbuzz-subset0 libffi-dev shared-mime-info
```

Tengeneza password ya database:

```bash
openssl rand -hex 32
```

Tengeneza PostgreSQL database na user wa app; tumia password hiyo:

```bash
sudo -u postgres psql
```

```sql
CREATE USER shule_user WITH PASSWORD 'WEKA_PASSWORD_NDEFU_HAPA';
CREATE DATABASE shulepluserp_db OWNER shule_user;
\q
```

Tumia password ya nasibu isiyo na single quote ili iwe rahisi kuweka kwenye
environment file. Database ibaki inasikiliza localhost tu.

## 3. Pakua code na weka environment ya production

Kwa repo ya private, sanidi SSH deploy key ya GitHub kwenye server kabla ya
ku-clone; tumia public key pekee kwenye GitHub, usiweke private key kwenye repo.

```bash
cd /home/ubuntu
git clone git@github.com:Daniel-bukori/ShulePlusERP.git shuleplus_erp
cd /home/ubuntu/shuleplus_erp
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
```

Tengeneza key ya Django:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

Tengeneza environment file. Weka thamani zako halisi badala ya mifano hapa
chini. `ALLOWED_HOSTS` na `CSRF_TRUSTED_ORIGINS` zihusishe apex na subdomains.

```bash
sudo nano /etc/shuleplus.env
```

```ini
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=WEKA_KEY_ILIYOTENGENEZWA_HAPA
ALLOWED_HOSTS=example.co.tz,.example.co.tz
CSRF_TRUSTED_ORIGINS=https://example.co.tz,https://*.example.co.tz
BASE_DOMAIN=example.co.tz
DB_NAME=shulepluserp_db
DB_USER=shule_user
DB_PASSWORD=WEKA_PASSWORD_ILE_ILE_YA_POSTGRES
DB_HOST=127.0.0.1
DB_PORT=5432
BEEM_API_KEY=
BEEM_SECRET_KEY=
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.provider.example
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL="ShulePlusERP <noreply@example.co.tz>"
```

Weka ruhusa za kusoma kwa user wa app:

```bash
sudo chown ubuntu:ubuntu /etc/shuleplus.env
sudo chmod 600 /etc/shuleplus.env
```

SMS OTP za wafanyakazi zinahitaji Beem credentials halisi; bila hizo SMS
hazitafika kwa watumiaji. Weka email SMTP halisi pia kama utategemea email
kwa OTP au magic links. Credentials hizi ni siri: usiziweke kwenye Git.

## 4. Andaa database na systemd

Endesha migrations na unda admin. Shell hii husoma environment file kwa
commands za Django:

```bash
sudo -u ubuntu bash -c 'set -a; . /etc/shuleplus.env; set +a; cd /home/ubuntu/shuleplus_erp && ./venv/bin/python manage.py migrate'
sudo -u ubuntu bash -c 'set -a; . /etc/shuleplus.env; set +a; cd /home/ubuntu/shuleplus_erp && ./venv/bin/python manage.py createsuperuser'
sudo -u ubuntu bash -c 'set -a; . /etc/shuleplus.env; set +a; cd /home/ubuntu/shuleplus_erp && ./venv/bin/python manage.py collectstatic --noinput'
sudo -u ubuntu mkdir -p /home/ubuntu/shuleplus_erp/media
```

Washa service:

```bash
sudo cp /home/ubuntu/shuleplus_erp/deploy/shuleplus.service.txt /etc/systemd/system/shuleplus.service
sudo systemctl daemon-reload
sudo systemctl enable --now shuleplus
sudo systemctl status shuleplus --no-pager
```

Service inatumia `core.wsgi:application` na `/etc/shuleplus.env`. Kama haijaanza,
angalia `sudo journalctl -u shuleplus -n 100 --no-pager`.

## 5. Sanidi Nginx

Unda `/etc/nginx/sites-available/shuleplus` na ubadilishe domain. Hii config
hupeleka HTTP kwenda HTTPS na ku-proxy app kupitia socket ya Gunicorn:

```nginx
upstream shuleplus_app {
    server unix:/home/ubuntu/shuleplus_erp/shuleplus.sock;
}

server {
    listen 80;
    server_name example.co.tz www.example.co.tz *.example.co.tz;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name example.co.tz www.example.co.tz *.example.co.tz;

    ssl_certificate /etc/letsencrypt/live/example.co.tz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.co.tz/privkey.pem;
    client_max_body_size 10m;

    location ^~ /media/ {
        return 404;
    }

    location /static/ {
        alias /home/ubuntu/shuleplus_erp/staticfiles/;
    }

    location / {
        proxy_pass http://shuleplus_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Usiiwashe config bado: certificate paths zitapatikana baada ya kumaliza hatua
ya 6. Baada ya kupata certificate, weka symlink na u-test Nginx kama ilivyo
kwenye hatua hiyo.

Hii config **haifungui `media/` kama public static files**: folder hiyo inaweza
kuwa na risiti, ushahidi na taarifa za wanafunzi. Tumia data ya majaribio
kwanza; kabla ya production yenye taarifa halisi, hakiki njia salama ya kuhudumia
mafaili hayo pamoja na backup ya database na media. `Nginx` huzuia direct
requests za `/media/`; picha za branding na mafaili ya risiti, ushahidi na kazi
za nyumbani huhudumiwa na Django views zenye uthibitishaji wa shule/ruhusa.

## 6. Weka HTTPS

Kwa `*.example.co.tz`, Let's Encrypt inahitaji DNS-01 challenge. Mfano kama
DNS iko Cloudflare:

```bash
sudo apt install -y certbot python3-certbot-dns-cloudflare
sudo install -d -m 700 /root/.secrets
sudo nano /root/.secrets/cloudflare.ini
```

Weka token yenye Zone:DNS:Edit scope:

```ini
dns_cloudflare_api_token = CLOUDFLARE_API_TOKEN
```

```bash
sudo chmod 600 /root/.secrets/cloudflare.ini
sudo certbot certonly --dns-cloudflare \
  --dns-cloudflare-credentials /root/.secrets/cloudflare.ini \
  -d example.co.tz -d '*.example.co.tz'
sudo ln -s /etc/nginx/sites-available/shuleplus /etc/nginx/sites-enabled/shuleplus
sudo nginx -t
sudo systemctl reload nginx
sudo certbot renew --dry-run
```

Kama DNS provider ni tofauti, tumia Certbot DNS plugin yake badala ya
`certbot-dns-cloudflare`. Usitumie HTTP-01 kwa wildcard.

Baada ya HTTPS kufanya kazi, hakikisha URL ya landing page, `www`, na subdomain
ya shule inafunguka. `DJANGO_DEBUG=False`, `ALLOWED_HOSTS`,
`CSRF_TRUSTED_ORIGINS`, na `BASE_DOMAIN` lazima zilingane na domain yako.

Ingia `https://example.co.tz/admin/` kwa superuser uliyotengeneza, ongeza
rekodi ya shule kwenye **Schools**, kisha tumia subdomain iliyowekwa kwenye
rekodi hiyo, kwa mfano `https://sehisco.example.co.tz/`. Hakikisha DNS wildcard
inaelekea kwenye server na jina la subdomain linalingana kabisa na rekodi ya
shule.

## Backfill ya mara moja kwa matokeo ya A-Level

Baada ya deploy ya code yenye marekebisho ya A-Level, kagua idadi ya rekodi
zitakazobadilishwa kisha endesha backfill. Command inaweka combination ya
mwanafunzi kwenye rekodi za A-Level ambazo combination bado ni `NULL`.

```bash
sudo -u ubuntu bash -c 'set -a; . /etc/shuleplus.env; set +a; cd /home/ubuntu/shuleplus_erp && ./venv/bin/python manage.py backfill_a_level_result_combinations --dry-run'
sudo -u ubuntu bash -c 'set -a; . /etc/shuleplus.env; set +a; cd /home/ubuntu/shuleplus_erp && ./venv/bin/python manage.py backfill_a_level_result_combinations'
```

## 7. Ukaguzi, update na backup

```bash
sudo -u ubuntu bash -c 'set -a; . /etc/shuleplus.env; set +a; cd /home/ubuntu/shuleplus_erp && ./venv/bin/python manage.py check --deploy'
sudo journalctl -u shuleplus -f
```

Kwa kila update ya code:

```bash
cd /home/ubuntu/shuleplus_erp
git pull
./venv/bin/pip install -r requirements.txt
sudo -u ubuntu bash -c 'set -a; . /etc/shuleplus.env; set +a; cd /home/ubuntu/shuleplus_erp && ./venv/bin/python manage.py migrate'
sudo -u ubuntu bash -c 'set -a; . /etc/shuleplus.env; set +a; cd /home/ubuntu/shuleplus_erp && ./venv/bin/python manage.py collectstatic --noinput'
sudo systemctl restart shuleplus
```

Sanidi `deploy/backup.sh` kwa database name/user na media path sahihi. Weka
PostgreSQL password kwenye `/home/ubuntu/.pgpass`:

```bash
nano /home/ubuntu/.pgpass
```

Weka mstari huu na password halisi ya database, kisha:

```text
*:*:shulepluserp_db:shule_user:PASSWORD
```

```bash
chmod 600 /home/ubuntu/.pgpass
mkdir -p /home/ubuntu/backups
chmod 700 /home/ubuntu/backups
chmod +x /home/ubuntu/shuleplus_erp/deploy/backup.sh
crontab -e
```

Ongeza cron ya backup ya kila siku:

```cron
0 2 * * * /home/ubuntu/shuleplus_erp/deploy/backup.sh >> /home/ubuntu/backup.log 2>&1
```

Jaribu `deploy/backup.sh` kwa mkono na ujaribu `deploy/restore.sh` kwenye
mazingira ya majaribio kabla ya kutegemea backup. Backup ibaki pia nje ya VPS.
