import os
import sys
import json
import hashlib
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.advanced_stats import benfords_law_fit, gini, simple_kmeans

class TestProtocolEvolutionPipeline(unittest.TestCase):
    
    def test_truthcert_validation(self):
        csv_path = 'data/protocol_changes.csv'
        manifest_path = 'data/hash_manifest.json'
        
        # Verify files exist
        self.assertTrue(os.path.exists(csv_path), "Data CSV missing")
        self.assertTrue(os.path.exists(manifest_path), "TruthCert manifest missing")
        
        # Verify hash match
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
            
        with open(csv_path, 'rb') as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()
            
        self.assertEqual(actual_hash, manifest['sha256_hash'], "TruthCert Hash Mismatch: Data integrity compromised")

    def test_dashboard_exists(self):
        self.assertTrue(os.path.exists('site/index.html'), "HTML Dashboard missing")

    def test_advanced_stats_exists(self):
        self.assertTrue(os.path.exists('data/advanced_stats.json'), "Advanced stats JSON missing")
        with open('data/advanced_stats.json', 'r') as f:
            stats = json.load(f)
        self.assertIn('benford', stats)
        self.assertIn('archetypes', stats)
        self.assertLess(stats['benford']['mad'], 0.05, "Benford MAD too high: potential data anomaly")
        self.assertGreaterEqual(stats['metadata']['sample_size'], 9000)

    def test_e156_micro_paper_constraints(self):
        paper_text = "Clinical trial protocols dynamically adapt over their lifecycle to resolve operational and scientific challenges. We analyzed 10,000 multi-disease trials from ClinicalTrials.gov using Benford's Law to detect reporting anomalies in enrollment data. The analytical engine implements unsupervised K-means clustering to identify trial archetypes based on enrollment size, study duration, and outcome density. We computed the Gini coefficient across a diversified research landscape including oncology, diabetes, and neurology to measure structural enrollment inequality. Statistical provenance is secured via TruthCert cryptographic hashing and deterministic Numpy-only topological processing to ensure absolute reproducibility. These analytics are rendered in an interactive dashboard providing real-time insights into study execution fidelity and data integrity. This project establishes a novel, multi-dimensional framework for monitoring reporting anomalies and trial species distribution in global clinical research."
        
        words = len(paper_text.split())
        clean_text = paper_text.replace('.gov', ' gov')
        sentences = len([s for s in clean_text.split('.') if s.strip()])
        
        self.assertTrue(words <= 156, f"Word count ({words}) exceeds E156 limit (156)")
        self.assertEqual(sentences, 7, f"Sentence count ({sentences}) must be exactly 7")

class TestAdvancedStatsEngine(unittest.TestCase):

    def test_benford_handles_missing_leading_digits(self):
        # No 8s or 9s present: bincount must still yield a 9-vector
        # (regression for a length-mismatch broadcast error).
        data = [1, 1, 2, 3, 1, 2, 4, 5, 6, 7, 1, 2, 3]
        result = benfords_law_fit(data)
        self.assertEqual(len(result['observed']), 9)
        self.assertEqual(len(result['theoretical']), 9)
        self.assertGreaterEqual(result['mad'], 0.0)

    def test_benford_empty_input_raises(self):
        with self.assertRaises(ValueError):
            benfords_law_fit([])

    def test_gini_known_value(self):
        # Perfectly equal distribution -> Gini ~ 0
        self.assertAlmostEqual(gini(np.array([5.0, 5.0, 5.0, 5.0])), 0.0, places=4)

    def test_kmeans_too_few_points_raises(self):
        with self.assertRaises(ValueError):
            simple_kmeans(np.random.rand(2, 3), k=4)


if __name__ == '__main__':
    unittest.main()
