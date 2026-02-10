import os, ast, csv, time
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from flask_cors import CORS

DATA_DIR = "data"
CLEAN_FILE = os.path.join(DATA_DIR, "recipes_clean.csv")
EMB_FILE = os.path.join(DATA_DIR, "embeddings.npz")
FEEDBACK_FILE = os.path.join(DATA_DIR, "feedback.csv")

# Tuning
TOP_K = 12
MIN_OVERLAP = 0  # set >0 to require that at least N query tokens overlap ingredients

app = Flask(__name__)
CORS(app)  # allow requests from Vue frontend (localhost:5173)

# Lazy globals
_model = None
_embeddings = None
_ids = None
_df = None

def load_index():
    global _model, _embeddings, _ids, _df
    if _df is None:
        assert os.path.exists(CLEAN_FILE), "Missing recipes_clean.csv. Run: python build_index.py"
        _df = pd.read_csv(CLEAN_FILE)
        # parse lists
        _df['ingredients_list'] = _df['ingredients_list'].apply(lambda s: ast.literal_eval(s) if isinstance(s,str) else [])
        _df['steps_list'] = _df['steps_list'].apply(lambda s: ast.literal_eval(s) if isinstance(s,str) else [])
    if _embeddings is None or _ids is None:
        assert os.path.exists(EMB_FILE), "Missing embeddings.npz. Run: python build_index.py"
        npz = np.load(EMB_FILE)
        _embeddings = npz['embeddings']
        _ids = npz['ids']
    if _model is None:
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model, _embeddings, _ids, _df

def prefer_healthier(df, idxs):
    sub = df.loc[idxs, ['calories']].copy()
    sub['cal'] = sub['calories'].fillna(1e9)
    order = sub['cal'].argsort(kind="mergesort")
    return idxs[order]

def token_overlap(query, ingredients):
    q = [t.strip().lower() for t in query.split(",") if t.strip()]
    ing = [t.strip().lower() for t in ingredients]
    return len(set(q) & set(ing))


@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    query = data.get("query", "").strip()
    healthy = bool(data.get("healthy", False))
    if not query:
        return jsonify({"results": []})

    model, embeddings, ids, df = load_index()

    qvec = model.encode([query], normalize_embeddings=True)
    sims = cosine_similarity(qvec, embeddings)[0]

    top_idx = sims.argsort()[-200:][::-1]
    if MIN_OVERLAP > 0:
        filtered = []
        for i in top_idx:
            row = df.iloc[i]
            if token_overlap(query, row['ingredients_list']) >= MIN_OVERLAP:
                filtered.append(i)
        top_idx = np.array(filtered, dtype=int)

    if healthy:
        top_idx = prefer_healthier(df, top_idx)

    top_idx = top_idx[:TOP_K]
    rows = df.iloc[top_idx].copy()
    rows['score'] = sims[top_idx]

    results = []
    for _, row in rows.iterrows():
        results.append({
            "id": int(row['id']),
            "name": row['name'],
            "minutes": int(row['minutes']) if not pd.isna(row['minutes']) else None,
            "n_ingredients": int(row['n_ingredients']) if not pd.isna(row['n_ingredients']) else None,
            "calories": float(row['calories']) if not pd.isna(row['calories']) else None,
            "score": float(row['score']),
        })

    return jsonify({"results": results, "query": query, "healthy": healthy})


@app.route("/recipe/<int:recipe_id>")
def recipe_detail(recipe_id):
    _, _, _, df = load_index()
    row = df[df['id'] == recipe_id].iloc[0]
    recipe = {
        "id": int(row['id']),
        "name": row['name'],
        "minutes": int(row['minutes']) if not pd.isna(row['minutes']) else None,
        "n_ingredients": int(row['n_ingredients']) if not pd.isna(row['n_ingredients']) else None,
        "calories": float(row['calories']) if not pd.isna(row['calories']) else None,
        "ingredients_list": row['ingredients_list'],
        "steps_list": row['steps_list'],
    }
    return jsonify({"recipe": recipe})


@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json()
    recipe_id = int(data.get("recipe_id"))
    query = data.get("query", "")
    helpful = int(data.get("helpful", 0))
    ts = int(time.time())
    header = not os.path.exists(FEEDBACK_FILE)
    with open(FEEDBACK_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if header:
            writer.writerow(["timestamp", "recipe_id", "query", "helpful"])
        writer.writerow([ts, recipe_id, query, helpful])
    return jsonify({"status": "success"})

@app.route("/top-feedback", methods=["GET"])
def top_feedback():
    if not os.path.exists(FEEDBACK_FILE):
        return jsonify({"recipes": []})

    # Load feedback
    df = pd.read_csv(FEEDBACK_FILE)

    # Only count helpful = 1
    good = df[df["helpful"] == 1]

    # Count most liked recipes
    counts = good.groupby("recipe_id").size().reset_index(name="count")
    counts = counts.sort_values("count", ascending=False).head(10)

    _, _, _, recipes_df = load_index()

    top_recipes = []
    for _, row in counts.iterrows():
        rid = row["recipe_id"]
        recipe_row = recipes_df[recipes_df["id"] == rid]
        if not recipe_row.empty:
            r = recipe_row.iloc[0]
            top_recipes.append({
                "id": int(r["id"]),
                "name": r["name"],
                "minutes": int(r["minutes"]) if not pd.isna(r["minutes"]) else None,
                "n_ingredients": int(r["n_ingredients"]) if not pd.isna(r["n_ingredients"]) else None,
                "calories": float(r["calories"]) if not pd.isna(r["calories"]) else None,
                "feedback_count": int(row["count"]),
            })

    return jsonify({"recipes": top_recipes})


if __name__ == "__main__":
    app.run(debug=True)
