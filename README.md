# 🍽️ Recipe Recommender — Flask API

A content-based recipe recommendation API built with Flask, TF-IDF, and cosine similarity.

---

## 📁 Project Structure

```
recipe_api/
├── app.py               ← Flask API
├── final_Datasets.csv   ← Your dataset
├── requirements.txt
├── Procfile             ← For Render / Railway
└── README.md
```

---

## 🚀 Run Locally

```bash
pip install -r requirements.txt
python app.py
```

API will be live at `http://localhost:5000`

---

## 🌐 Deploy Online for FREE

### Option 1 — Render.com (Recommended, easiest)

1. Push your project to GitHub (include the CSV file)
2. Go to https://render.com → Sign up free
3. Click **New → Web Service**
4. Connect your GitHub repo
5. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Free
6. Click **Deploy** — your API will be live at `https://your-app.onrender.com`

> ⚠️ Free tier spins down after inactivity (cold start ~30s). Upgrade for always-on.

---

### Option 2 — Railway.app

1. Go to https://railway.app → Sign up with GitHub
2. Click **New Project → Deploy from GitHub repo**
3. Railway auto-detects the `Procfile` and deploys
4. Free tier gives $5/month credit (enough for small APIs)

---

### Option 3 — PythonAnywhere (100% free tier)

1. Go to https://www.pythonanywhere.com → Sign up free
2. Upload your files via the **Files** tab
3. Go to **Web** tab → Add a new web app → Flask
4. Set the path to `app.py`
5. Install requirements in the **Bash console:**
   ```bash
   pip install flask pandas scikit-learn --user
   ```
6. Reload the web app — live at `https://yourusername.pythonanywhere.com`

> ⚠️ Free tier only: no outbound internet from the app, 512MB storage, 100s CPU/day.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info & all endpoints |
| GET | `/recipes?page=1&per_page=20` | Paginated list of all recipes |
| GET | `/recipe/<name>` | Full details of one recipe |
| GET | `/recommend?dish=<name>&location=Punjab&diet=Vegetarian` | Content-based recommendations |
| GET | `/recommend/onboarding?state=Punjab&diet=Vegetarian&goal=weight_loss` | First-time user recommendations |
| GET | `/search?q=paneer` | Search recipes by name |

---

## 🔧 Example Requests

```bash
# Get recommendations for a dish
curl "http://localhost:5000/recommend?dish=Butter+Chicken&location=Punjab&n=5"

# Onboarding recommendations
curl "http://localhost:5000/recommend/onboarding?state=South+India&diet=Vegetarian&goal=high_protein"

# Search
curl "http://localhost:5000/search?q=dal"
```

---

## 📦 onboarding `goal` values

| goal | Description |
|------|-------------|
| `weight_loss` | Low calorie dishes |
| `weight_gain` | High calorie dishes |
| `high_protein` | Max protein dishes |
| `lean_muscle` | High protein-to-calorie ratio |
| `general` | Location-boosted, no goal filter |
