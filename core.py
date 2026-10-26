"""Pure functions for CareerCollective: matching, documents, data normalisation."""
from __future__ import annotations

import io
import re
import html
from datetime import date, datetime
from typing import Any
from urllib.parse import urlparse

import pandas as pd
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

JOB_COLUMNS = [
    "id", "title", "company", "city", "contract", "sector", "description",
    "skills", "language", "deadline", "url", "source", "source_type",
    "first_seen", "last_checked", "feed_status",
]
TRACKER_COLUMNS = ["job_id", "company", "title", "city", "contract", "url",
                   "deadline", "status", "applied_on", "notes", "source"]
STATUSES = ["Saved", "Applied", "Interview", "Offer", "Rejected", "Withdrawn"]

SKILL_VOCAB = {
    "project management": ["project management", "gestion de projet", "project coordination", "coordination de projet", "gestion de projets"],
    "events": ["events", "event management", "événementiel", "evenementiel", "event planning", "organisation d'événements", "event coordination"],
    "marketing": ["marketing", "campaign", "campagne", "branding", "communication digitale"],
    "customer service": ["customer service", "service client", "relation client", "guest relations", "client experience", "expérience client"],
    "data analysis": ["data analysis", "analyse de données", "analytics", "tableau", "power bi", "statistiques"],
    "excel": ["excel", "spreadsheet", "tableur", "pivot table", "tableau croisé"],
    "python": ["python", "pandas", "scikit-learn"],
    "sales": ["sales", "vente", "commercial", "business development", "prospection"],
    "finance": ["finance", "financial modeling", "modélisation financière", "comptabilité", "accounting"],
    "design": ["design", "figma", "ux", "ui", "graphisme", "création graphique"],
    "operations": ["operations", "opérations", "gestion opérationnelle", "logistics", "logistique"],
    "hospitality": ["hospitality", "hôtellerie", "hotellerie", "restauration", "f&b", "food and beverage"],
    "research": ["research", "recherche", "analyse qualitative", "études", "market research"],
    "communication": ["communication", "writing", "rédaction", "public relations", "relations presse"],
    "sustainability": ["sustainability", "durabilité", "rse", "csr", "environnement"],
    "software development": ["software", "développement logiciel", "javascript", "developer", "développeur", "programming"],
    "recruitment": ["recruitment", "recrutement", "talent acquisition", "ressources humaines", "human resources"],
}


def clean_text(value: Any, limit: int = 12000) -> str:
    if value is None or (not isinstance(value, (str, bytes)) and pd.isna(value)):
        return ""
    text = BeautifulSoup(str(value), "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()[:limit]


def safe_url(value: Any) -> str:
    candidate = str(value or "").strip()
    if len(candidate) > 1500 or any(x in candidate for x in ("\n", "\r", "\t")):
        return ""
    parsed = urlparse(candidate)
    return candidate if parsed.scheme in ("http", "https") and parsed.netloc else ""


def infer_contract(title: str, description: str = "", category: str = "") -> str:
    primary = clean_text(f"{title} {category}").lower()
    secondary = clean_text(description, 500).lower()
    for text in (primary, secondary):
        if re.search(r"\b(alternance|apprentissage|apprenti|apprentice|work[ -]study)\b", text):
            return "Apprenticeship"
        if re.search(r"\b(stage|stagiaire|internship|intern|trainee|practicum)\b", text):
            return "Internship"
    return "Other / unknown"


def normalize_date(value: Any) -> str:
    """Conservatively parse explicit YYYY-MM-DD or DD/MM/YYYY dates only."""
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y-%m-%d")
    text = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    return ""


def deadline_from_description(description: str) -> str:
    text = clean_text(description)
    pattern = (r"(?:application deadline|closing date|apply by|date limite(?: de candidature)?|"
               r"candidatures? avant le|date de clôture)\s*[:\-]?\s*(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{4})")
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return normalize_date(match.group(1)) if match else ""


def normalize_job(item: dict) -> dict:
    record = {key: item.get(key, "") for key in JOB_COLUMNS}
    for col in ("id", "title", "company", "city", "contract", "sector", "description", "skills", "language", "source", "source_type", "feed_status"):
        record[col] = clean_text(record[col], limit=12000 if col == "description" else 450)
    record["url"] = safe_url(record["url"])
    for col in ("deadline", "first_seen", "last_checked"):
        record[col] = normalize_date(record[col])
    record["contract"] = record["contract"] if record["contract"] in ("Internship", "Apprenticeship", "Other / unknown") else infer_contract(record["title"], record["description"])
    return record


def deduplicate_jobs(items: list[dict]) -> list[dict]:
    unique = {}
    for raw in items:
        job = normalize_job(raw)
        if not job["title"]:
            continue
        key = job["url"] or (job["source"], job["id"] or (job["company"], job["title"], job["city"]))
        unique[key] = job
    return list(unique.values())


def skill_tags(text: str) -> list[str]:
    hay = f" {clean_text(text).casefold()} "
    tags = []
    for label, synonyms in SKILL_VOCAB.items():
        if any(re.search(r"(?<!\w)" + re.escape(term.casefold()) + r"(?!\w)", hay) for term in synonyms):
            tags.append(label)
    return tags


def extract_cv(filename: str, data: bytes) -> str:
    """Read machine-readable TXT, PDF, DOCX. Never performs OCR."""
    filename = filename.lower()
    if len(data) > 6 * 1024 * 1024:
        raise ValueError("Maximum CV size is 6 MB.")
    if filename.endswith(".txt"):
        return data.decode("utf-8-sig", errors="replace")[:25000]
    if filename.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return "\n".join((page.extract_text() or "") for page in reader.pages[:12])[:25000]
    if filename.endswith(".docx"):
        from docx import Document
        doc = Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)[:25000]
    raise ValueError("Please upload a TXT, PDF or DOCX document.")


