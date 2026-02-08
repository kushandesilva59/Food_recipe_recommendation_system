import os, ast, math
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

DATA_DIR = "data"
RAW_FILE = os.path.join(DATA_DIR, "RAW_recipes.csv")
CLEAN_FILE = os.path.join(DATA_DIR, "recipes_clean.csv")
EMB_FILE = os.path.join(DATA_DIR, "embeddings.npz")

# You can cap recipes for low-memory environments
MAX_RECIPES = None  # e.g., 50000

def parse_list_str(s):
    if pd.isna(s): return []
    try:
        v = ast.literal_eval(s)
        if isinstance(v, list):
            return [str(x).strip() for x in v]
        return []
    except Exception:
        return []

def parse_nutrition(s):
    # Food.com nutrition format: [calories, total fat Pdv, sugar Pdv, sodium Pdv, protein Pdv, sat fat Pdv, carbs Pdv]
    lst = parse_list_str(s)
    if not lst or len(lst) < 1:
        return None
    try:
        return float(lst[0])  # calories
    except Exception:
        return None

def load_and_clean():
    assert os.path.exists(RAW_FILE), f"Missing {RAW_FILE}. Please put RAW_recipes.csv in data/."
    df = pd.read_csv(RAW_FILE)
    cols = ['id','name','minutes','ingredients','n_ingredients','steps','nutrition','tags']
    df = df[cols].copy()

    # normalize
    df['ingredients_list'] = df['ingredients'].apply(parse_list_str)
    df['steps_list'] = df['steps'].apply(parse_list_str)
    df['calories'] = df['nutrition'].apply(parse_nutrition)

    # build text for embedding: name + ingredients
    def join_ing(lst): return ", ".join(lst[:25])
    df['text'] = df['name'].fillna('') + " | ingredients: " + df['ingredients_list'].apply(join_ing)

    # filter minimal viable recipes
    df = df[(df['name'].notna()) & (df['ingredients_list'].str.len() > 0) & (df['steps_list'].str.len() > 0)]
    if MAX_RECIPES:
        df = df.head(MAX_RECIPES).copy()

    # save cleaned csv
    df[['id','name','minutes','n_ingredients','calories','ingredients_list','steps_list','text']].to_csv(CLEAN_FILE, index=False)
    return df

def build_embeddings(df):
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    texts = df['text'].tolist()
    # encode in batches
    emb = model.encode(texts, batch_size=256, show_progress_bar=True, normalize_embeddings=True)
    emb = np.asarray(emb, dtype="float32")
    ids = df['id'].to_numpy()
    np.savez(EMB_FILE, embeddings=emb, ids=ids)

if __name__ == "__main__":
    print("Loading & cleaning...")
    df = load_and_clean()
    print(f"Recipes after cleaning: {len(df)}")
    print("Building embeddings...")
    build_embeddings(df)
    print("Done. Files written to data/.")
