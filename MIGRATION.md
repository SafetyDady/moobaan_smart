# Moobaan Smart — คู่มือย้าย PC

คู่มือนี้ใช้สำหรับย้ายโปรเจกต์ไปยัง PC เครื่องใหม่ ไม่กระทบ production deploy (Railway/Vercel ยัง auto-deploy ตามปกติเมื่อ push)

## ภาพรวม

**Code:** อยู่บน [GitHub](https://github.com/SafetyDady/moobaan_smart) แล้ว → clone ใหม่บน PC เครื่องใหม่
**Secrets ตัวจริง:** อยู่บน Railway/Vercel dashboard — ไม่อยู่ในไฟล์ local
**สิ่งที่ต้องย้ายจริงๆ:** มีแค่ 2 ไฟล์ `.env` เล็กๆ + (optional) `.claude/`

---

## ขั้นตอนย้าย — บน PC เครื่องเก่า

### 1. ตรวจสอบว่า commit ทุกอย่างขึ้น GitHub แล้ว

```bash
cd C:\web_project\moobaan_smart
git status                    # ควรเห็น "nothing to commit, working tree clean"
git log origin/master..HEAD   # ไม่มี output = sync แล้ว
```

ถ้ามี changes ค้าง → commit + push ก่อน

### 2. รัน migration bundle (สร้าง zip ที่มีไฟล์สำคัญ)

```powershell
.\migrate-bundle.ps1
```

จะได้ไฟล์ `moobaan-smart-migration-YYYYMMDD.zip` (ขนาดเล็กมาก ~10 KB)
ภายในมี:
- `backend/.env`
- `frontend/.env`
- `.claude/settings.local.json`
- `MIGRATION.md` (ไฟล์นี้)

### 3. โอน zip ไป PC ใหม่

เลือกอย่างใดอย่างหนึ่ง:
- **USB drive** (เร็วและปลอดภัยที่สุด)
- **OneDrive / Google Drive** (sync เฉพาะไฟล์ zip — อย่า sync ทั้งโฟลเดอร์โปรเจกต์)
- **Password manager** (Bitwarden/1Password — แนะนำสำหรับ .env)

> 🔒 **เคล็ดลับความปลอดภัย:** ถ้าใส่ OneDrive — zip + password ก่อน (7-Zip/WinRAR)

---

## ขั้นตอนติดตั้ง — บน PC เครื่องใหม่

### 1. ติดตั้งเครื่องมือพื้นฐาน

| เครื่องมือ | เวอร์ชั่นแนะนำ | ลิงก์ |
|------------|----------------|-------|
| Git | ล่าสุด | https://git-scm.com/ |
| Node.js | 18+ หรือ 20+ | https://nodejs.org/ |
| Python | 3.11 | https://www.python.org/ |
| PostgreSQL | 14+ (ถ้าจะรัน local DB) | https://www.postgresql.org/ |

### 2. Clone โปรเจกต์จาก GitHub

```bash
cd C:\web_project
git clone https://github.com/SafetyDady/moobaan_smart.git
cd moobaan_smart
```

### 3. แตก zip ไฟล์ migration วาง .env กลับ

จาก zip ที่ย้ายมา:
- Copy `backend/.env` → `C:\web_project\moobaan_smart\backend\.env`
- Copy `frontend/.env` → `C:\web_project\moobaan_smart\frontend\.env`
- Copy `.claude/` (ทั้งโฟลเดอร์) → `C:\web_project\moobaan_smart\.claude\` (optional)

### 4. ติดตั้ง dependencies

**Backend:**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Frontend:**
```bash
cd ..\frontend
npm install
```

### 5. ตั้งค่า Database (ถ้าจะรัน local)

```bash
# สร้าง DB ใน PostgreSQL
psql -U postgres -c "CREATE DATABASE moobaan_smart;"

# รัน migrations (จาก backend/)
cd ..\backend
.venv\Scripts\activate
alembic upgrade head
```

> 💡 **ทางลัด:** ถ้าไม่อยากรัน local DB เลย ให้ใช้ Railway DB ตรงๆ — แก้ `DATABASE_URL` ใน `backend/.env` เป็น URL จาก Railway (Settings → Variables → DATABASE_URL)

### 6. รันทดสอบ

**Backend** (terminal แรก):
```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload
# เปิด http://localhost:8000/docs ดู API
```

**Frontend** (terminal สอง):
```bash
cd frontend
npm run dev
# เปิด http://localhost:5173
```

### 7. ตั้งค่า Git author (ถ้ายังไม่ได้)

```bash
git config --global user.email "sanchai5651@gmail.com"
git config --global user.name "ชื่อของคุณ"
```

### 8. ตั้งค่า Git credentials (ถ้า push ครั้งแรก)

GitHub ใช้ Personal Access Token (PAT) แทน password:
1. ไปที่ https://github.com/settings/tokens
2. Generate new token (classic) → ติ๊ก `repo`
3. Copy token เก็บไว้
4. ครั้งแรกที่ `git push` Windows Credential Manager จะถาม → ใส่ token เป็น password

### 9. (Optional) ตั้งค่า IDE

- **VS Code:** เปิด `C:\web_project\moobaan_smart\` แล้วติดตั้ง extensions ที่ใช้บ่อย:
  - Python (Microsoft)
  - ESLint
  - Tailwind CSS IntelliSense
  - GitLens
- **Cursor / Windsurf / Claude Code:** เปิดโปรเจกต์ → จะอ่าน `CLAUDE.md` อัตโนมัติ

---

## สิ่งที่ **ไม่ต้อง** ย้าย (rebuild ได้ทั้งหมด)

- `node_modules/` (300+ MB) — `npm install` สร้างใหม่ได้
- `.venv/` — `pip install` สร้างใหม่ได้
- `__pycache__/`, `.pytest_cache/`, `dist/`, `build/` — generate ใหม่อัตโนมัติ
- `.vercel/`, `.vite/` — สร้างเมื่อรันคำสั่ง Vercel/Vite ครั้งแรก

---

## Production Secrets

ทั้งหมดอยู่บน dashboard ของ Railway/Vercel — ไม่ต้องย้าย:

- **Railway (backend):** https://railway.app/ → moobaan_smart_production → Settings → Variables
  - `DATABASE_URL`, `SECRET_KEY`, `R2_*`, `LINE_*`, `SMSMKT_*` ฯลฯ
- **Vercel (frontend):** https://vercel.com/ → moobaan-smart → Settings → Environment Variables
  - `VITE_API_BASE_URL`, `VITE_APP_URL`

ถ้าจำเป็นต้องดู — login dashboard ผ่าน browser ปกติ

---

## User Memory (Claude Code) — Optional

ถ้าใช้ Claude Code และต้องการเก็บ memory ของคุณ (settings, plans, conversation history):

```
C:\Users\sanch\.claude\
```

โฟลเดอร์นี้มี:
- `memory/` — บันทึก preference ที่สอนไปแล้ว (เรื่อง slip URL via proxy, hardcode static data, etc.)
- `plans/` — เก็บ implementation plans
- `projects/` — transcript ของ conversation ทั้งหมด

**ขนาด:** อาจหลายร้อย MB — เลือกย้ายเฉพาะ `memory/` ก็พอ

---

## Checklist สุดท้าย

PC เก่า:
- [ ] `git status` clean + `git push` ทุกอย่างขึ้น GitHub
- [ ] รัน `migrate-bundle.ps1` ได้ zip
- [ ] โอน zip ไปที่ปลอดภัย

PC ใหม่:
- [ ] ติดตั้ง Git, Node.js, Python, (PostgreSQL)
- [ ] Clone repo จาก GitHub
- [ ] วาง `.env` 2 ไฟล์กลับที่
- [ ] `pip install -r requirements.txt`
- [ ] `npm install`
- [ ] `alembic upgrade head`
- [ ] Backend รันได้ (`uvicorn`)
- [ ] Frontend รันได้ (`npm run dev`)
- [ ] เปิดหน้า login ได้

เสร็จแล้ว → ลบ zip ออกจาก USB/cloud เพื่อความปลอดภัย
