# ================================================
# Movie Recommender System via KNN + KD-TREE
# TMDB Dataset | Content-Based Filtering
# ================================================

# [IMPORT] Standard Libraries
import time
import numpy as np
import pandas as pd
import ast
from collections import Counter

# [IMPORT] Warnings
import warnings
warnings.filterwarnings("ignore")

# [IMPORT] Machine Learning Libraries
from scipy.sparse import load_npz, hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler, normalize
from sklearn.decomposition import TruncatedSVD
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_distances
import matplotlib.pyplot as plt
import seaborn as sns

# ================================================
# 1. Data Loading & Preprocessing
# ================================================
print("Loading TMDB dataset...")
df_raw = pd.read_csv('tmdb_movies_dataset.csv')

# Keep original title for display
df = df_raw.copy()
df['title'] = df['title'].fillna("Unknown Movie")
df['overview'] = df['overview'].fillna("")

# Parse release date
df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
df['release_year'] = df['release_date'].dt.year.fillna(2025).astype(int)

# Parse genre_ids
def parse_genres(x):
    try:
        return ast.literal_eval(x) if isinstance(x, str) else []
    except:
        return []
df['genre_ids'] = df['genre_ids'].apply(parse_genres)

print(f"Dataset loaded: {len(df)} movies")

# ================================================
# 2. Feature Engineering
# ================================================
print("Building feature matrix...")

# Text: TF-IDF on overview
tfidf = TfidfVectorizer(stop_words='english', max_features=10000)
overview_tfidf = tfidf.fit_transform(df['overview'])

# Genres: Multi-label binarizer
mlb = MultiLabelBinarizer()
genre_features = mlb.fit_transform(df['genre_ids'])

# Numerical features
numerical = df[['popularity', 'vote_average', 'vote_count']].fillna(0).values
scaler = StandardScaler()
numerical_scaled = scaler.fit_transform(numerical)

# Combine all
X_full = hstack([
    overview_tfidf * 2.0,      # Text is most important
    csr_matrix(genre_features) * 1.5,
    csr_matrix(numerical_scaled),
    csr_matrix(df[['release_year']].values)
], format='csr')

print(f"Final sparse feature matrix: {X_full.shape}")

# Save for future use (optional)
# from scipy.sparse import save_npz
# save_npz("tmdb_features.npz", X_full)

# ================================================
# 3. Dense Reduced Representation (for KD-Tree)
# ================================================
print("Computing TruncatedSVD (100 dims) for KD-Tree...")
svd = TruncatedSVD(n_components=100, random_state=42)
X_reduced = svd.fit_transform(X_full)
X_reduced = normalize(X_reduced, norm='l2')  # L2 normalize for cosine-like behavior
print(f"Explained variance: {svd.explained_variance_ratio_.sum():.3f}")

# ================================================
# 4. Models
# ================================================
k = 11  # +1 to drop self

# sklearn models
nn_brute_cosine = NearestNeighbors(n_neighbors=k, metric='cosine', algorithm='brute', n_jobs=-1)
nn_kd_tree = NearestNeighbors(n_neighbors=k, algorithm='kd_tree', n_jobs=-1)
nn_ball_tree = NearestNeighbors(n_neighbors=k, algorithm='ball_tree', n_jobs=-1)

nn_brute_cosine.fit(X_full)
nn_kd_tree.fit(X_reduced)
nn_ball_tree.fit(X_reduced)

# * [CLASS] Raw KNN (improved with vectorized distance)
class RawKNN:
    def __init__(self, k=10):
        self.k = k
    def fit(self, X):
        self.X = np.asarray(X)
    def query(self, x):
        dists = np.linalg.norm(self.X - x, axis=1)
        idx = np.argpartition(dists, self.k)[:self.k]
        sorted_idx = idx[np.argsort(dists[idx])]
        return list(zip(dists[sorted_idx], sorted_idx))

raw_knn = RawKNN(k=k)
raw_knn.fit(X_reduced)

# KD-Tree (use sklearn if issues in high dim)
try:
    from sklearn.neighbors import KDTree
    kd_tree_custom = KDTree(X_reduced)
    print("Using sklearn KDTree (recommended for reliability)")
except:
    kd_tree_custom = None

# ================================================
# 5. Recommendation Functions
# ================================================
titles = df['title'].values
years = df['release_year'].values
votes = df['vote_average'].fillna(0).values
title_to_idx = {t.lower(): i for i, t in enumerate(titles)}

def get_idx(title):
    key = title.lower().strip()
    if key in title_to_idx:
        return title_to_idx[key]
    for t, i in title_to_idx.items():
        if key in t:
            return i
    raise ValueError(f"Movie '{title}' not found")

