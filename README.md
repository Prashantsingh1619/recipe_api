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
