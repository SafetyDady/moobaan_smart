# 🚀 Deployment Guide - Moobaan Smart

คู่มือการ Deploy ระบบ Moobaan Smart ขึ้น Production

## 📋 ภาพรวม Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Vercel       │────▶│    Railway      │────▶│    Railway      │
│   (Frontend)    │     │   (Backend)     │     │  (PostgreSQL)   │
│   React + Vite  │     │   FastAPI       │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Cloudflare R2    │
                    │ (Object Storage)  │
                    │  Invoice/Receipt  │
                    └─────────────────┘
```

---

## 🗄️ ขั้นตอนที่ 1: Railway - PostgreSQL Database

### 1.1 สร้าง Project ใหม่บน Railway

1. ไปที่ [railway.app](https://railway.app) และ Login
2. Click **"New Project"**
3. เลือก **"Provision PostgreSQL"**
4. รอให้ Database ถูกสร้าง (ประมาณ 30 วินาที)

### 1.2 Get Database Connection String

1. Click ที่ PostgreSQL service
2. ไปที่ tab **"Variables"** หรือ **"Connect"**
3. Copy `DATABASE_URL` ซึ่งจะมีรูปแบบ:
   ```
   postgresql://postgres:password@host:port/railway
   ```

### 1.3 ⚠️ สำคัญ: แปลง URL Format

เนื่องจาก Backend ใช้ **psycopg v3** ต้องแปลง URL เป็น:

```
postgresql+psycopg://postgres:password@host:port/railway
```

**เพิ่ม `+psycopg` หลัง `postgresql`**

---

## 🔧 ขั้นตอนที่ 2: Railway - Backend (FastAPI)

### 2.1 เตรียม Repository

ตรวจสอบว่า code อยู่บน GitHub แล้ว:

```bash
cd c:\web_project\moobaan_smart
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### 2.2 สร้าง Backend Service บน Railway

1. ใน Project เดียวกันกับ Database, click **"New"** → **"GitHub Repo"**
2. เลือก Repository `moobaan_smart`
3. ตั้งค่า **Root Directory** เป็น: `backend`

### 2.3 ตั้งค่า Environment Variables

ไปที่ tab **"Variables"** ของ Backend service และเพิ่ม:

| Variable | Value | หมายเหตุ |
|----------|-------|---------|
| `DATABASE_URL` | `postgresql+psycopg://postgres:xxx@xxx/railway` | **ต้องมี +psycopg** |
| `APP_NAME` | `moobaan_smart_backend` | |
| `ENV` | `production` | |
| `SECRET_KEY` | `<generate-random-64-chars>` | ⚠️ ต้อง generate ใหม่! |
| `PORT` | `${{PORT}}` | Railway จะ inject อัตโนมัติ |
| `R2_ACCOUNT_ID` | `<cloudflare-account-id>` | Cloudflare R2 |
| `R2_ACCESS_KEY_ID` | `<r2-access-key>` | R2 API Token |
| `R2_SECRET_ACCESS_KEY` | `<r2-secret-key>` | R2 API Token |
| `R2_BUCKET_NAME` | `moobaan-smart-production` | R2 bucket name |
| `R2_ENDPOINT` | `https://<account-id>.r2.cloudflarestorage.com` | R2 S3-compatible endpoint |
| `R2_PUBLIC_URL` | `https://pub-xxx.r2.dev` | Public read URL (r2.dev domain) |

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2.4 Railway Settings

ไปที่ **Settings** tab:

1. **Build Command**: *(ปล่อยว่าง - ใช้ Dockerfile)*
2. **Start Command**: *(ปล่อยว่าง - ใช้ Dockerfile CMD)*
3. **Watch Paths**: `backend/**`

### 2.5 Verify Deployment

หลัง deploy สำเร็จ:
1. Click **"Generate Domain"** เพื่อได้ URL เช่น `https://moobaan-smart-backend-production.up.railway.app`
2. ทดสอบ: `https://your-domain/health`

---

## 🎨 ขั้นตอนที่ 3: Vercel - Frontend (React + Vite)

### 3.1 ตั้งค่า Project บน Vercel

