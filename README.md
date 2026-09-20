# 🐝 MONEY For HONEY — Autonomous Quantitative Trading & Self-Wealth Engine

> **Tagline:** Autonomous Trading System & Self Wealth Engine for the Future.  
> **Architecture:** FastAPI (Python 3.11+, CCXT, SQLite WAL / PostgreSQL) + React 18 (Vite, TypeScript, Tailwind CSS, Lucide Icons).

---

## 🚀 Panduan Pengembangan di Visual Studio Code (VS Code Setup)

Proyek ini telah dikonfigurasi secara lengkap dengan template bawaan `.vscode/` agar Anda dapat langsung melanjutkan pengembangan dengan satu klik (*out-of-the-box*).

### 1. Prasyarat Sistem
* **Python**: Versi 3.10, 3.11, atau 3.12
* **Node.js**: Versi 18+ atau 20+ LTS
* **VS Code**: Disarankan memasang ekstensi rekomendasi (akan otomatis diminta oleh VS Code sesuai `.vscode/extensions.json`):
  * *Python* & *Debugpy* (`ms-python.python`)
  * *Ruff* (`charliermarsh.ruff`)
  * *ESLint* & *Prettier*
  * *Tailwind CSS IntelliSense*

---

### 2. Langkah Instalasi Cepat (Quick Start)

#### A. Konfigurasi Lingkungan Backend (Python)
Buka terminal terintegrasi di VS Code (`Ctrl + ~` atau `Cmd + ~`):
```bash
# 1. Buat Virtual Environment Python
python3 -m venv .venv

# 2. Aktifkan Virtual Environment
# Linux / macOS:
source .venv/bin/activate
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# 3. Instal dependensi kuantitatif (FastAPI, CCXT, Pandas, Pydantic, dsb.)
pip install -r requirements.txt
```

#### B. Konfigurasi Lingkungan Frontend (React + Vite)
```bash
# Instal dependensi UI (Tailwind, Lucide, Motion, dsb.)
npm install
```

#### C. Konfigurasi File Environment `.env`
Salin template konfigurasi:
```bash
cp .env.example .env
```
Buka `.env` dan atur parameter utama Anda:
* `TESTNET_MODE=true` (Gunakan mode Testnet terlebih dahulu untuk keamanan)
* `STRICT_PRODUCTION_MODE=false` (Gunakan `true` hanya jika siap trading uang riil dengan API Key valid)
* `BINANCE_API_KEY` & `BINANCE_API_SECRET`
* `TELEGRAM_BOT_TOKEN` & `TELEGRAM_CHAT_ID`
* `TELEGRAM_WEBHOOK_SECRET` (Token otentikasi webhook Telegram)

---

### 3. Menjalankan & Men-debug Proyek di VS Code (F5 One-Click Run)

1. Buka tab **Run and Debug** di sisi kiri VS Code (`Ctrl + Shift + D` atau `Cmd + Shift + D`).
2. Pilih profile **"Full Stack: Backend & Frontend"** dari dropdown atas.
3. Tekan **F5** atau klik tombol hijau Play ▶️.
   * VS Code akan otomatis menjalankan **FastAPI Backend di port 8000** dan **Vite Frontend di port 3000** secara bersamaan.
   * Debugger breakpoints pada file Python maupun TypeScript akan langsung aktif!

#### Menjalankan Lewat Terminal / Tasks VS Code:
Tekan `Ctrl + Shift + P` -> pilih **Tasks: Run Task**:
* `3. Run: FastAPI Backend Server (Uvicorn)` -> Meluncurkan server backend
* `4. Run: React Dashboard Dev Server (Vite)` -> Meluncurkan antarmuka web
* `6. Test: Verify Python Compilation` -> Uji sintaksis seluruh file Python
* `7. Test: TypeScript Lint & Compile` -> Uji tipe data & build frontend

---

### 4. Menjalankan Menggunakan Docker Compose (Alternatif)

Jika Anda ingin menjalankan seluruh ekosistem (FastAPI, Redis, PostgreSQL, Nginx) dalam container terisolasi:
```bash
docker-compose up --build -d
```
Akses dashboard di browser Anda: `http://localhost:3000`  
Dokumentasi API Swagger interaktif: `http://localhost:8000/docs`

---

## 🛡️ Fitur Keamanan & Algoritma Produksi

1. **Strict Production Execution Guard**:
   * Menolak *silent paper trading fallback* ketika berada di mode produksi riil (`STRICT_PRODUCTION_MODE=true`).
2. **Atomic Two-Leg Delta-Neutral Execution**:
   * Membuka posisi *Long Spot* dan *Short Perp* dengan proteksi *emergency rollback* instan jika kaki kedua gagal terisi, mencegah *directional leg-risk*.
3. **Dynamic Trailing Stop & Auto Break-Even**:
   * Ratchet otomatis ke Break-Even saat keuntungan mencapai $\ge +1.5R$.
   * Melacak trailing stop berbasis volatilitas pasar riil ($3 \times \text{ATR}_{14}$).
4. **Multi-Timeframe (MTF) Confluence**:
   * Menyaring sinyal 15m/1h terhadap tren makro 4H/1D (EMA 200 & MACD) guna mengeliminasi sinyal palsu (*whipsaw*).
5. **Two-Way Telegram ChatOps**:
   * Pengendalian jarak jauh `/status`, `/emergency_stop`, `/resume`, `/close_all`, dan `/harvest` dengan otorisasi ID Chat operator dan verifikasi header `X-Telegram-Bot-Api-Secret-Token`.
6. **High-Concurrency SQLite WAL**:
   * Mode Write-Ahead Logging (`PRAGMA journal_mode=WAL`) dengan timeout 15 detik untuk menjamin tidak ada kendala *database locked* saat transaksi konkuren tinggi.

---

## 🧪 Pengujian & Verifikasi

Uji kompilasi kode dan integritas tipe:
```bash
# Verifikasi Python
python3 -m py_compile backend/app/main.py backend/app/api/endpoints.py backend/app/core/config.py backend/app/db/database.py backend/app/engine/exchange.py

# Verifikasi TypeScript & Linter
npm run lint
npm run build
```
Semua pemeriksaan teruji lolos 100% tanpa error!
