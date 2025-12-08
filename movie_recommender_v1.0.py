# ================================================
# Movie Recommender System v1.0
# TMDB Dataset | Content-Based Filtering | KNN + KD-Tree
# ================================================

import time
import numpy as np
import pandas as pd
import ast
import warnings
warnings.filterwarnings("ignore")

from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler, normalize
from sklearn.decomposition import TruncatedSVD
from sklearn.neighbors import NearestNeighbors
import matplotlib.pyplot as plt
import seaborn as sns

from modules.clear_screen import clear_screen
clear_screen()

# ================================================
# 1. Data Loading & Preprocessing
# ================================================
print("Loading TMDB dataset...")
df_raw = pd.read_csv('tmdb_movies_dataset.csv')
df = df_raw.copy()

df['title'] = df['title'].fillna("Unknown Movie")
df['overview'] = df['overview'].fillna("")

df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
df['release_year'] = df['release_date'].dt.year.fillna(2025).astype(int)

def parse_genres(x):
    try:
        return ast.literal_eval(x) if isinstance(x, str) else []
    except:
        return []
df['genre_ids'] = df['genre_ids'].apply(parse_genres)

print(f"Dataset loaded: {len(df):,} movies")

# ================================================
# 2. Feature Engineering
# ================================================
print("Building feature matrix...")
tfidf = TfidfVectorizer(stop_words='english', max_features=10000)
overview_tfidf = tfidf.fit_transform(df['overview'])

mlb = MultiLabelBinarizer()
genre_features = mlb.fit_transform(df['genre_ids'])

numerical = df[['popularity', 'vote_average', 'vote_count']].fillna(0).values
scaler = StandardScaler()
numerical_scaled = scaler.fit_transform(numerical)

X_full = hstack([
    overview_tfidf * 2.0,
    csr_matrix(genre_features) * 1.5,
    csr_matrix(numerical_scaled),
    csr_matrix(df[['release_year']].values)
], format='csr')
print(f"Final sparse feature matrix: {X_full.shape}")

# ================================================
# 3. Dimensionality Reduction (Fast Search)
# ================================================
print("Computing Truncated SVD (100 dimensions)...")
svd = TruncatedSVD(n_components=100, random_state=42)
X_reduced = svd.fit_transform(X_full)
X_reduced = normalize(X_reduced, norm='l2')
print(f"Explained variance ratio: {svd.explained_variance_ratio_.sum():.3f}")

# ================================================
# 4. Models
# ================================================
k = 11
nn_brute_cosine = NearestNeighbors(n_neighbors=k, metric='cosine', algorithm='brute', n_jobs=-1)
nn_kd_tree = NearestNeighbors(n_neighbors=k, algorithm='kd_tree', n_jobs=-1)

nn_brute_cosine.fit(X_full)
nn_kd_tree.fit(X_reduced)

# ================================================
# 5. Helper Functions
# ================================================
titles = df['title'].values
years = df['release_year'].values
votes = df['vote_average'].fillna(0).values
title_to_idx = {t.lower(): i for i, t in enumerate(titles)}

def get_idx(title):
    key = title.lower().strip()
    if key in title_to_idx:
        return title_to_idx[key]
    matches = [i for t, i in title_to_idx.items() if key in t.lower()]
    if matches:
        return matches[0]
    raise ValueError(f"Movie '{title}' not found.")

def rec_brute_cosine(title):
    idx = get_idx(title)
    dists, idxs = nn_brute_cosine.kneighbors(X_full[idx], n_neighbors=k)
    idxs, sims = idxs[0][1:], 1 - dists[0][1:]
    return pd.DataFrame({'title': titles[idxs], 'year': years[idxs],
                         'vote_average': votes[idxs], 'score': sims})

def rec_kd_tree(title):
    idx = get_idx(title)
    dists, idxs = nn_kd_tree.kneighbors(X_reduced[idx].reshape(1, -1))
    idxs, sims = idxs[0][1:], 1 / (1 + dists[0][1:])
    return pd.DataFrame({'title': titles[idxs], 'year': years[idxs],
                         'vote_average': votes[idxs], 'score': sims})

def recommend_for_user(liked_movies, top_n=15):
    idxs = [get_idx(m) for m in liked_movies]
    profile = np.mean(X_reduced[idxs], axis=0).reshape(1, -1)
    dists, neighbors = nn_kd_tree.kneighbors(profile, n_neighbors=top_n + len(idxs))
    
    seen = set(idxs)
    results = []
    for idx, dist in zip(neighbors[0], dists[0]):
        if idx not in seen and len(results) < top_n:
            sim = round(1 / (1 + dist), 4)
            results.append((titles[idx], int(years[idx]), round(float(votes[idx]), 1), sim))
            seen.add(idx)
    return pd.DataFrame(results, columns=["title", "year", "vote_average", "score"])

# ================================================
# 6. Fixed-Width Table
# ================================================
def print_table(recs_df, top_n=10):
    if recs_df.empty:
        print(" " * 35 + "No recommendations found.")
        return
    
    display = recs_df.head(top_n).copy()
    display = display.reset_index(drop=True)
    display.index += 1
    
    titles_trunc = display['title'].apply(lambda x: x[:37] + "..." if len(x) > 40 else x)
    
    print("  #  Movie Title                                 Year   Rating   Similarity")
    print("  ────────────────────────────────────────────────────────────────────────────────")
    for i, row in display.iterrows():
        title = titles_trunc.iloc[i-1].ljust(40)
        year = str(row['year']).center(6)
        rating = f"{row['vote_average']:.1f}".center(8)
        score = f"{row['score']:.3f}".center(10)
        print(f"  {i:>2}. {title}  {year}  {rating}  {score}")
    print()