1. ไปที่ [vercel.com](https://vercel.com) และ Login
2. Click **"Add New..."** → **"Project"**
3. Import Repository `moobaan_smart`

### 3.2 Configure Build Settings

| Setting | Value |
|---------|-------|
| **Framework Preset** | Vite |
| **Root Directory** | `frontend` |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |
| **Install Command** | `npm install` |

### 3.3 Environment Variables

ไปที่ **Settings** → **Environment Variables**:

| Variable | Value |
|----------|-------|
| `VITE_API_BASE_URL` | `https://your-backend.up.railway.app` |

**⚠️ สำคัญ:** 
- ไม่ต้องใส่ `/` ตรงท้าย URL
- ใช้ HTTPS

### 3.4 Deploy

Click **"Deploy"** และรอประมาณ 1-2 นาที

---

## 🔒 ขั้นตอนที่ 4: Update CORS (Backend)

หลังได้ Vercel URL แล้ว ต้องเพิ่มใน CORS allowed origins:

### อัพเดท `backend/app/main.py`:

```python
allow_origins=[
    # Development
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # Production - Vercel
    "https://moobaan-smart.vercel.app",
    "https://your-custom-domain.vercel.app",  # เพิ่ม URL จริงของคุณ
],
```

---

## 🗃️ ขั้นตอนที่ 5: Database Migration

### 5.1 Run Initial Migration

วิธีที่ 1: **ผ่าน Railway CLI**
```bash
npm install -g @railway/cli
railway login
railway link
railway run alembic upgrade head
```

วิธีที่ 2: **ผ่าน Railway Shell**
1. ไปที่ Backend service บน Railway
2. Click **"Connect"** → **"Shell"**
3. Run:
```bash
alembic upgrade head
```

วิธีที่ 3: **เพิ่มใน Dockerfile** (แนะนำ)

อัพเดท `backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

EXPOSE ${PORT:-8000}

# Run migration then start server
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### 5.2 Seed Initial Data (ถ้าต้องการ)

สร้าง script สำหรับ seed production data:
```bash
railway run python seed_users.py
```

---

## ✅ ขั้นตอนที่ 6: Verification Checklist

### Backend Health Check
```bash
curl https://your-backend.up.railway.app/health
```
Expected: `{"status": "healthy"}`

### Frontend Test
1. เปิด `https://your-app.vercel.app`
2. ทดสอบ Login
3. ตรวจสอบ Network tab ว่า API calls ถูกต้อง

### Database Connection
```bash
curl https://your-backend.up.railway.app/api/houses
```

---

## 🔧 Files ที่ต้องสร้าง/แก้ไข

### 1. `vercel.json` (สร้างใหม่ใน frontend/)

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/" }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" }
      ]
    }
  ]
}
```

### 2. `railway.json` (สร้างใหม่ใน backend/)

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

---

## 🐛 Troubleshooting

### ปัญหา: CORS Error
**วิธีแก้:** เพิ่ม Vercel URL ใน `allow_origins` ของ backend

### ปัญหา: Database Connection Failed
**วิธีแก้:** 
1. ตรวจสอบ `DATABASE_URL` มี `+psycopg` 
2. ตรวจสอบ Railway PostgreSQL service กำลังทำงาน

### ปัญหา: 404 on Page Refresh (Vercel)
**วิธีแก้:** เพิ่ม `vercel.json` กับ rewrites configuration

### ปัญหา: Build Failed
**วิธีแก้:** ตรวจสอบ logs บน Railway/Vercel Dashboard

---

## 💰 Cost Estimation

| Service | Free Tier | Paid |
|---------|-----------|------|
| **Vercel** | ✅ Unlimited for hobby | $20/mo Pro |
| **Railway** | $5 free credit/month | Pay-as-you-go |
| **PostgreSQL (Railway)** | Included in $5 | ~ $5-20/mo |
| **Cloudflare R2** | ✅ 10GB storage + 1M class A ops/mo | $0.015/GB/mo |

**สำหรับ Project ขนาดเล็ก:** ใช้ได้ฟรี หรือ < $10/เดือน

---

## 📝 Quick Reference

| Component | URL |
|-----------|-----|
| Frontend (Vercel) | `https://moobaan-smart.vercel.app` |
| Backend (Railway) | `https://moobaan-smart-backend.up.railway.app` |
| Railway Dashboard | `https://railway.app/dashboard` |
| Vercel Dashboard | `https://vercel.com/dashboard` |

---

## 🚀 Deploy Commands Summary

```bash
# 1. Push to GitHub
git add .
git commit -m "Deploy to production"
git push origin main

# 2. Railway will auto-deploy from GitHub

# 3. Vercel will auto-deploy from GitHub

# 4. Run migrations (if needed)
railway run alembic upgrade head
```

---

*อัพเดทล่าสุด: February 2026*
