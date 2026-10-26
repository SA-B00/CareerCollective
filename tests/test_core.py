import io
from datetime import date
from unittest.mock import patch, Mock

import pandas as pd
import pytest

from core import (
    normalize_date, deadline_from_description, infer_contract, normalize_job,
    skill_tags, rank_jobs, filter_jobs, deduplicate_jobs, make_tracker_row,
    import_tracker, export_tracker_xlsx, days_until_deadline, extract_cv, safe_url,
)
from sources import fetch_greenhouse, fetch_lever, monitored_status


def job(**overrides):
    defaults = dict(id="test1", title="Event coordination internship", company="Demo", city="Paris",
                    contract="Internship", sector="Events", description="Project management, event planning and client experience.",
                    skills="project management; events", source="Demo", source_type="Demo data")
    return normalize_job(defaults | overrides)


def test_date_parsing_conservative():
    assert normalize_date("06/11/2026") == "2026-11-06"
    assert normalize_date("2026-11-06") == "2026-11-06"
    assert normalize_date("some day") == ""
    assert deadline_from_description("Application deadline: 2026-11-06") == "2026-11-06"
    assert deadline_from_description("Hiring throughout 2026") == ""
    assert days_until_deadline({"deadline": "2026-11-06"}, today=date(2026,11,5)) == 1


def test_contract_detection():
    assert infer_contract("Stage Analyste") == "Internship"
    assert infer_contract("Alternance Data Scientist") == "Apprenticeship"
    assert infer_contract("Full-time Sales Executive") == "Other / unknown"


def test_skill_tags_bilingual_and_score():
    tags = skill_tags("Gestion de projet, service client et Excel")
    assert "project management" in tags and "customer service" in tags and "excel" in tags
    ranked, engine = rank_jobs([job(), job(id="test2", title="Finance Internship", sector="Finance", description="Financial reporting and accounting", skills="finance; accounting")],
                               {"goal": "event coordination project management", "skills": "events, customer service, communication", "location":"Paris", "contracts":["Internship"]})
    assert ranked[0]["id"] == "test1"
    assert engine == "tf-idf-fallback"
    assert 0 <= ranked[0]["score"] <= 100
    assert ranked[0]["shared_skills"]


def test_semantic_model_mock():
    class DummyModel:
        def encode(self, corpus, **kwargs):
            return [[1,0],[.9,.1]]
    ranked, engine = rank_jobs([job()], {"goal": "Events", "skills": "events"}, use_semantic=True, model=DummyModel())
    assert engine == "multilingual-transformer"
    assert ranked[0]["score"] > 0


def test_filters_and_dedup():
    a = job()
    b = job(id="test2", city="London", sector="Finance", title="Analyst Apprenticeship", contract="Apprenticeship")
    assert len(filter_jobs([a,b], only_france=True)) == 1
    assert len(filter_jobs([a,b], contract="Apprenticeship", only_france=False)) == 1
    assert len(deduplicate_jobs([a,a,b])) == 2


def test_tracker_io_roundtrip():
    saved = make_tracker_row(job())
    content = export_tracker_xlsx([saved])
    assert content[:2] == b"PK"
    imported = import_tracker(content, "tracker.xlsx")
    assert imported[0]["company"] == "Demo" and imported[0]["status"] == "Saved"


def test_fr_csv_import():
    blob = "Entreprise,Poste,Statut,Date limite\nExample,Stage,Applied,07/11/2026\n".encode()
    imported = import_tracker(blob, "my.csv")
    assert imported[0]["title"] == "Stage"
    assert imported[0]["deadline"] == "2026-11-07"


def test_cv_text_and_safety():
    assert extract_cv("sample.txt", b"Hello CV") == "Hello CV"
    with pytest.raises(ValueError): extract_cv("evil.exe", b"xxx")
    assert safe_url("javascript:alert(1)") == ""
    assert safe_url("https://example.org/job") == "https://example.org/job"


def test_greenhouse_live_feed_parser(monkeypatch):
    payload = {"jobs": [{"id":123, "title":"Stage - Marketing", "location":{"name":"Paris"},
                          "content":"<p>Marketing &amp; communications. Date limite: 05/11/2026</p>",
                          "absolute_url":"https://example.com/careers/123"}]}
    monkeypatch.setattr("sources._fetch_json", lambda *a, **k: payload)
    jobs = fetch_greenhouse("example")
    assert len(jobs) == 1 and jobs[0]["contract"] == "Internship"
    assert jobs[0]["deadline"] == "2026-11-05"
    assert jobs[0]["source_type"] == "Live feed"


def test_lever_live_feed_parser(monkeypatch):
    payload = [{"id":"42", "text":"Alternance Sales", "categories":{"location":"Paris", "team":"Commercial", "commitment":"Apprenticeship"},
                "descriptionPlain":"Business development", "hostedUrl":"https://jobs.lever.co/example/42"}]
    monkeypatch.setattr("sources._fetch_json", lambda *a, **k: payload)
    jobs = fetch_lever("example", "eu")
    assert jobs[0]["contract"] == "Apprenticeship"
    assert jobs[0]["city"] == "Paris"
    assert jobs[0]["source_type"] == "Live feed"


def test_missing_post_is_uncertain():
    row = {"job_id": "a", "url": "https://example.com/a"}
    assert "verify" in monitored_status(row, [], True)
    assert monitored_status(row, [], False) == "Not checked"