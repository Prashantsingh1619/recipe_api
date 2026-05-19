from flask import Flask, request, jsonify
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

app = Flask(__name__)

# ──────────────────────────────────────────────
#  1. LOAD & PREPROCESS DATA (runs once on startup)
# ──────────────────────────────────────────────
print("Loading dataset...")
df = pd.read_csv("final_Datasets.csv")
df = df.fillna("")

# Parse nutrition
def parse_nutrition(text):
    try:
        cal   = re.search(r'Calories:\s*(\d+)', str(text))
        prot  = re.search(r'Protein:\s*(\d+)',  str(text))
        return int(cal.group(1)) if cal else 9999, int(prot.group(1)) if prot else 0
    except:
        return 9999, 0

df[["calories", "protein"]] = df["nutrition"].apply(lambda x: pd.Series(parse_nutrition(x)))

# Build TF-IDF + cosine similarity
features = ["name", "ingredients", "description", "cuisine", "diet", "course"]
for f in features:
    df[f] = df[f].fillna("")

df["soup"] = (
    df["name"] + " " +
    df["ingredients"] + " " +
    df["description"] + " " +
    df["cuisine"] + " " +
    df["diet"] + " " +
    df["course"]
)

tfidf       = TfidfVectorizer(stop_words="english")
tfidf_matrix = tfidf.fit_transform(df["soup"])
cosine_sim  = linear_kernel(tfidf_matrix, tfidf_matrix)
indices     = pd.Series(df.index, index=df["name"]).drop_duplicates()

print(f"✅ Loaded {len(df)} recipes — API ready.")

# ──────────────────────────────────────────────
#  2. LOCATION MAP
# ──────────────────────────────────────────────
LOCATION_MAP = {
    "Maharashtra": ["Maharashtrian", "Mumbai", "Konkani"],
    "Punjab":      ["Punjabi", "North Indian"],
    "South India": ["South Indian", "Kerala", "Tamil Nadu", "Karnataka", "Andhra"],
    "Gujarat":     ["Gujarati"],
    "Bengal":      ["Bengali"],
}

# ──────────────────────────────────────────────
#  3. HELPER — serialize a slice of df to JSON
# ──────────────────────────────────────────────
RETURN_COLS = ["name", "cuisine", "diet", "course", "calories", "protein"]

def rows_to_json(slice_df, n=10):
    cols = [c for c in RETURN_COLS if c in slice_df.columns]
    return slice_df[cols].head(n).to_dict(orient="records")

# ──────────────────────────────────────────────
#  4. ROUTES
# ──────────────────────────────────────────────

@app.route("/")
def home():
    return jsonify({
        "message": "🍽️ Recipe Recommender API",
        "endpoints": {
            "GET /recipes":              "List all recipes (name, cuisine, diet, course)",
            "GET /recipe/<name>":        "Get details of a single recipe",
            "GET /recommend":            "Content-based recommendations — ?dish=<name>&location=<loc>&diet=<diet>",
            "GET /recommend/onboarding": "First-time user recs — ?state=<state>&diet=<diet>&gluten_free=true&goal=<goal>",
            "GET /search":               "Search recipes by name — ?q=<query>",
        }
    })


@app.route("/recipes")
def list_recipes():
    """Return all recipe names with basic info."""
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    start    = (page - 1) * per_page
    end      = start + per_page

    cols   = [c for c in ["name", "cuisine", "diet", "course"] if c in df.columns]
    result = df[cols].iloc[start:end].to_dict(orient="records")

    return jsonify({
        "total":   len(df),
        "page":    page,
        "per_page": per_page,
        "recipes": result
    })


@app.route("/recipe/<path:name>")
def get_recipe(name):
    """Return all details for a single recipe."""
    if name not in indices:
        return jsonify({"error": f"Recipe '{name}' not found."}), 404

    idx    = indices[name]
    if isinstance(idx, pd.Series):
        idx = idx.iloc[0]

    record = df.iloc[idx].drop(labels=["soup"], errors="ignore").to_dict()
    return jsonify(record)


