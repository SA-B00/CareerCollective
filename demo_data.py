"""Load reproducible, visibly fictional data for the CareerCollective demonstration."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd


def load_demo_profile(root: Path) -> dict:
    return json.loads((Path(root) / "data" / "demo_profile.json").read_text(encoding="utf-8"))


def empty_profile() -> dict:
    return {"goal": "", "skills": "", "location": "", "sectors": "", "cv_text": "",
            "contracts": ["Internship", "Apprenticeship"]}


def load_demo_tracker(root: Path) -> dict:
    df = pd.read_csv(Path(root) / "data" / "demo_applications.csv", dtype=str).fillna("")
    return {row["job_id"]: row for row in df.to_dict("records")}


def load_demo_discussions(root: Path) -> list[dict]:
    data = Path(root) / "data"
    posts = pd.read_csv(data / "sample_discussions.csv", dtype=str).fillna("").to_dict("records")
    replies = pd.read_csv(data / "demo_community_replies.csv", dtype=str).fillna("").to_dict("records")
    by_id = {}
    for reply in replies:
        by_id.setdefault(str(reply["thread_id"]), []).append({"author": reply["author"], "text": reply["text"]})
    for post in posts:
        post["user_replies"] = by_id.get(str(post["id"]), [])
        post["replies"] = 0
    return posts