def candidate_text(profile: dict) -> str:
    parts = [profile.get("goal", ""), profile.get("skills", ""), profile.get("sectors", ""), profile.get("cv_text", "")]
    return " ".join(str(s or "") for s in parts).strip()[:30000]


def _job_text(job: dict) -> str:
    # Job title appears three times to make exact role fit meaningful.
    return " ".join([job.get("title", "")] * 3 + [job.get("sector", ""), job.get("skills", ""), job.get("description", "")])[:18000]


def similarity_scores(profile_text: str, jobs: list[dict], use_semantic: bool = False, model=None) -> tuple[list[float], str]:
    if not jobs:
        return [], "none"
    corpus = [profile_text or "student seeking internship apprentissage"] + [_job_text(job) for job in jobs]
    if use_semantic and model is not None:
        vectors = model.encode(corpus, normalize_embeddings=True, show_progress_bar=False)
        sims = cosine_similarity(vectors[:1], vectors[1:]).flatten()
        return [max(0.0, min(1.0, float(s))) for s in sims], "multilingual-transformer"
    vect = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1, max_features=24000, sublinear_tf=True)
    matrix = vect.fit_transform(corpus)
    sims = cosine_similarity(matrix[:1], matrix[1:]).flatten()
    return [float(max(0.0, min(1.0, s))) for s in sims], "tf-idf-fallback"


def rank_jobs(jobs: list[dict], profile: dict, use_semantic=False, model=None) -> tuple[list[dict], str]:
    """Fit score is recommendation similarity, never a hiring probability."""
    base = candidate_text(profile)
    sims, engine = similarity_scores(base, jobs, use_semantic, model)
    user_tags = set(skill_tags(base))
    city_preference = clean_text(profile.get("location", "")).casefold().strip()
    wanted = profile.get("contracts", ["Internship", "Apprenticeship"])
    ranked = []
    for job, sim in zip(jobs, sims):
        tags = set(skill_tags(_job_text(job)))
        shared = sorted(user_tags & tags)
        skill_fit = len(shared) / max(1, min(4, len(user_tags)))
        # 80% similarity, 20% transparent skill overlap. Score is descriptive, not calibrated.
        score = 100.0 * (0.80 * sim + 0.20 * skill_fit)
        if city_preference and city_preference not in ("all france", "france", "toute la france", "anywhere", "remote", "partout"):
            if city_preference not in job["city"].casefold() and not re.search(r"remote|télétravail|teletravail|hybrid|hybride", job["city"], re.I):
                score *= 0.83
        match_contract = job["contract"] in wanted if wanted else True
        if not match_contract:
            score *= 0.70
        result = dict(job)
        result["score"] = round(max(0, min(100, score)))
        result["shared_skills"] = shared
        result["missing_skills"] = sorted(tags - user_tags)[:3]
        result["contract_match"] = match_contract
        ranked.append(result)
    return sorted(ranked, key=lambda x: (-x["score"], x["company"], x["title"])), engine