def pretty_recommendations(title, recs_df, method_name, top_n=10):
    print(f"\n{'='*90}")
    
    # Dynamic, beautiful header — looks perfect for any title length
    title_line = f" RECOMMENDATIONS FOR: {title.upper()} "
    method_line = f" Method: {method_name} "
    
    # Center both lines within 90 chars, but trim if too long
    print(title_line.center(90))
    print(method_line.center(90))
    
    print(f"{'='*90}")
    
    if recs_df.empty:
        print(" " * 35 + "No recommendations found.")
        print()
        return
    
    display = recs_df.head(top_n).copy()
    display = display.reset_index(drop=True)
    display.index += 1
    
    # Truncate long titles
    titles_trunc = display['title'].apply(
        lambda x: x if len(x) <= 40 else x[:37] + "..."
    )
    
    # Table header
    print("  #  Movie Title                                 Year   Rating   Similarity")
    print("  ────────────────────────────────────────────────────────────────────────────────")
    
    for i, row in display.iterrows():
        rank = f"{i:>2}."
        title = titles_trunc.iloc[i-1].ljust(40)
        year = str(row['year']).center(6)
        rating = f"{row['vote_average']:.1f}".center(8)
        score = f"{row['score']:.3f}".center(10)
        print(f"  {rank}  {title}  {year}  {rating}  {score}")
    
    print()

# ================================================
# 7. Banner Helper
# ================================================
def banner(text, char="="):
    t = f" {text} "
    side = (90 - len(t)) // 2
    print(char * 90)
    print(char * side + t + char * (90 - len(t) - side))
    print(char * 90)

# ================================================
# 7. Speed Benchmark + Visualization
# ================================================
def run_benchmark():
    print("\nRunning performance benchmark...")
    test_titles = ["Inception", "Dune", "The Matrix", "Interstellar", "Oppenheimer", "The Dark Knight", "Avatar"]
    
    methods = [
        ("Brute Force (Cosine)", lambda t: nn_brute_cosine.kneighbors(X_full[get_idx(t)])),
        ("KD-Tree (100D Fast)", lambda t: nn_kd_tree.kneighbors(X_reduced[get_idx(t)].reshape(1, -1))),
    ]
    
    results = []
    raw_times = {}
    
    for name, func in methods:
        times = []
        print(f"  Testing {name.ljust(28)} ... ", end="")
        for _ in range(15):  # 15 repeats for stable stats
            start = time.time()
            for title in test_titles:
                func(title)
            times.append((time.time() - start) / len(test_titles))
        avg_ms = np.mean(times) * 1000
        results.append({"Method": name, "Avg Time (ms)": avg_ms, "Times": times})
        raw_times[name] = times
        print(f"{avg_ms:.2f} ms/query")
    
    df_bench = pd.DataFrame(results)
    
    # === Beautiful Plot ===
    sns.set_style("whitegrid")
    plt.figure(figsize=(14, 7))
    
    # Bar plot
    ax1 = plt.subplot(1, 2, 1)
    bars = sns.barplot(data=df_bench, x="Method", y="Avg Time (ms)", palette="viridis")
    plt.title("Average Query Speed\n(lower = faster faster)", fontsize=16, fontweight='bold')
    plt.ylabel("Time per query (ms)")
    for i, bar in enumerate(bars.patches):
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., h + h*0.05,
                 f'{h:.1f} ms', ha='center', va='bottom', fontweight='bold', fontsize=12)
    
    # Box plot
    ax2 = plt.subplot(1, 2, 2)
    bp = plt.boxplot([raw_times[m] for m in df_bench["Method"]], patch_artist=True,
                     labels=df_bench["Method"])
    colors = sns.color_palette("viridis", 2)
    for box, col in zip(bp['boxes'], colors):
        box.set_facecolor(col)
        box.set_alpha(0.8)
    plt.title("Query Time Distribution", fontsize=16, fontweight='bold')
    plt.ylabel("Time per query (seconds)")
    plt.grid(True, axis='y', alpha=0.3)
    
    plt.suptitle(f"Recommender Speed Benchmark • {len(df):,} Movies • 15 Runs", 
                 fontsize=18, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.show()
    
    # Summary
    speedup = df_bench["Avg Time (ms)"].max() / df_bench["Avg Time (ms)"].min()
    fastest = df_bench.loc[df_bench["Avg Time (ms)"].idxmin(), "Method"]
    
    print(f"\n{'='*90}")
    print(f" BENCHMARK SUMMARY")
    print(f"{'='*90}")
    print(f" Fastest method: {fastest}")
    print(f" Speed advantage: {speedup:.1f}× faster")
    print(f"{'='*90}\n")

run_benchmark()

# ================================================
# 9. Final Output
# ================================================
banner("MOVIE RECOMMENDER SYSTEM - RESULTS")

movies_to_test = ["Inception", "The Dark Knight", "Dune: Part Two", "Oppenheimer"]

for movie in movies_to_test:
    pretty_recommendations(movie, rec_brute_cosine(movie),
                          "High Accuracy → Brute-Force Cosine (Full Features)")
    pretty_recommendations(movie, rec_kd_tree(movie),
                          "Fast & Scalable → KD-Tree (100D Embedding)")

banner("PERSONALIZED RECOMMENDATIONS", char="═")

user_likes = ["Inception", "Interstellar", "The Matrix", "Blade Runner 2049"]
print(f"{' Because you loved:: ':═^90}")
print(f" {', '.join(user_likes):^88} ")
print("═" * 90 + "\n")

recs = recommend_for_user(user_likes, top_n=15)

print(f"{' We predict you will love these: ':═^90}")
print()
print_table(recs, top_n=15)

print("═" * 90)
print(f"{' Recommender ready! Edit user_likes to personalize. ':^90}")
print("═" * 90)