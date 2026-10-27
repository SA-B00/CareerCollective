"""CareerCollective  -  bilingual student career discovery, matching & tracking.
Run: streamlit run app.py
No authentication; all personal input remains in browser session and in local
Streamlit server memory for that session (not persistent across reloads).
"""
from __future__ import annotations

import html
import io
import json
import os
import re
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from core import (
    JOB_COLUMNS, TRACKER_COLUMNS, STATUSES, candidate_text, clean_text,
    days_until_deadline, deduplicate_jobs, export_tracker_xlsx, extract_cv,
    filter_jobs, import_tracker, make_tracker_row, normalize_date,
    normalize_job, rank_jobs, safe_url,
)
from sources import fetch_greenhouse, fetch_lever, fetch_featured_jobs, monitored_status
from demo_data import load_demo_profile, load_demo_tracker, load_demo_discussions, empty_profile
from calendar_ui import render_status_strip, render_calendar


ROOT = Path(__file__).parent
DISPLAY_PICTOGRAPHS = re.compile(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]")


def professional_text(value):
    """Remove emoji characters from untrusted employer descriptions in the UI."""
    return DISPLAY_PICTOGRAPHS.sub("", str(value))


st.set_page_config(page_title="CareerCollective | Find your next step", page_icon=":material/work:", layout="wide", initial_sidebar_state="expanded")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap');
:root {--navy:#18385f;--blue:#205caa;--ink:#213652;--pale:#eef5fd;--line:#d9e6f7;}
html,body,[class*="css"],.stApp{font-family:'DM Sans',sans-serif;}
.stApp{background:#ffffff;color:#213652;}
h1,h2,h3{font-family:'Outfit',sans-serif;letter-spacing:-.023em;color:#1b3558;}
.block-container{max-width:1320px;padding-top:2rem;padding-bottom:4rem;}
[data-testid="stSidebar"]{background:#f7faff;border-right:1px solid #e2ebf7;}
[data-testid="stSidebar"] .stRadio label{font-weight:500;color:#28476d;}
.hero{background:linear-gradient(115deg,#ffffff 0%,#f2f7ff 100%);border:1px solid #dce9f8;border-left:5px solid #205caa;border-radius:17px;padding:28px 36px;margin-bottom:22px;color:#203d63;box-shadow:0 5px 23px #173c7410;}
.hero h1{color:#163960!important;font-size:2.4rem;line-height:1.15;margin:0 0 12px;max-width:800px;}
.hero p{color:#536b88;margin:0;max-width:780px;font-size:1rem;}
.eyebrow{font-size:.74rem!important;text-transform:uppercase;letter-spacing:.13em;font-weight:800;color:#2768b3!important;margin-bottom:10px!important;}
.tiny-pill{display:inline-block;border-radius:7px;padding:5px 11px;background:#eaf2fd;color:#234f8b;font-size:.76rem;font-weight:700;margin-right:6px;}
.disclaimer{border:1px solid #dce8f7;background:#f7faff;border-radius:10px;padding:11px 15px;color:#526b87;font-size:.84rem;margin-top:12px;}
.header-line{font-size:1.8rem;font-weight:750;color:#183b64;margin-bottom:.1rem;}
.note-small{font-size:.83rem;color:#687f9b;}
[data-testid="stMetric"]{background:#f8fbff;border:1px solid #e1eaf7;border-radius:13px;padding:15px 18px;}
[data-testid="stVerticalBlockBorderWrapper"]{border-color:#e0e9f6!important;border-radius:14px!important;}
div.stButton>button[kind="primary"]{background:#205caa;border:1px solid #205caa;border-radius:9px;color:white;font-weight:700;}
div.stButton>button[kind="primary"]:hover{background:#164680;border-color:#164680;}
div.stButton>button{border-radius:9px;}
[data-testid="stLinkButton"] a{border-radius:9px;}
hr{border-top:1px solid #e7eef8!important;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

TEXT = {
    "en": {
        "discover": "Discover", "tracker": "My applications", "calendar": "Calendar", "community": "Community", "profile": "My profile", "about": "About & sources",
        "subtitle": "AI-guided internships, apprenticeships and a community to move forward together.",
        "welcome": "Your next opportunity starts here.", "mission": "Discover relevant internships and apprenticeships, organize every application, and learn from other students  -  all in one place.",
        "demo": "Demonstration mode", "info": "This app starts with a fictional student profile and simulated applications, interviews and discussions. No applications were actually submitted. Employer vacancies are separate and must be checked at source. Session changes are not saved unless exported.",
        "total": "Opportunities", "tracked": "Applications tracked", "soon": "Deadlines within 7 days", "posts": "Community discussions",
        "matches": "Find your matches", "find_desc": "Smart matching considers your goals, transferable skills and career interests  -  not just job-title keywords.",
        "query": "Search jobs, companies or skills", "sector": "Industry", "contract": "Contract type", "source": "Source", "france": "Prioritize France / exclude obvious non-French cities", "all": "All",
        "rank": "Match score", "save": "Save opportunity", "saved": "Saved", "apply": "Open original job listing", "reason": "Why this match?", "overlap": "Related strengths", "gaps": "Skills mentioned in the role to explore", "none": "No specific vocabulary overlap found  -  review the description manually.",
        "deadline": "Application deadline", "not_given": "Not published", "match_notice": "Match scores are relative recommendations, NOT hiring probabilities. Contract and location information may require verification.",
        "live_header": "Import current vacancies", "live_help": "These APIs read publicly published jobs from one participating employer at a time. Enter its board identifier (not its URL).",
        "load": "Import public job listings", "live_success": "Imported", "live_error": "Could not import this board", "notice_live": "Refreshes are on demand; these sources do not provide universal job search or confirmed closing dates.",
        "manual": "Add a job manually", "company": "Company", "title": "Role title", "city": "City / location", "description": "Description", "skills": "Skills (comma-separated)", "job_url": "Original job URL (optional)", "submit_job": "Add opportunity", "manual_added": "Opportunity added to the catalogue.",
        "tracker_header": "Your application pipeline", "tracker_desc": "Update your progress and notes in the table. Download your tracker before leaving or refreshing the page.",
        "empty_tracker": "No applications yet. Save a job from Discover or import an existing tracker below.",
        "export": "Download Excel tracker", "export_csv": "Download CSV tracker", "import": "Import an existing Excel / CSV tracker", "import_button": "Import tracker", "import_success": "Applications imported", "import_error": "Could not import tracker", "snapshot": "Download session backup (JSON)", "restore": "Restore session backup", "restore_button": "Restore backup",
        "status": "Status", "notes": "Notes", "upcoming": "Upcoming deadlines", "delayed": "Deadline passed", "unlisted": "No published deadline", "delete": "Remove", "monitor": "Availability check", "monitor_description": "After refreshing its employer feed, a tracked listing can be checked against the latest public results. Missing does not prove closure.",
        "community_header": "A career journey is better together.", "community_desc": "Ask questions, exchange interview experiences, or find fellow applicants. This is a DEMO discussion board; only participants in this browser session see your messages.",
        "new_post": "Start a discussion", "alias": "Display name (avoid personal details)", "topic": "Discussion title", "category": "Category", "post": "Post discussion", "posted": "Your demo post is visible in this session.", "comment": "Leave a reply", "send_reply": "Post reply", "all_discussions": "Community feed", "community_note": "Every visible starter conversation and reply is fictional, including messages by Alex Martin. New replies appear only in your own session. There is no shared community database or moderation.", "group_link": "Optional external student-group link", "group_link_help": "Organizers may add a verified Discord/WhatsApp invitation. Never upload CVs or personal details into an untrusted group.",
        "profile_header": "Make the recommendations yours.", "profile_desc": "Tell CareerCollective what you want to do next. You can type details or upload a machine-readable CV.",
        "goal": "Career goal / roles sought", "location": "Preferred location", "interest": "Preferred industries", "profile_skills": "Skills and experiences", "contracts": "Looking for", "resume": "Upload your CV (PDF, DOCX, TXT)", "resume_ok": "CV text extracted", "resume_err": "Unable to read this file", "cv_warning": "Scanned or image-only PDFs cannot be read here. Enter your background manually instead.", "save_profile": "Save profile", "profile_saved": "Profile updated. Recommendations will use these preferences.", "engine": "AI matching engine", "engine_fast": "Fast text-similarity baseline", "engine_ai": "Multilingual pretrained transformer (AI)", "model_error": "The pretrained model was unavailable. Showing the reproducible text-matching baseline instead.", "current_engine": "Current engine", "recalculate": "Recommendations refresh when your profile or filters change.",
        "about_header": "How CareerCollective works", "about_desc": "Educational prototype built for a student AI project. Its capabilities and limitations are clearly labeled.",
        "step1": "1. Describe your experience and career goals or upload a CV.", "step2": "2. Search current public employer feeds and previously observed employer links; switch to sample roles only for demos.", "step3": "3. Compare explainable recommendations, save roles and track the process.", "step4": "4. Exchange ideas in the demonstrative Community area and export your records.",
        "data_note": "Example data are fictional and intended only for testing. Live listings originate directly from selected employers' publicly available feeds; their availability can change. No automated applications are submitted.",
        "download_data": "Download demonstration dataset", "download_prompts": "Sources, technical citations and example prompts are included in the project ZIP.",
        "filter_none": "No results match the current filters. Try broader terms, or add a job manually.",
    },
    "fr": {
        "discover": "Découvrir", "tracker": "Mes candidatures", "calendar": "Calendrier", "community": "Communauté", "profile": "Mon profil", "about": "À propos & sources",
        "subtitle": "Stages, alternances et entraide étudiante, guidés par l'IA.",
        "welcome": "Votre prochaine opportunité commence ici.", "mission": "Trouvez des stages et alternances adaptés, suivez vos candidatures et échangez avec d'autres étudiants  -  au même endroit.",
        "demo": "Mode démonstration", "info": "Profil initial fictif avec candidatures envoyées simulées, entretiens et discussions fictives. Aucune candidature réelle n'a été envoyée. Les offres employeurs sont distinctes et à vérifier. Exportez vos données pour les conserver.",
        "total": "Opportunités", "tracked": "Candidatures suivies", "soon": "Échéances sous 7 jours", "posts": "Discussions",
        "matches": "Trouver des opportunités", "find_desc": "La recommandation examine vos objectifs, compétences transférables et centres d'intérêt, au-delà des seuls mots-clés.",
        "query": "Rechercher poste, entreprise ou compétences", "sector": "Secteur", "contract": "Type de contrat", "source": "Source", "france": "Priorité France / exclure les villes étrangères évidentes", "all": "Tous",
        "rank": "Score de correspondance", "save": "Enregistrer l'offre", "saved": "Enregistrée", "apply": "Voir l'annonce originale", "reason": "Pourquoi cette recommandation ?", "overlap": "Compétences proches", "gaps": "Compétences à développer", "none": "Pas de mots-clés spécifiques communs. Consultez la description.",
        "deadline": "Date limite", "not_given": "Non indiquée", "match_notice": "Les scores expriment une similarité indicative, PAS une probabilité de recrutement. Vérifiez le contrat et la localisation.",
        "live_header": "Importer des offres actuelles", "live_help": "Ces API donnent accès aux offres publiques d'une entreprise à la fois. Saisissez son identifiant de job board (pas l'URL).",
        "load": "Importer les offres publiques", "live_success": "Offres importées", "live_error": "Import impossible", "notice_live": "Actualisation manuelle ; ces sources ne permettent pas une recherche universelle ni la vérification définitive des dates de clôture.",
        "manual": "Ajouter une offre manuellement", "company": "Entreprise", "title": "Intitulé du poste", "city": "Ville / lieu", "description": "Description", "skills": "Compétences (séparées par des virgules)", "job_url": "Lien original (facultatif)", "submit_job": "Ajouter l'offre", "manual_added": "Offre ajoutée au catalogue.",
        "tracker_header": "Suivi des candidatures", "tracker_desc": "Modifiez les statuts et les notes dans le tableau. Téléchargez votre suivi avant de fermer ou d'actualiser la page.",
        "empty_tracker": "Aucune candidature pour l'instant. Enregistrez une offre ou importez votre fichier de suivi.",
        "export": "Télécharger le suivi Excel", "export_csv": "Télécharger le suivi CSV", "import": "Importer un suivi Excel / CSV", "import_button": "Importer", "import_success": "Candidatures importées", "import_error": "Import impossible", "snapshot": "Télécharger une sauvegarde (JSON)", "restore": "Restaurer une sauvegarde", "restore_button": "Restaurer",
        "status": "Statut", "notes": "Notes", "upcoming": "Échéances à venir", "delayed": "Date limite dépassée", "unlisted": "Date limite non indiquée", "delete": "Supprimer", "monitor": "Vérifier la disponibilité", "monitor_description": "Après avoir actualisé les annonces d'une entreprise, une offre peut être recherchée dans le dernier flux. L'absence ne prouve pas la clôture.",
        "community_header": "Avançons ensemble.", "community_desc": "Posez vos questions, partagez vos entretiens et rencontrez d'autres candidats. Ce forum est une DÉMONSTRATION : vos messages restent limités à cette session.",
        "new_post": "Créer une discussion", "alias": "Pseudo (évitez les données personnelles)", "topic": "Sujet", "category": "Catégorie", "post": "Publier", "posted": "Votre message de démonstration est visible dans cette session.", "comment": "Répondre", "send_reply": "Envoyer la réponse", "all_discussions": "Fil communautaire", "community_note": "Toutes les conversations et réponses initiales sont fictives, y compris celles d'Alex Martin. Vos nouvelles réponses restent dans votre session. Il n'existe ni base de données communautaire partagée ni modération.", "group_link": "Lien facultatif vers un groupe étudiant", "group_link_help": "Les organisateurs peuvent fournir un lien Discord/WhatsApp vérifié. Ne partagez pas de CV ni de données personnelles dans un groupe non fiable.",
        "profile_header": "Des recommandations qui vous ressemblent.", "profile_desc": "Indiquez vos objectifs. Vous pouvez saisir votre parcours ou importer un CV contenant du texte sélectionnable.",
        "goal": "Objectif / postes recherchés", "location": "Lieu privilégié", "interest": "Secteurs recherchés", "profile_skills": "Compétences et expériences", "contracts": "Je recherche", "resume": "Importer un CV (PDF, DOCX, TXT)", "resume_ok": "Texte du CV extrait", "resume_err": "Lecture du fichier impossible", "cv_warning": "Les PDF scannés ne peuvent pas être lus ici. Indiquez manuellement votre parcours.", "save_profile": "Enregistrer le profil", "profile_saved": "Profil mis à jour. Les recommandations tiennent compte de vos critères.", "engine": "Moteur de recommandation", "engine_fast": "Référence rapide par similarité textuelle", "engine_ai": "Transformeur multilingue pré-entraîné (IA)", "model_error": "Modèle IA indisponible. Utilisation de la comparaison textuelle reproductible.", "current_engine": "Moteur actif", "recalculate": "Les résultats évoluent avec les informations de votre profil et les filtres.",
        "about_header": "Comment fonctionne CareerCollective", "about_desc": "Prototype pédagogique pour un projet d'IA, avec limites explicites.",
        "step1": "1. Présentez votre parcours et vos objectifs, ou importez un CV.", "step2": "2. Recherchez les offres publiques et les liens employeurs vérifiables ; les annonces fictives restent dans le mode démo.", "step3": "3. Consultez les recommandations expliquées et suivez vos candidatures.", "step4": "4. Échangez dans la communauté de démonstration et exportez vos données.",
        "data_note": "Le jeu de données fourni est fictif et destiné au test. Les offres en direct proviennent des flux publics des entreprises choisies et peuvent évoluer. Aucune candidature n'est envoyée automatiquement.",
        "download_data": "Télécharger les données de démonstration", "download_prompts": "Sources, références techniques et exemples de prompts figurent dans l'archive du projet.",
        "filter_none": "Aucun résultat. Élargissez les filtres ou ajoutez une offre manuellement.",
    }
}

if "language" not in st.session_state:
    st.session_state.language = "en"
if "nav_page" not in st.session_state:
    st.session_state.nav_page = "discover"
if "cc_calendar_filter" not in st.session_state:
    st.session_state.cc_calendar_filter = "all"
if "cc_calendar_month" not in st.session_state:
    st.session_state.cc_calendar_month = date.today().replace(day=1).isoformat()
if "cc_calendar_date" not in st.session_state:
    st.session_state.cc_calendar_date = date.today().isoformat()
if "demo_workspace" not in st.session_state:
    st.session_state.demo_workspace = True
if "profile_data" not in st.session_state:
    st.session_state.profile_data = load_demo_profile(ROOT)
if "manual_jobs" not in st.session_state: st.session_state.manual_jobs = []
if "live_jobs" not in st.session_state: st.session_state.live_jobs = []
if "featured_jobs" not in st.session_state: st.session_state.featured_jobs = []
if "live_feed_errors" not in st.session_state: st.session_state.live_feed_errors = []
if "live_feed_count" not in st.session_state: st.session_state.live_feed_count = 0
if "tracker_rows" not in st.session_state:
    st.session_state.tracker_rows = load_demo_tracker(ROOT)
if "discussions" not in st.session_state:
    st.session_state.discussions = load_demo_discussions(ROOT)
if "live_board_checks" not in st.session_state: st.session_state.live_board_checks = {}
if "community_link" not in st.session_state: st.session_state.community_link = ""

language = st.session_state.language

def tr(key):
    return TEXT[language].get(key, TEXT["en"].get(key, key))


def render_headline(eyebrow, title, subtitle):
    st.markdown(f"<div class='hero'><p class='eyebrow'>{html.escape(eyebrow)}</p><h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p></div>", unsafe_allow_html=True)


def show_demo_warning():
    st.markdown(f"<div class='disclaimer'><b>{html.escape(tr('demo'))}</b> | {html.escape(tr('info'))}</div>", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def sample_jobs():
    df = pd.read_csv(ROOT / "data/sample_jobs.csv", dtype=str).fillna("")
    return [normalize_job(row) for row in df.to_dict("records")]


@st.cache_resource(show_spinner=False)
def load_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


@st.cache_data(show_spinner=False)
def observed_employer_jobs():
    df = pd.read_csv(ROOT / "data/observed_employer_listings.csv", dtype=str).fillna("")
    return [normalize_job(row) for row in df.to_dict("records")]


@st.cache_data(ttl=1800, show_spinner=False)
def cached_featured_jobs():
    return fetch_featured_jobs()


def all_jobs():
    mode = st.session_state.get("catalog_mode", "Employer listings")
    if mode == "Demonstration data":
        return deduplicate_jobs(sample_jobs() + st.session_state.manual_jobs)
    if mode == "Live feeds only":
        return deduplicate_jobs(st.session_state.featured_jobs + st.session_state.live_jobs + st.session_state.manual_jobs)
    # Recently observed URLs are distinct from actively refreshed employer feeds.
    # Put fetched jobs last so current live-feed metadata wins on duplicate URLs.
    return deduplicate_jobs(observed_employer_jobs() + st.session_state.featured_jobs + st.session_state.live_jobs + st.session_state.manual_jobs)


def save_job(job):
    st.session_state.tracker_rows[job["id"]] = make_tracker_row(job)


with st.sidebar:
    st.markdown("## CareerCollective")
    st.caption(tr("subtitle"))
    chosen = st.segmented_control("Language / Langue", ["English", "Français"], default="Français" if language == "fr" else "English")
    new_lang = "fr" if chosen == "Français" else "en"
    if new_lang != st.session_state.language:
        st.session_state.language = new_lang
        st.rerun()
    st.divider()
    pages = ["discover", "tracker", "calendar", "community", "profile", "about"]
    chosen_page = st.radio("Navigation", pages, format_func=tr, label_visibility="collapsed", key="nav_page")
    st.divider()
    engine_label = st.selectbox(tr("engine"), ["semantic", "baseline"], format_func=lambda x: tr("engine_ai") if x == "semantic" else tr("engine_fast"), index=1)
    st.caption("Multilingual sentence embeddings · Hugging Face" if engine_label == "semantic" else "Character n-gram TF-IDF · scikit-learn")
    if chosen_page == "discover":
        catalog_mode = st.radio(
            "Job catalogue / Catalogue d'offres",
            ["Employer listings", "Live feeds only", "Demonstration data"],
            format_func=lambda x: {
                "Employer listings": "Employer listings / Offres d'employeurs",
                "Live feeds only": "Live feeds only / Flux actualisés",
                "Demonstration data": "Demonstration only / Démonstration",
            }[x],
            key="catalog_mode",
        )
    st.divider()
    st.caption("ESSEC student project · 2026  |  v1.0")
    st.caption("No account | Session-only | Educational demo")
    with st.expander("Sample workspace / Espace fictif", expanded=False):
        st.caption("Fictional candidate Alex Martin, with sample applications and replies. No employer application has actually been sent.")
        if st.button("Reload fictional example / Recharger la démo", key="reload_demo"):
            st.session_state.profile_data = load_demo_profile(ROOT)
            st.session_state.tracker_rows = load_demo_tracker(ROOT)
            st.session_state.discussions = load_demo_discussions(ROOT)
            st.session_state.demo_workspace = True
            st.session_state.pop("tracker_editor", None)
            st.rerun()
        if st.button("Start with empty profile / Profil vierge", key="blank_demo"):
            st.session_state.profile_data = empty_profile()
            st.session_state.tracker_rows = {}
            st.session_state.discussions = load_demo_discussions(ROOT)
            st.session_state.demo_workspace = False
            st.session_state.pop("tracker_editor", None)
            st.rerun()

model = None
using_semantic = engine_label == "semantic"
if chosen_page == "discover" and using_semantic:
    try:
        with st.spinner("Loading multilingual AI model / Chargement du modèle IA…"):
            model = load_model()
    except Exception as exc:
        using_semantic = False
        st.warning(tr("model_error") + f" ({type(exc).__name__})")

if chosen_page == "discover" and st.session_state.get("catalog_mode") != "Demonstration data":
    with st.spinner("Checking public employer job boards / Consultation des offres publiques..."):
        fresh, failures, checked = cached_featured_jobs()
    st.session_state.featured_jobs = fresh
    st.session_state.live_feed_errors = failures
    st.session_state.live_feed_count = checked

jobs = all_jobs()
tracked = list(st.session_state.tracker_rows.values())
near = sum(days_until_deadline(j) is not None and 0 <= days_until_deadline(j) <= 7 and j.get("status") == "Saved" for j in tracked)

if chosen_page == "discover":
    render_headline("Career discovery, reimagined" if language == "en" else "Découvrez votre avenir", tr("welcome"), tr("mission"))
    render_status_strip(tracked, language)
    stats = st.columns(4)
    for col, value, label in zip(stats, [len(jobs), len(tracked), near, len(st.session_state.discussions)], [tr("total"), tr("tracked"), tr("soon"), tr("posts")]):
        col.metric(label, value)
    show_demo_warning()
    if st.session_state.get("catalog_mode") != "Demonstration data":
        total_live = len(st.session_state.featured_jobs)
        observed_total = len(observed_employer_jobs())
        st.caption((f"Checked {st.session_state.live_feed_count}/8 public employer boards. "
                    f"{total_live} France-based student roles found in current feeds; "
                    f"{observed_total} previously observed employer links also available for reference. "
                    "A previously observed link is not a claim that the job is still open.") if language == "en" else
                   (f"{st.session_state.live_feed_count}/8 sites employeurs consultés. "
                    f"{total_live} offres étudiant en France trouvées dans les flux ; "
                    f"{observed_total} liens repérés précédemment à vérifier."))
        if st.session_state.live_feed_errors:
            with st.expander("Sources unavailable / Sources indisponibles"):
                st.write("; ".join(st.session_state.live_feed_errors))
        if st.button("Refresh live listings / Actualiser les offres"):
            cached_featured_jobs.clear()
            st.rerun()
    st.write("")
    st.subheader(tr("matches"))
    st.caption(tr("find_desc"))
    search_col, city_col = st.columns([2, 1])
    query = search_col.text_input(tr("query"), placeholder="e.g. marketing, data, événementiel")
    city_query = city_col.text_input("City / Ville", placeholder="Paris, Lyon, ...")
    fc1, fc2, fc3 = st.columns(3)
    sector_options = ["All"] + sorted(set(j["sector"] for j in jobs if j["sector"]))
    sectors = fc1.selectbox(tr("sector"), sector_options, format_func=lambda x: tr("all") if x == "All" else x)
    contracts = fc2.selectbox(tr("contract"), ["All", "Internship", "Apprenticeship", "Other / unknown"], format_func=lambda x: {"All": tr("all"), "Internship": "Stage / Internship", "Apprenticeship": "Alternance / Apprenticeship", "Other / unknown": "Other / À confirmer"}.get(x, x))
    sources = fc3.selectbox(tr("source"), ["All"] + sorted(set(j["source_type"] for j in jobs)), format_func=lambda x: tr("all") if x == "All" else x)
    france_filter = st.checkbox(tr("france"), value=True)
    st.write("")
    with st.expander(tr("live_header") + "  -  additional employer board", expanded=False):
        st.caption(tr("live_help"))
        provider = st.selectbox("Source API", ["Greenhouse", "Lever (global)", "Lever (EU)"])
        slug = st.text_input("Employer board identifier / Identifiant", placeholder="e.g. greenhouse board token or Lever site")
        only_student_roles = st.checkbox("Only student-oriented roles / Stages et alternances uniquement", value=True)
        if st.button(tr("load"), disabled=not slug.strip()):
            try:
                with st.spinner("Fetching published postings…"):
                    if provider == "Greenhouse": new = fetch_greenhouse(slug.strip())
                    else: new = fetch_lever(slug.strip(), "eu" if provider.endswith("EU)") else "global")
                if only_student_roles: new = [j for j in new if j["contract"] in ("Internship", "Apprenticeship")]
                src_key = f"{provider}:{slug.strip()}"
                # Replace only the board's previously imported listings.
                old_ids = set(st.session_state.live_board_checks.get(src_key, {}).get("job_ids", []))
                st.session_state.live_jobs = [j for j in st.session_state.live_jobs if j["id"] not in old_ids] + new
                st.session_state.live_board_checks[src_key] = {"job_ids": [j["id"] for j in new], "date": date.today().isoformat(), "checked_jobs": new}
                st.toast(f"{tr('live_success')}: {len(new)}")
                st.rerun()
            except Exception as exc:
                st.error(f"{tr('live_error')}: {exc}")
    with st.expander(tr("manual"), expanded=False):
        with st.form("manual_role"):
            a,b = st.columns(2)
            company = a.text_input(tr("company"))
            job_title = b.text_input(tr("title"))
            city = a.text_input(tr("city"), value="Paris")
            contract = b.selectbox(tr("contract"), ["Internship", "Apprenticeship", "Other / unknown"])
            sector = a.text_input(tr("sector"), value="Other")
            job_url = b.text_input(tr("job_url"))
            desc = st.text_area(tr("description"), height=100)
            skills = st.text_input(tr("skills"))
            has_deadline = st.checkbox("Deadline published / Date limite publiée")
            deadline = st.date_input(tr("deadline"), value=date.today()) if has_deadline else None
            submitted = st.form_submit_button(tr("submit_job"), type="primary")
        if submitted:
            if not company.strip() or not job_title.strip(): st.error("Company and role title are required / Entreprise et poste obligatoires")
            elif job_url and not safe_url(job_url): st.error("Only valid http(s) URLs are accepted")
            else:
                item = normalize_job({"id": "manual:" + str(pd.Timestamp.now().value), "company": company,
                    "title": job_title, "city": city, "contract": contract, "sector": sector,
                    "description": desc, "skills": skills, "url": job_url,
                    "deadline": deadline.isoformat() if deadline else "", "source": "Manually entered",
                    "source_type": "Manual", "first_seen": date.today().isoformat()})
                st.session_state.manual_jobs.append(item)
                st.success(tr("manual_added"))
                st.rerun()

    listing = filter_jobs(jobs, query, sectors, contracts, sources, france_filter)
    if city_query.strip():
        listing = [j for j in listing if city_query.casefold().strip() in j.get("city", "").casefold()]
    ranked, actual_engine = rank_jobs(listing, st.session_state.profile_data, using_semantic, model)
    st.caption(f"{tr('current_engine')}: {'Multilingual pretrained transformer / Transformeur multilingue' if actual_engine == 'multilingual-transformer' else 'TF-IDF baseline / Référence TF-IDF'} · {len(ranked)} results")
    st.info(tr("match_notice"))
    if not ranked:
        st.warning(tr("filter_none"))
    result_limit = st.select_slider("Visible recommendations / Recommandations affichées", options=[5, 8, 12, 20, 30], value=8)
    for job in ranked[:result_limit]:
        with st.container(border=True):
            c1,c2 = st.columns([4,1.2])
            with c1:
                st.markdown(f"### {html.escape(professional_text(job['title']))}")
                st.markdown(f"**{html.escape(professional_text(job['company']))}**  ·  {html.escape(professional_text(job['city'] or 'Location not specified'))}")
                st.caption(f"{job['contract']}  ·  {job['sector']}  ·  {job['source']}")
            with c2:
                st.metric(tr("rank"), f"{job['score']} / 100")
                if job["source_type"] == "Demo data": st.caption("FICTIONAL / FICTIF")
                elif job["source_type"] == "Live feed": st.caption("PUBLIC EMPLOYER FEED / FLUX PUBLIC")
                elif job["source_type"] == "Employer link  -  verify": st.caption("PREVIOUSLY OBSERVED  -  VERIFY / LIEN À VÉRIFIER")
                else: st.caption("MANUAL / MANUEL")
            st.write(professional_text((job["description"][:330] + "…") if len(job["description"])>330 else job["description"]))
            if job["deadline"]:
                remaining = days_until_deadline(job)
                deadline_text = job["deadline"]
                if remaining is not None and remaining < 0: deadline_text += f" · {tr('delayed')}"
                elif remaining is not None and remaining <= 7: deadline_text += f" · {remaining} days / jours"
            else:
                deadline_text = tr("not_given")
            st.caption(f"{tr('deadline')}: {deadline_text}")
            with st.expander(tr("reason")):
                st.write(f"**{tr('overlap')}:** " + (", ".join(job["shared_skills"]) if job["shared_skills"] else tr("none")))
                st.write(f"**{tr('gaps')}:** " + (", ".join(job["missing_skills"]) if job["missing_skills"] else " - "))
                st.caption("Similarity + transparent skill overlap; this is not a predictor of hiring decisions.")
            b1,b2,b3 = st.columns([1.6,1.6,3])
            with b1:
                if job["id"] in st.session_state.tracker_rows:
                    st.button(tr("saved"), key="already-"+job["id"], disabled=True)
                elif st.button(tr("save"), key="save-"+job["id"], type="primary"):
                    save_job(job); st.rerun()
            with b2:
                if job["url"]:
                    st.link_button(tr("apply"), job["url"])

elif chosen_page == "calendar":
    render_headline("Track what comes next" if language == "en" else "Anticipez vos échéances",
                    "Application calendar" if language == "en" else "Calendrier des candidatures",
                    "Click a date to review deadlines and application activity. Your tracker updates the calendar immediately." if language == "en" else "Cliquez sur une date pour afficher les échéances et les candidatures. Le calendrier suit les changements du tableau.")
    show_demo_warning()
    render_status_strip(tracked, language)
    render_calendar(tracked, language)

elif chosen_page == "tracker":
    render_headline("Your application workspace" if language == "en" else "Votre espace candidatures", tr("tracker_header"), tr("tracker_desc"))
    show_demo_warning()
    render_status_strip(tracked, language)
    if tracked:
        summary = st.columns(4)
        counts = {status: sum(item["status"] == status for item in tracked) for status in STATUSES}
        for col, label, count in zip(summary,
            ["Saved / Enregistrées", "Applied / Envoyées (simulées)", "Interviews / Entretiens", "Deadlines soon / Échéances proches"],
            [counts["Saved"], counts["Applied"], counts["Interview"], near]):
            col.metric(label, count)
        if st.session_state.demo_workspace:
            st.caption("EXAMPLE RECORDS ONLY. 'Applied' and 'Interview' statuses are part of a fictional applicant journey; no employer has received an application.")
    if not tracked: st.info(tr("empty_tracker"))
    else:
        st.caption("Edit status, deadline, application date or notes directly in the table. Other columns are locked. / Modifiez directement le statut, les dates et les notes.")
        df = pd.DataFrame(tracked, columns=TRACKER_COLUMNS).fillna("")
        edited = st.data_editor(df, hide_index=True, use_container_width=True, num_rows="fixed",
            disabled=["job_id", "company", "title", "city", "contract", "url", "source"],
            column_config={
                "status": st.column_config.SelectboxColumn(tr("status"), options=STATUSES, required=True),
                "url": st.column_config.LinkColumn("URL"),
                "notes": st.column_config.TextColumn(tr("notes"), max_chars=2000),
                "deadline": st.column_config.TextColumn(tr("deadline"), help="YYYY-MM-DD"),
            }, key="tracker_editor")
        rows_now = []
        for row in edited.fillna("").to_dict("records"):
            row["deadline"] = normalize_date(row["deadline"])
            row["applied_on"] = normalize_date(row["applied_on"])
            rows_now.append(row)
        st.session_state.tracker_rows = {r["job_id"]: r for r in rows_now}
        tracked = rows_now
        dl1,dl2,dl3 = st.columns([1.2,1.2,2])
        dl1.download_button(tr("export"), export_tracker_xlsx(tracked), "CareerCollective_applications.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
        dl2.download_button(tr("export_csv"), pd.DataFrame(tracked, columns=TRACKER_COLUMNS).to_csv(index=False).encode("utf-8-sig"), "CareerCollective_applications.csv", mime="text/csv")
        if tracked:
            remove_id = dl3.selectbox(tr("delete"), [" - "] + [r["job_id"] for r in tracked], format_func=lambda v: v if v == " - " else next((f"{r['company']} | {r['title']}" for r in tracked if r['job_id'] == v), v))
            if remove_id != " - " and dl3.button(" " + tr("delete"), key="remove_saved"):
                st.session_state.tracker_rows.pop(remove_id, None); st.rerun()
        st.subheader(tr("upcoming"))
        future = [(days_until_deadline(row),row) for row in tracked]
        future = sorted([(d,j) for d,j in future if d is not None and d>=0 and j["status"] == "Saved"], key=lambda x:x[0])
        if future:
            for days,job in future[:8]:
                st.markdown(f"**{html.escape(job['company'])} · {html.escape(job['title'])}**  -  {job['deadline']} · {days} days / jours")
        else: st.caption(tr("unlisted"))
        with st.expander(tr("monitor")):
            st.caption(tr("monitor_description"))
            for r in tracked:
                if "Greenhouse ·" in r["source"] or "Lever ·" in r["source"]:
                    board_name = r["source"].split(" · ",1)[-1]
                    board_matches = [v for k,v in st.session_state.live_board_checks.items() if k.endswith(":"+board_name)]
                    if board_matches:
                        latest = board_matches[-1]
                        status = monitored_status(r, latest["checked_jobs"], True)
                    else: status = monitored_status(r, [], False)
                    st.write(f"{r['company']} · {r['title']}: **{status}**")
    st.divider()
    st.subheader(tr("import"))
    uploaded = st.file_uploader("Excel / CSV", type=["xlsx", "csv"], key="tracker_import")
    if st.button(tr("import_button"), disabled=uploaded is None):
        try:
            items = import_tracker(uploaded.getvalue(), uploaded.name)
            for r in items: st.session_state.tracker_rows[r["job_id"]] = r
            st.success(f"{tr('import_success')}: {len(items)}")
            st.rerun()
        except Exception as exc: st.error(f"{tr('import_error')}: {exc}")
    st.divider()
    backup = {
        "version": 1, "profile": st.session_state.profile_data,
        "tracker": list(st.session_state.tracker_rows.values()),
        "manual_jobs": st.session_state.manual_jobs,
        "community_posts": [p for p in st.session_state.discussions if str(p.get("id","")).startswith("user-")],
    }
    st.download_button(tr("snapshot"), json.dumps(backup, ensure_ascii=False, indent=2).encode("utf-8"), "CareerCollective_session.json", mime="application/json")
    with st.expander(tr("restore")):
        backup_file = st.file_uploader("JSON", type="json")
        if st.button(tr("restore_button"), disabled=backup_file is None):
            try:
                if backup_file.size > 3_000_000: raise ValueError("Backup is too large")
                loaded = json.loads(backup_file.getvalue().decode("utf-8"))
                if loaded.get("version") != 1 or not isinstance(loaded.get("tracker"), list): raise ValueError("Not a valid CareerCollective backup")
                st.session_state.profile_data = loaded.get("profile", st.session_state.profile_data)
                st.session_state.manual_jobs = [normalize_job(x) for x in loaded.get("manual_jobs", [])[:300] if isinstance(x,dict)]
                safe_rows = {}
                for r in loaded["tracker"][:500]:
                    if isinstance(r,dict) and r.get("job_id"):
                        row = {key: clean_text(r.get(key,""), 2000) for key in TRACKER_COLUMNS}
                        row["status"] = row["status"] if row["status"] in STATUSES else "Saved"
                        row["url"] = safe_url(row["url"])
                        row["deadline"] = normalize_date(row["deadline"])
                        row["applied_on"] = normalize_date(row["applied_on"])
                        safe_rows[str(r["job_id"])] = row
                st.session_state.tracker_rows = safe_rows
                for p in loaded.get("community_posts", [])[:100]:
                    if isinstance(p,dict) and str(p.get("id", "")).startswith("user-"):
                        st.session_state.discussions.append({key: clean_text(p.get(key, ""), 2000) for key in ("id", "author", "category", "sector", "title", "body", "posted")} | {"replies":0,"user_replies":[]})
                st.success("Session restored / Session restaurée")
                st.rerun()
            except Exception as exc: st.error(f"Backup error: {exc}")

elif chosen_page == "community":
    render_headline("CareerCollective Community", tr("community_header"), tr("community_desc"))
    st.markdown("<span class='tiny-pill'>Ask / Questions</span><span class='tiny-pill'>Interviews / Entretiens</span><span class='tiny-pill'>Find your peers / Réseau</span>", unsafe_allow_html=True)
    st.info(tr("community_note"))
    if st.session_state.demo_workspace:
        st.caption("Alex Martin (DEMO) has started a discussion and replied to classmates below. These are example messages, not interactions with real users.")
    with st.expander(tr("new_post")):
        with st.form("post_form", clear_on_submit=True):
            name = st.text_input(tr("alias"), placeholder="Student_2026")
            category = st.selectbox(tr("category"), ["Ask the community", "Interview experiences", "Find your peers"])
            sector = st.selectbox(tr("sector"), ["General", "Marketing", "Hospitality", "Events", "Finance", "Consulting", "Technology", "Human Resources", "Design", "Other"])
            topic = st.text_input(tr("topic"), max_chars=140)
            body = st.text_area("Message", height=105, max_chars=1500)
            submit = st.form_submit_button(tr("post"), type="primary")
        if submit:
            if not all(x.strip() for x in [name, topic, body]): st.error("Name, title and message required / Pseudo, titre et message obligatoires")
            else:
                st.session_state.discussions.insert(0, {
                    "id": "user-" + str(pd.Timestamp.now().value), "author": clean_text(name, 45),
                    "category": category, "sector": sector, "title": clean_text(topic, 140),
                    "body": clean_text(body, 1500), "replies": 0,
                    "posted": date.today().isoformat(), "user_replies": [],
                })
                st.success(tr("posted")); st.rerun()
    st.subheader(tr("all_discussions"))
    cat_filter = st.selectbox(tr("category"), ["All", "Ask the community", "Interview experiences", "Find your peers"], format_func=lambda x: tr("all") if x == "All" else x)
    for p in st.session_state.discussions:
        if cat_filter != "All" and p["category"] != cat_filter: continue
        with st.container(border=True):
            st.caption(f"{p['category']}  ·  {p['sector']}  ·  {p['posted']}")
            st.markdown(f"### {html.escape(str(p['title']))}")
            st.write(str(p["body"]))
            st.caption(f"{p['author']}  ·  {int(p['replies']) + len(p['user_replies'])} replies / réponses")
            for reply in p["user_replies"]:
                st.markdown(f"**{html.escape(reply['author'])}:** {html.escape(reply['text'])}")
            with st.expander(tr("comment")):
                with st.form("reply_"+str(p["id"]), clear_on_submit=True):
                    author = st.text_input(tr("alias"), key="author_"+str(p["id"]))
                    message = st.text_area("Message", max_chars=700, key="message_"+str(p["id"]))
                    sent = st.form_submit_button(tr("send_reply"))
                if sent and author.strip() and message.strip():
                    p["user_replies"].append({"author": clean_text(author, 45), "text": clean_text(message, 700)})
                    st.rerun()
                elif sent: st.error("Please enter a name and a reply.")
    with st.expander(tr("group_link")):
        st.caption(tr("group_link_help"))
        group_url = st.text_input("Verified invitation URL / Lien d'invitation vérifié", value=st.session_state.community_link)
        if st.button("Save link / Enregistrer le lien"):
            st.session_state.community_link = safe_url(group_url)
            if group_url and not st.session_state.community_link: st.error("Use a complete http(s) URL")
        if st.session_state.community_link:
            st.link_button("Join external group / Rejoindre le groupe", st.session_state.community_link)

elif chosen_page == "profile":
    render_headline("My career profile" if language == "en" else "Mon parcours", tr("profile_header"), tr("profile_desc"))
    show_demo_warning()
    if st.session_state.demo_workspace:
        st.subheader("Alex Martin | Fictional example candidate")
        st.caption("This sample CV is already loaded for the matching algorithm. It contains no real person's information. You may replace it with a CV using the form below.")
        col_pdf, col_txt = st.columns([1,1])
        with col_pdf:
            st.download_button("Download fictional CV (PDF) / Télécharger le CV fictif", (ROOT / "data/Alex_Martin_Fictional_CV.pdf").read_bytes(), file_name="Alex_Martin_Fictional_CV.pdf", mime="application/pdf")
        with col_txt:
            st.download_button("Download fictional CV (TXT)", (ROOT / "data/example_cv.txt").read_bytes(), file_name="Alex_Martin_Fictional_CV.txt", mime="text/plain")
        with st.expander("Preview fictional CV / Aperçu du CV fictif"):
            st.text(st.session_state.profile_data.get("cv_text", "")[:5000])
    profile = st.session_state.profile_data
    with st.form("career_profile"):
        goal = st.text_area(tr("goal"), value=profile.get("goal", ""), height=105)
        col1,col2 = st.columns(2)
        skills = col1.text_area(tr("profile_skills"), value=profile.get("skills", ""), height=100)
        sectors = col2.text_area(tr("interest"), value=profile.get("sectors", ""), height=100)
        location = st.text_input(tr("location"), value=profile.get("location", ""))
        contracts = st.multiselect(tr("contracts"), ["Internship", "Apprenticeship", "Other / unknown"], default=profile.get("contracts", ["Internship", "Apprenticeship"]))
        cv = st.file_uploader(tr("resume"), type=["pdf", "docx", "txt"])
        submitted = st.form_submit_button(tr("save_profile"), type="primary")
    if submitted:
        text_cv = profile.get("cv_text", "")
        if cv is not None:
            try:
                text_cv = extract_cv(cv.name, cv.getvalue())
                if len(text_cv.strip()) < 50: st.warning(tr("cv_warning"))
                else: st.success(f"{tr('resume_ok')}: {len(text_cv)} characters")
            except Exception as exc: st.warning(f"{tr('resume_err')}: {exc}")
        st.session_state.profile_data = {"goal": clean_text(goal, 1200), "skills": clean_text(skills, 2500), "sectors": clean_text(sectors, 1000), "location": clean_text(location, 150), "contracts": contracts, "cv_text": text_cv}
        if cv is not None:
            st.session_state.demo_workspace = False
        st.success(tr("profile_saved"))
    st.subheader("Profile insights / Aperçu des données")
    st.write(f"**{tr('goal')}:** {st.session_state.profile_data['goal']}")
    st.write(f"**{tr('profile_skills')}:** {st.session_state.profile_data['skills']}")
    st.caption(f"CV text length / Longueur du texte CV: {len(st.session_state.profile_data['cv_text'])} characters · {tr('recalculate')}")

elif chosen_page == "about":
    render_headline("Transparency by design", tr("about_header"), tr("about_desc"))
    for key in ("step1","step2","step3","step4"): st.markdown(tr(key))
    st.divider()
    st.subheader("Matching / Correspondance")
    st.write("**AI mode:** sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2, cosine similarity of multilingual sentence embeddings, plus an explicit skills overlap component and location/contract preference adjustments.")
    st.write("**Fallback mode:** scikit-learn character-level TF-IDF with the same structured adjustments. This ensures the app runs even when a large pretrained model cannot download.")
    st.write("Scores measure relative textual fit, not interview likelihood or objective suitability. Review every recommendation critically.")
    st.subheader("Job data / Données des offres")
    st.write(tr("data_note"))
    st.markdown("**Current employer feeds:** Vestiaire Collective, Bigblue, Cheerz, Scaleway, Ekimetrics, C12 Quantum Electronics, Aircall and Mirakl. These employer job boards are fetched using public Greenhouse / Lever APIs. **Previously observed employer links** are provided as a separate, clearly labeled offline reference, not as confirmation of a current vacancy.")
    st.write("Selected company feeds are checked on demand or cached for 30 minutes. Public listings are not guaranteed to remain open; advertised deadlines are shown only when explicitly published.")
    st.markdown("- [Greenhouse public Job Board API](https://developers.greenhouse.io/job-board.html)  -  unauthenticated public GETs for a specific employer board.\n- [Lever public Postings API](https://github.com/lever/postings-api)  -  public posts for a specific employer site.\n- Previously observed employer listings CSV  -  real employer links observed in October 2026; availability must be verified.\n- Local demonstration CSV  -  fictional examples, never represented as live jobs.")
    st.download_button(tr("download_data"), (ROOT / "data/sample_jobs.csv").read_bytes(), "CareerCollective_demo_jobs.csv", "text/csv")
    st.subheader("Privacy & limitations / Confidentialité et limites")
    st.write("The starter profile, the marked Applied statuses, interview progress and community activity are all fictional demonstrations. No applications have been sent, and no real students participated. No logins, server-side database, shared persistent community, notifications, automatic applications or universal web scraping are provided. Session state is temporary; uploaded CV text is processed in hosted server memory.")
    st.write(tr("download_prompts"))

st.divider()
st.caption("CareerCollective · Academic proof of concept · 2026 · Transparent sample data · Human judgment comes first")