def filter_jobs(jobs: list[dict], query: str = "", sector: str = "All", contract: str = "All", source: str = "All", only_france: bool = True) -> list[dict]:
    terms = clean_text(query).casefold().split()
    out = []
    for job in jobs:
        hay = " ".join(str(job.get(k, "")) for k in ("title", "company", "city", "sector", "skills", "description")).casefold()
        if terms and not all(t in hay for t in terms):
            continue
        if sector != "All" and job["sector"] != sector:
            continue
        if contract != "All" and job["contract"] != contract:
            continue
        if source != "All" and job["source_type"] != source:
            continue
        if only_france:
            loc = job.get("city", "").casefold()
            # Known obvious non-French location markers only: never silently exclude uncertain labels.
            foreign = ("london", "new york", "berlin", "madrid", "amsterdam", "san francisco", "singapore", "toronto", "boston", "austin", "remote - us")
            if any(f in loc for f in foreign):
                continue
        out.append(job)
    return out


def make_tracker_row(job: dict) -> dict:
    return dict(job_id=job["id"], company=job["company"], title=job["title"],
                city=job["city"], contract=job["contract"], url=job["url"],
                deadline=job["deadline"], status="Saved", applied_on="", notes="", source=job["source"])


def import_tracker(data: bytes, filename: str) -> list[dict]:
    if filename.lower().endswith(".xlsx"):
        df = pd.read_excel(io.BytesIO(data), dtype=str, engine="openpyxl").fillna("")
    elif filename.lower().endswith(".csv"):
        df = pd.read_csv(io.BytesIO(data), dtype=str).fillna("")
    else:
        raise ValueError("Import a .csv or .xlsx file")
    # Accept both English template headings and common French headings.
    aliases = {"entreprise": "company", "poste": "title", "intitulé": "title", "ville": "city",
               "contrat": "contract", "lien": "url", "date limite": "deadline", "statut": "status",
               "date candidature": "applied_on", "commentaires": "notes"}
    df.columns = [aliases.get(str(c).casefold().strip(), str(c).casefold().strip().replace(" ", "_")) for c in df.columns]
    if not {"company", "title"}.issubset(df.columns):
        raise ValueError("Tracker must contain company and title columns (or Entreprise and Poste).")
    output = []
    for index, row in df.head(500).iterrows():
        rec = {c: clean_text(row.get(c, ""), 2000 if c == "notes" else 500) for c in TRACKER_COLUMNS}
        rec["job_id"] = rec["job_id"] or f"import:{index}:{rec['company']}:{rec['title']}"
        rec["url"] = safe_url(rec["url"])
        rec["deadline"] = normalize_date(rec["deadline"])
        rec["applied_on"] = normalize_date(rec["applied_on"])
        rec["status"] = rec["status"] if rec["status"] in STATUSES else "Saved"
        output.append(rec)
    return output


def export_tracker_xlsx(rows: list[dict]) -> bytes:
    output = io.BytesIO()
    frame = pd.DataFrame(rows, columns=TRACKER_COLUMNS)
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, sheet_name="Applications")
        ws = writer.sheets["Applications"]
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        widths = {"A": 19, "B": 24, "C": 38, "D": 23, "E": 20, "F": 43, "G": 18, "H": 19, "I": 19, "J": 55, "K": 25}
        from openpyxl.styles import Font, PatternFill, Alignment
        for col, width in widths.items():
            ws.column_dimensions[col].width = width
        for cell in ws[1]:
            cell.fill = PatternFill("solid", fgColor="193D43")
            cell.font = Font(bold=True, color="FFFFFF")
            cell.alignment = Alignment(vertical="center")
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(vertical="top", wrap_text=True)
    return output.getvalue()


def days_until_deadline(row: dict, today: date | None = None) -> int | None:
    value = normalize_date(row.get("deadline"))
    if not value:
        return None
    return (date.fromisoformat(value) - (today or date.today())).days