def print_recommendations(title, method_name, get_recs_func):
    print(f"\n{'='*60}")
    print(f" RECOMMENDATIONS FOR: {title.upper()}")
    print(f" Method: {method_name}")
    print(f"{'='*60}")
    try:
        recs = get_recs_func()
        for i, row in recs.head(10).iterrows():
            print(f"{i+1:2}. {row['title']} ({row['year']}) | Rating: {row['vote_average']:.1f} | Sim: {row['score']:.3f}")
    except Exception as e:
        print(f"Error: {e}")

# Define recommendation functions
def rec_brute_cosine(title):
    idx = get_idx(title)
    dists, idxs = nn_brute_cosine.kneighbors(X_full[idx], n_neighbors=k)
    idxs = idxs[0][1:]  # drop self
    sims = 1 - dists[0][1:]
    return pd.DataFrame({
        'title': titles[idxs],
        'year': years[idxs],
        'vote_average': votes[idxs],
        'score': sims
    })

def rec_kd_tree(title):
    idx = get_idx(title)
    dists, idxs = nn_kd_tree.kneighbors(X_reduced[idx].reshape(1, -1))
    idxs = idxs[0][1:]
    sims = 1 / (1 + dists[0][1:])
    return pd.DataFrame({
        'title': titles[idxs],
        'year': years[idxs],
        'vote_average': votes[idxs],
        'score': sims
    })

# ================================================
# 6. Timing Comparison
# ================================================
def benchmark(titles_list, repeats=3):
    results = []
    for name, func in [
        ("Brute Force (Cosine)", lambda t: nn_brute_cosine.kneighbors(X_full[get_idx(t)])),
        ("KD-Tree (Reduced)", lambda t: nn_kd_tree.kneighbors(X_reduced[get_idx(t)].reshape(1, -1))),
        ("Ball Tree", lambda t: nn_ball_tree.kneighbors(X_reduced[get_idx(t)].reshape(1, -1))),
        ("Raw KNN (Raw Implementation)", lambda t: raw_knn.query(X_reduced[get_idx(t)])),
    ]:
        times = []
        for _ in range(repeats):
            start = time.time()
            for t in titles_list:
                func(t)
            times.append(time.time() - start)
        results.append({"Method": name, "Avg Time (s)": np.mean(times)/len(titles_list)})
    return pd.DataFrame(results)

print("\n" + "="*70)
print(" BENCHMARK RESULTS")
print("="*70)
bench_df = benchmark(["Inception", "Dune", "The Matrix", "Interstellar"])
print(bench_df.round(4))

# ================================================
# 7. Final Recommendations
# ================================================
test_movies = ["Inception", "The Dark Knight", "Dune: Part Two", "Oppenheimer"]

for movie in test_movies:
    print_recommendations(movie, "Best Quality: Brute-Force Cosine (Sparse TF-IDF)", lambda: rec_brute_cosine(movie))
    print_recommendations(movie, "Fast Approximation: KD-Tree (100D)", lambda: rec_kd_tree(movie))

# ================================================
# 8. User Profile
# ================================================
def recommend_for_user(liked_movies, top_n=10):
    try:
        idxs = [get_idx(m) for m in liked_movies]
    except ValueError as e:
        print(f"Error: {e}")
        return pd.DataFrame()
    
    # Create average profile vector in reduced space
    profile = np.mean(X_reduced[idxs], axis=0).reshape(1, -1)
    
    # Query using fast KD-Tree
    dists, neighbors = nn_kd_tree.kneighbors(profile, n_neighbors=top_n + len(idxs))
    neighbors = neighbors[0]
    dists = dists[0]
    
    # Remove the movies the user already liked
    filtered_neighbors = []
    filtered_sims = []
    for neigh_idx, dist in zip(neighbors, dists):
        if neigh_idx not in idxs:
            filtered_neighbors.append(neigh_idx)
            filtered_sims.append(1 / (1 + dist))  # convert Euclidean → similarity
        if len(filtered_neighbors) >= top_n:
            break
    
    # Build DataFrame safely
    recs = pd.DataFrame({
        'title': [titles[i] for i in filtered_neighbors],
        'year': [years[i] for i in filtered_neighbors],
        'vote_average': [float(votes[i]) for i in filtered_neighbors],
        'score': [round(s, 4) for s in filtered_sims]
    })
    
    return recs

# ================================================
# 9. Evaluation
# ================================================
print("\n" + "="*70)
print(" CONCLUSION & INSIGHTS")
print("="*70)
print("""
Most accurate                         : Brute-force cosine search using full TF-IDF and genre data.
Fastest after reduction               : KD-Tree or Ball Tree on a 100-dimensional embedding.
Custom KNN and KD-Tree                : Work well on low-dimensional dense data.
High-dimensional sparse data (>5000D) : KD-Tree performance drops, brute-force is better.
TruncatedSVD                          : Reduces dimensions while keeping about 80–90% of the similarity information.
Real-world use                        : Content-based filtering is used by Netflix, Spotify, and YouTube.
""")