import csv
import json
import os
from datetime import datetime
import numpy as np

def gini(array):
    """Gini coefficient: Measure of statistical dispersion."""
    array = array.astype(float)
    if np.amin(array) < 0: array -= np.amin(array)
    array += 1e-7
    array = np.sort(array)
    n = array.shape[0]
    index = np.arange(1, n + 1)
    return ((np.sum((2 * index - n - 1) * array)) / (n * np.sum(array)))

def benfords_law_fit(data):
    """Calculate Benford's Law distribution fit for the first digits of enrollment numbers."""
    first_digits = []
    for val in data:
        s = str(int(val)).strip()
        if s and s[0] != '0':
            first_digits.append(int(s[0]))
    
    counts = np.bincount(first_digits)[1:10]
    observed_probs = counts / np.sum(counts)
    
    # Theoretical Benford's Law: P(d) = log10(1 + 1/d)
    theoretical_probs = np.log10(1 + 1/np.arange(1, 10))
    
    # Mean Absolute Deviation (MAD)
    mad = np.mean(np.abs(observed_probs - theoretical_probs))
    return {
        "observed": observed_probs.tolist(),
        "theoretical": theoretical_probs.tolist(),
        "mad": float(mad)
    }

def simple_kmeans(data, k=3, max_iters=20):
    """Manual implementation of K-Means clustering (Numpy-only)."""
    # Normalize data (Min-Max)
    data_min = data.min(axis=0)
    data_max = data.max(axis=0)
    norm_data = (data - data_min) / (data_max - data_min + 1e-7)
    
    # Randomly initialize centroids
    indices = np.random.choice(len(data), k, replace=False)
    centroids = norm_data[indices]
    
    for _ in range(max_iters):
        # Assign clusters
        distances = np.linalg.norm(norm_data[:, np.newaxis] - centroids, axis=2)
        clusters = np.argmin(distances, axis=1)
        
        # Update centroids
        new_centroids = np.array([norm_data[clusters == i].mean(axis=0) if np.any(clusters == i) else centroids[i] for i in range(k)])
        if np.allclose(centroids, new_centroids):
            break
        centroids = new_centroids
        
    # De-normalize centroids
    final_centroids = centroids * (data_max - data_min) + data_min
    return final_centroids.tolist()

def run_advanced_stats(csv_path):
    print(f"Loading {csv_path} for topology analysis (10k records)...")
    records = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                row['EnrollmentCount'] = float(row['EnrollmentCount'])
                row['PrimaryOutcomesCount'] = float(row['PrimaryOutcomesCount'])
                
                fmt1, fmt2 = "%Y-%m-%d", "%Y-%m"
                try: s_date = datetime.strptime(row['StartDate'], fmt1)
                except: s_date = datetime.strptime(row['StartDate'], fmt2)
                try: c_date = datetime.strptime(row['CompletionDate'], fmt1)
                except: c_date = datetime.strptime(row['CompletionDate'], fmt2)
                
                row['DurationDays'] = (c_date - s_date).days
                if row['DurationDays'] > 0:
                    records.append(row)
            except Exception: continue

    print(f"Analyzing {len(records)} valid trials...")
    enrollments = np.array([r['EnrollmentCount'] for r in records])
    outcomes = np.array([r['PrimaryOutcomesCount'] for r in records])
    durations = np.array([r['DurationDays'] for r in records])

    # 1. Benford's Law Analysis (Anomaly Detection)
    benford_results = benfords_law_fit(enrollments)

    # 2. Unsupervised Archetype Clustering (K-Means)
    # Features: Log(Enrollment), Log(Duration), Outcomes
    clustering_features = np.column_stack((
        np.log10(enrollments + 1),
        np.log10(durations + 1),
        outcomes
    ))
    archetype_centroids = simple_kmeans(clustering_features, k=4)

    # 3. Gini Coefficient
    gini_val = gini(enrollments)

    # 4. Meta-Regression (Normal Equations)
    X = np.column_stack((outcomes, durations))
    X_mat = np.column_stack((np.ones(X.shape[0]), X))
    weights, _, _, _ = np.linalg.lstsq(X_mat, enrollments, rcond=None)
    
    stats_report = {
        "metadata": {"sample_size": len(records), "timestamp": datetime.now().isoformat()},
        "benford": benford_results,
        "archetypes": {
            "centroids": archetype_centroids,
            "labels": ["Enrollment (Log10)", "Duration (Log10)", "OutcomeCount"]
        },
        "inequality": {"gini_coefficient": float(gini_val)},
        "regression": {
            "intercept": float(weights[0]),
            "outcome_weight": float(weights[1]),
            "duration_weight": float(weights[2])
        }
    }

    with open('data/advanced_stats.json', 'w', encoding='utf-8') as f:
        json.dump(stats_report, f, indent=4)
    print("Topological advanced stats (Benford + K-Means) calculated successfully.")

if __name__ == "__main__":
    run_advanced_stats('data/protocol_changes.csv')