@app.route("/recommend")
def recommend():
    """
    Content-based recommendations with optional location boost + diet filter.
    Query params:
        dish      (required) – recipe name
        location  (optional) – e.g. Maharashtra, Punjab
        diet      (optional) – e.g. Vegetarian, Vegan, Gluten Free
        n         (optional) – number of results (default 10)
    """
    dish     = request.args.get("dish", "").strip()
    location = request.args.get("location", "").strip()
    diet     = request.args.get("diet", "").strip()
    n        = int(request.args.get("n", 10))

    if not dish:
        return jsonify({"error": "Missing required param: dish"}), 400

    if dish not in indices:
        return jsonify({"error": f"Recipe '{dish}' not found."}), 404

    idx = indices[dish]
    if isinstance(idx, pd.Series):
        idx = idx.iloc[0]

    sim_scores   = list(enumerate(cosine_sim[idx]))
    loc_keywords = LOCATION_MAP.get(location, [])

    boosted = []
    for i, score in sim_scores:
        if i == idx:
            continue
        if loc_keywords and any(k in df.iloc[i]["cuisine"] for k in loc_keywords):
            score += 0.15
        boosted.append((i, score))

    boosted.sort(key=lambda x: x[1], reverse=True)

    final = []
    for i, _ in boosted:
        recipe_diet = df.iloc[i]["diet"]
        if diet:
            if diet == "Vegetarian":
                if "Vegetarian" not in recipe_diet and "Vegan" not in recipe_diet:
                    continue
            elif diet not in recipe_diet:
                continue
        final.append(i)
        if len(final) >= n:
            break

    return jsonify({
        "dish":          dish,
        "location":      location or None,
        "diet_filter":   diet or None,
        "recommendations": rows_to_json(df.iloc[final], n)
    })


@app.route("/recommend/onboarding")
def onboarding():
    """
    First-time user recommendations based on preferences.
    Query params:
        state        – home state (e.g. Punjab)
        diet         – Vegetarian | Vegan | Non Vegetarian
        gluten_free  – true | false
        goal         – weight_loss | weight_gain | high_protein | lean_muscle | general
        n            – number of results (default 10)
    """
    state       = request.args.get("state", "").strip()
    diet        = request.args.get("diet", "").strip()
    gluten_free = request.args.get("gluten_free", "false").lower() == "true"
    goal        = request.args.get("goal", "general").strip().lower()
    n           = int(request.args.get("n", 10))

    exclude_pattern = "Dessert|Sweet|Spice Blend|Side Dish|Condiment|Spices"
    filtered = df[~df["course"].str.contains(exclude_pattern, case=False, na=False)].copy()

    if diet == "Vegan":
        filtered = filtered[filtered["diet"].str.contains("Vegan", case=False)]
    elif diet == "Vegetarian":
        filtered = filtered[filtered["diet"].str.contains("Vegetarian|Vegan", case=False)]

    if gluten_free:
        filtered = filtered[filtered["diet"].str.contains("Gluten Free", case=False)]

    loc_keywords = LOCATION_MAP.get(state, [])
    filtered["relevance_score"] = filtered["cuisine"].apply(
        lambda c: 100 if any(k in c for k in loc_keywords) else 0
    )

    if goal == "weight_loss":
        results = filtered.sort_values(["relevance_score", "calories"], ascending=[False, True])
    elif goal == "weight_gain":
        results = filtered.sort_values(["relevance_score", "calories"], ascending=[False, False])
    elif goal == "high_protein":
        results = filtered.sort_values(["relevance_score", "protein"],  ascending=[False, False])
    elif goal == "lean_muscle":
        lean = filtered[filtered["protein"] > 10].copy()
        lean["protein_density"] = lean["protein"] / (lean["calories"] + 1)
        results = lean.sort_values(["relevance_score", "protein_density"], ascending=[False, False])
    else:
        results = filtered.sort_values("relevance_score", ascending=False)

    return jsonify({
        "state":       state or None,
        "diet":        diet or None,
        "gluten_free": gluten_free,
        "goal":        goal,
        "recommendations": rows_to_json(results, n)
    })


@app.route("/search")
def search():
    """
    Simple name search.
    Query params:
        q   – search term
        n   – max results (default 10)
    """
    q = request.args.get("q", "").strip().lower()
    n = int(request.args.get("n", 10))

    if not q:
        return jsonify({"error": "Missing required param: q"}), 400

    mask    = df["name"].str.lower().str.contains(q, na=False)
    results = df[mask][["name", "cuisine", "diet", "course"]].head(n).to_dict(orient="records")

    return jsonify({"query": q, "results": results, "count": len(results)})


# ──────────────────────────────────────────────
#  5. ERROR HANDLERS
# ──────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error", "detail": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
