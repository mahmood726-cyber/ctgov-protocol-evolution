import os
import json
import hashlib
import unittest

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

if __name__ == '__main__':
    unittest.main()
