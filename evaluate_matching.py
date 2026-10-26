"""Reproducible toy evaluation: relevance labels are subjective and synthetic.
Usage: python evaluate_matching.py [--semantic]
"""
import argparse
from pathlib import Path
import pandas as pd
from core import normalize_job, rank_jobs

SCENARIOS = [
    ({"goal":"Event project coordination and guest experience", "skills":"events, project management, hospitality", "location":"Paris", "contracts":["Internship","Apprenticeship"]},
     {"demo-001", "demo-005", "demo-013", "demo-015"}, "Events"),
    ({"goal":"Software engineering and data science", "skills":"Python, data analysis, software development, Excel", "location":"Paris", "contracts":["Internship"]},
     {"demo-003", "demo-009", "demo-012"}, "Technology"),
    ({"goal":"Finance, management controlling, accounting", "skills":"Financial reporting, Excel, accounting", "location":"Paris", "contracts":["Internship","Apprenticeship"]},
     {"demo-006", "demo-014"}, "Finance"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--semantic", action="store_true", help="Download and use Hugging Face multilingual model")
    args = parser.parse_args()
    df = pd.read_csv(Path(__file__).parent / "data/sample_jobs.csv", dtype=str).fillna("")
    jobs = [normalize_job(row) for row in df.to_dict("records")]
    model = None
    if args.semantic:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    precision = []
    for profile, relevant, label in SCENARIOS:
        recommendations, engine = rank_jobs(jobs, profile, args.semantic, model)
        top3 = [x["id"] for x in recommendations[:3]]
        p3 = len(set(top3) & relevant) / 3
        precision.append(p3)
        print(f"{label}: Top 3 = {top3}, precision@3 = {p3:.2f}")
    print(f"Engine: {engine}; mean toy precision@3: {sum(precision)/len(precision):.2f}")
    print("IMPORTANT: labels are hand-selected SYNTHETIC examples, not measured real-user relevance or fair evaluation.")

if __name__ == "__main__": main()