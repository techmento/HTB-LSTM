# Windows Setup Guide — Marine Machinery Fault Detection Dashboard

This guide walks through setting up the whole project (backend + frontend) on a **fresh Windows computer that has nothing installed yet**. Follow the steps in order.

---

## 1. Install Prerequisites

### 1.1 Python 3.10

This project's ML libraries (TensorFlow specifically) require **Python 3.10**. A newer version (e.g. 3.12+, 3.13, 3.14) will fail to install TensorFlow.

1. Go to **python.org** → Downloads → look for **Python 3.10.x** (not the latest version shown by default — you may need "View the full list of downloads" to find 3.10).
2. Run the installer. **Important:** on the first install screen, check the box **"Add python.exe to PATH"** before clicking Install.
3. Verify it worked — open **Command Prompt** (search "cmd" in the Start menu) and run:
   ```
   python --version
   ```
   It should print `Python 3.10.x`. If it prints a different version (e.g. 3.12) and you already have another Python installed, use `py -3.10` instead of `python` in the commands below.

### 1.2 Node.js (for the frontend)

1. Go to **nodejs.org** and download the **LTS** version (the recommended one, not "Current").
2. Run the installer with default options.
3. Verify:
   ```
   node --version
   npm --version
   ```

### 1.3 (Optional) Git

Only needed if you're getting the project via `git clone` rather than copying the folder directly. Download from **git-scm.com** if needed.

---

## 2. Get the Project Onto the Machine

Copy the whole `HTB-LSTM` project folder onto the Windows machine (via USB drive, zip file, `git clone`, cloud sync, etc.). Note where you put it — this guide assumes it's at:

```
C:\Users\<YourName>\Desktop\HTB-LSTM
```

Adjust the path in the commands below if you put it somewhere else.

---

## 3. Backend Setup

Open **Command Prompt** and run these one at a time.

### 3.1 Navigate to the backend folder

```
cd C:\Users\<YourName>\Desktop\HTB-LSTM\backend
```

### 3.2 Create the virtual environment

```
python -m venv .venv
```

(If your default `python` is not 3.10, use `py -3.10 -m venv .venv` instead.)

### 3.3 Activate the virtual environment

**In Command Prompt:**
```
.venv\Scripts\activate.bat
```

**In PowerShell instead**, use:
```
.venv\Scripts\Activate.ps1
```

If PowerShell blocks this with a script-execution error, run this once (as a normal user, not Administrator) and try again:
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

You'll know it worked when the prompt shows `(.venv)` at the start of the line.

### 3.4 Install Python dependencies

```
pip install -r requirements.txt
```

This installs numpy, pandas, scikit-learn, matplotlib, seaborn, joblib, tensorflow, fastapi, uvicorn, python-multipart, and openpyxl. This step can take several minutes (TensorFlow is large).

### 3.5 Train the models (first time only)

These scripts read `data/processed/sealine_data_with_features.csv` and write trained model files into `ml/models/`. Run them **in this order**:

```
python ml/train_rf.py
python ml/train_lstm.py
python ml/train_hybrid.py
python ml/evaluate_all.py
```

- `train_rf.py` trains the Random Forest (fast, a few seconds).
- `train_lstm.py` trains the LSTM (slower — a couple of minutes, prints accuracy/recall at the end).
- `train_hybrid.py` compares RF vs LSTM vs Hybrid on the same test rows (no new files saved, just printed output).
- `evaluate_all.py` is the important one — it grid-searches the best RF/LSTM weighting for the hybrid model, saves `ml/models/evaluation_results.json` (which the dashboard reads for the "Model Performance" section) and `ml/models/roc_comparison.png`.

You should see `rf_model.pkl`, `lstm_model.keras`, `lstm_scaler.pkl`, `evaluation_results.json`, and `evaluation_comparison.csv` appear inside `backend\ml\models\` once these finish.

### 3.6 Start the backend server

```
uvicorn app.main:app --reload
```

Leave this window open — it needs to keep running. You should see:
```
Uvicorn running on http://127.0.0.1:8000
```

The first time it starts, it automatically creates `backend\app\dashboard.db` (a SQLite file) and seeds a default login account:

```
Username: admin
Password: admin123
```

(You can change the default password by setting an environment variable **before** the first run — `set DASHBOARD_ADMIN_PASSWORD=yourpassword` in Command Prompt, then start uvicorn in that same window. This only matters the very first time, since after that the account already exists in the database.)

---

## 4. Frontend Setup

Open a **second** Command Prompt window (leave the backend one running in the first).

### 4.1 Navigate to the frontend folder

```
cd C:\Users\<YourName>\Desktop\HTB-LSTM\frontend
```

### 4.2 Install dependencies

```
npm install
```

### 4.3 Start the frontend

```
npm run dev
```

You should see:
```
Local:   http://localhost:5173/
```

---

## 5. Open the Dashboard

Open a browser and go to:
```
http://localhost:5173
```

Log in with:
```
Username: admin
Password: admin123
```

---

## 6. Running It Again Later (After the First Setup)

You don't need to repeat the training or `npm install` steps every time — only when the code/models change. For normal day-to-day use:

**Backend** (Command Prompt #1):
```
cd C:\Users\<YourName>\Desktop\HTB-LSTM\backend
.venv\Scripts\activate.bat
uvicorn app.main:app --reload
```

**Frontend** (Command Prompt #2):
```
cd C:\Users\<YourName>\Desktop\HTB-LSTM\frontend
npm run dev
```

---

## 7. Common Windows Issues

| Problem | Fix |
|---|---|
| `python` command not found | Python wasn't added to PATH during install. Reinstall and check "Add python.exe to PATH", or use the full path to `python.exe`. |
| `pip install` fails on tensorflow | Check `python --version` inside the activated venv — if it's not 3.10.x, the venv was created with the wrong Python version. Delete the `.venv` folder and recreate it with `py -3.10 -m venv .venv`. |
| PowerShell won't activate the venv | Use `.venv\Scripts\activate.bat` in plain Command Prompt instead of PowerShell, or run the `Set-ExecutionPolicy` command from step 3.3. |
| `uvicorn` command not found | The venv isn't activated — you should see `(.venv)` at the start of the prompt. Re-run `.venv\Scripts\activate.bat`. |
| Port 8000 or 5173 already in use | Another instance is already running. Close the old Command Prompt window, or find and stop the process using that port. |
| Dashboard loads but shows no dataset stats / login fails | Make sure the backend Command Prompt window is still open and shows no errors — if it crashed, dataset/model calls will fail. |
| Forgot the admin password | Stop the backend, delete `backend\app\dashboard.db`, and restart `uvicorn` — a fresh database with a new default admin account (`admin` / `admin123`, or your custom `DASHBOARD_ADMIN_PASSWORD`) will be created. **Note: this also deletes all saved prediction history.** |
