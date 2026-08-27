# Mwongozo wa GitHub kwa ShulePlusERP (Windows)

## Awamu 1: Install Git kwenye Windows
1. Pakua kutoka https://git-scm.com/download/win
2. Install na chaguo za default (bonyeza "Next" hadi mwisho)
3. Fungua PowerShell mpya, jaribu:
   ```powershell
   git --version
   ```
   Ikionyesha namba ya version, uko tayari.

## Awamu 2: Weka Utambulisho Wako (mara moja tu)
```powershell
git config --global user.name "Jina Lako"
git config --global user.email "email@yako.com"
```

## Awamu 3: Tengeneza Akaunti + Repository kwenye GitHub
1. Fungua https://github.com, jisajili (bure)
2. Bonyeza **"+"** juu kulia → **New repository**
3. Jina: `shuleplus-erp`
4. **Muhimu:** Chagua **Private** (siyo Public) — mradi wako una taarifa za biashara/malengo ya kibiashara, na hata bila `media/`, code yenyewe (design ya bei, model za data za shule) ni bora ibaki faragha mpaka utakapoamua vinginevyo
5. USIWEKE tick kwenye "Add README" (tutaleta yetu wenyewe)
6. Bonyeza **Create repository** — GitHub itakuonyesha amri, lakini fuata hizi hapa chini badala yake (zinakamilika zaidi)

## Awamu 4: Weka .gitignore Mahali Pake
Nakili faili ya `.gitignore` niliyokutengenezea kwenye **mzizi (root)** wa folder yako ya project (sehemu moja na `manage.py`).

**Hii ni muhimu SANA kabla ya `git add` yoyote** — bila hii, unaweza kupakia kimakosa:
- `.env` (SECRET_KEY, database password, Beem API keys)
- `media/` (picha/risiti/taarifa za wanafunzi halisi - baadhi ni watoto)
- `venv/` (folder kubwa isiyo na maana kwa wengine)

## Awamu 5: Anzisha Git kwenye Project Yako
Kwenye PowerShell, nenda kwenye folder ya project:
```powershell
cd C:\Path\ya\shuleplus_erp
git init
git add .
git status
```
Kabla ya `git commit`, angalia matokeo ya `git status` — **hakikisha `.env` na `media/` HAZIONEKANI** kwenye orodha ya "Changes to be committed". Zikionekana, `.gitignore` yako haiko mahali pazuri au jina si sahihi — simama, niambie, tusuluhishe kabla ya kuendelea.

```powershell
git commit -m "Awali - ShulePlusERP mfumo kamili"
git branch -M main
git remote add origin https://github.com/<jina-lako>/shuleplus-erp.git
git push -u origin main
```

GitHub itakuomba uingie (username + Personal Access Token, siyo password ya kawaida tena tangu 2021):
1. GitHub → Settings → Developer settings → Personal access tokens → **Generate new token (classic)**
2. Chagua scope: `repo` (tick zote za repo)
3. Nakili token (itaonyesha mara moja tu - iandike mahali salama)
4. Wakati PowerShell inakuomba password, bandika hiyo token (siyo password yako ya GitHub)

## Awamu 6: Baada ya Kupush
- Angalia https://github.com/<jina-lako>/shuleplus-erp — hakikisha faili zote muhimu zipo, na `.env`/`media/` HAZIPO kabisa kwenye listing
- Kwa mabadiliko yajayo (bug fix, feature mpya), badala ya kurudia yote:
  ```powershell
  git add .
  git commit -m "Maelezo mafupi ya mabadiliko"
  git push
  ```

## Awamu 7 (Baadaye): Kutumia Git Kwenye Deployment (Oracle)
Ukishafika kwenye Awamu 4 ya mwongozo wa deployment (badala ya SCP), sasa unaweza:
```bash
git clone https://github.com/<jina-lako>/shuleplus-erp.git shuleplus_erp
```
Na kwa update zijazo za server, badala ya kupakia upya kila kitu:
```bash
cd /home/ubuntu/shuleplus_erp
git pull
sudo systemctl restart shuleplus
```

---

## Angalizo la Usalama (soma kabla ya kupush)
- Kama tayari umewahi ku-`git add .env` bila kutaka kwenye jaribio la awali, futa historia hiyo kabisa kabla ya kupush hadharani — token/password iliyowahi kuonekana kwenye git history inahitaji kubadilishwa mara moja (siyo kufutwa tu), kwa sababu commit za zamani zinabaki kwenye historia hata ukiifuta faili baadaye
- Kama huna uhakika kama `.env` "imeshaingia" kwenye git tayari kabla ya kuweka `.gitignore`, niambie kabla ya `git push` ili tukague kwanza
