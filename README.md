# CareerCollective  -  Professional blue/white edition
**Find your path. Track your progress. Grow together.**

CareerCollective is a **bilingual (English/French) educational web application** for students searching for internships and apprenticeships in France. It combines explainable AI-powered matching, public job-board feed ingestion, a reusable application tracker, and a **clearly labeled session-only community prototype**.

> **Important:** The 16 supplied sample jobs and 7 community threads are **fictional**. The 12 *previously observed employer links* in `data/observed_employer_listings.csv` point to real company-hosted vacancy pages discovered in October 2026 but **must be rechecked at the source**. Live job-feed results reflect the latest successful API request and may change.

## Finding real opportunities

On **Discover**, leave the **Employer listings** catalogue selected (default). CareerCollective fetches public Greenhouse and Lever postings from eight curated employers: Vestiaire Collective, Bigblue, Cheerz, Scaleway, Ekimetrics, C12 Quantum Electronics, Aircall and Mirakl. Search by keyword and city; filter by industry, internship versus apprenticeship, and source. Links open the official employer posting. Use **Refresh live listings** to clear the 30-minute feed cache.

You can switch to **Live feeds only** to hide previously observed employer links, or **Demonstration data** to show the fictional student dataset. If company APIs are unavailable, the employer-links mode still shows previously observed real URLs with prominent verification notices. This app is **not** a universal crawler and does not promise comprehensive French job-board coverage. Application deadlines are displayed only if explicitly present in the employer content.

## Interface

The UI uses white, navy and blue with text-only navigation and no decorative emojis. The fast TF-IDF model is selected initially for responsiveness; switch to the multilingual pretrained Hugging Face transformer using the sidebar selector for the AI-driven demonstration.

> **Important:** The 16 supplied sample jobs and 7 community threads are **fictional**. They are not open vacancies, real individuals, or indicators of employer recruitment. The application does not submit job applications or send notifications.


## Preloaded fictional demo account

At first launch, CareerCollective opens with **Alex Martin (FICTIONAL)**, an entirely invented candidate. The sample CV is preloaded into the matching profile and downloadable as `data/Alex_Martin_Fictional_CV.pdf` or `data/example_cv.txt`. Seven sample tracked applications demonstrate Saved, Applied, Interview and Rejected statuses. Fictional deadlines are attached only to fictional demo jobs, and an authored community question plus illustrative replies show discussion participation. **No real applications were sent, and no real students are represented.**

Use **Sample workspace** in the sidebar to reload the fictional example or start with an empty profile. Changes in the shared Streamlit demo are session-only. The example application data are stored in `data/demo_applications.csv`, the profile in `data/demo_profile.json`, and sample replies in `data/demo_community_replies.csv`.

## Start locally

Supported: Python 3.11 - 3.13, browser, internet connection for *optional* pretrained-model download and live feeds.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

The Streamlit terminal displays the local web URL (usually http://localhost:8501).

For a quicker, lighter install without downloading the pretrained model:

```bash
python -m pip install -r requirements-lite.txt
streamlit run app.py
```

Choose **Fast text-similarity baseline** in the sidebar. The full AI model is not bundled as weights and is fetched from Hugging Face at first use. This avoids redistributing model files and keeps the source archive small.

## AI and reproducibility

The **AI matching mode** calls pretrained `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, hosted on Hugging Face, and compares candidate text with job-title/description embeddings using cosine similarity. The recommender incorporates a small auditable bilingual skill vocabulary, explicit location preference adjustment, and the selected contract types. The score is **not calibrated** and **is not a hiring probability**.

The reproducible **fallback** uses character n-gram TF-IDF (`scikit-learn`) and the same rule-based explanation. When the pretrained model is unavailable, the interface names the fallback engine instead of presenting it as pretrained AI.

### Live data sources

- **Greenhouse public Job Board API:** `GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true`
- **Lever public Postings API:** `GET https://api.lever.co/v0/postings/{site}?mode=json` (EU endpoint can also be selected).

The user must supply the company board identifier. Public GET endpoints generally require no authentication. These APIs provide **employer-specific listings, not an all-company search index**. Some boards will return zero matching internships; deleted postings may disappear. The app never claims that a missing job is definitely closed. Not all posts contain a closing date; blank dates are displayed as **not published**. Job feeds are fetched on explicit user action only. The sample dataset works without network access.

## Features

1. **Discover:** search/filter across sample, manual and fetched live opportunities, AI or baseline ranking, fit explanations, skills to explore, save to tracker, open original live link.
2. **My applications:** editable application statuses, notes, explicit deadlines, dated reminders on-screen, Excel/CSV export, import existing Excel/CSV, JSON backup/restore.
3. **Community:** illustrative threads, session-only new discussions and replies, category filters, optional link to organizer-approved external group.
4. **My profile:** ambitions, skills, sectors, location, contract preferences; optional TXT/PDF/DOCX CV text extraction.
5. **About:** methods, limitations, datasets, and sources.

## Limitations and responsible use

- **No user login or permanent backend.** `st.session_state` is per browser connection. Refreshing/reconnecting may reset the data. Export JSON backup or Excel/CSV before leaving. Posts are not shared across different users.
- **Privacy:** CVs are processed in the server's session memory; don't upload real sensitive information to a public student demo. For recording the 5-minute video, use `data/example_cv.txt`.
- **No OCR:** PDFs with scanned images typically yield little/no extracted text.
- **Date indicators:** only explicit dates in the sample data, manually entered posts or matched deadline phrases are used. No guessed closing dates.
- **No automated application submission or unauthorized job scraping.** External recruitment websites may change or rate-limit their APIs.
- **No actual notification scheduler:** deadlines are highlighted when the application is opened.
- **No persisted community nor moderation** in this prototype. A shared production community would require authentication, storage, moderation and privacy compliance.
- **Language:** controls are bilingual. Job descriptions remain in the original language; content is not automatically translated.

## Deploy to Streamlit Community Cloud

1. Create a GitHub repository named `careercollective` (can be public for class evaluation; **never commit personal CVs or credentials**).
2. Upload every file in this directory **including** `.streamlit/config.toml`, `data/`, `requirements.txt`, `app.py`, `core.py` and `sources.py`.
3. Sign in at [share.streamlit.io](https://share.streamlit.io/) using GitHub, choose **Create app** → your repository and branch → main file `app.py` → Deploy.
4. Share the resulting `https://...streamlit.app` address. This URL is issued **only after deployment**; it cannot be generated by this source archive.
5. On first launch, the semantic model may need to download. If hosting memory/network limits cause an issue, replace `requirements.txt` with `requirements-lite.txt` and use the explicitly labeled TF-IDF fallback. For the final AI grading demonstration, record the working pretrained-model mode on a machine where it is available.

The project itself does **not** create a public URL, and it cannot publish to your personal GitHub without account authorization.

## File list

- `app.py`: Streamlit application and translated UI
- `core.py`: matching, CV extraction, normalization, tracker utilities
- `sources.py`: public Greenhouse and Lever sources
- `data/sample_jobs.csv`: 16 fictional job examples
- `data/sample_discussions.csv`: 6 fictional community threads
- `data/example_cv.txt`, `data/example_tracker.csv`: safe video-test materials
- `tests/test_core.py`: unit tests with mocked APIs
- `evaluate_matching.py`: small fully synthetic benchmark; use `--semantic` for an illustrative AI/baseline comparison
- `CareerCollective_User_Guide.pdf`: printable bilingual two-page guide
- `TEST_REPORT.md`: what was verified and what must still be smoke-tested
- `USER_GUIDE.md`: step-by-step user guide
- `DEMO_SCRIPT.md`: 5-minute demonstration outline
- `AI_USE_LOG.md`: prompts and AI tool disclosure
- `SOURCES_AND_CREDITS.md`: packages, source documents and dataset attribution

## Verification status

The pure Python modules passed **19 unit tests** on 26 October 2026. The full Streamlit UI, model download, public feeds and cloud deployment still need an internet-connected smoke test. See `TEST_REPORT.md`.

## Run tests

```bash
python -m pip install pytest
python -m pytest -q
python -m compileall -q app.py core.py sources.py evaluate_matching.py
python evaluate_matching.py
```

## Student team

Smreti AMIN, Paul de FELICE, Anabel GAMBIHLER GUERREIRO, François LAURE, Inès NOAGBEWONOU.

This proof-of-concept was created for an academic AI application assignment. Students must review and approve the deliverable and disclose the assistance used.
## Calendar, status indicators and exports

The **Calendar / Calendrier** page is connected to the session application tracker. Any edited deadline, submission date or status is reflected in its month view. Click a date to inspect the related opportunity. The dashboard chips are also clickable: **red** for deadlines in the next seven days or overdue; **green** for applications in progress (Applied or Interview); **blue** for Saved opportunities to apply to. Calendar day cells use the same colors and can be selected to display individual events.

For personal calendars, click a tracked deadline and choose **Add to Google Calendar** to prefill a new all-day event. Use **Download calendar event (.ics)** for a single deadline or **Export all tracked dates (.ics)** for all recorded deadlines and application dates, compatible with Google Calendar, Outlook and Apple Calendar. Exporting an ICS file or opening a Google Calendar event composer is **not automatic syncing**: if you change a deadline later, repeat the export or update the event yourself. No personal calendar account is accessed or modified directly by CareerCollective.

The fictional student applications and calendar events are marked as DEMO. Dates not published by employers cannot be inferred, and the calendar does not imply real applications were submitted.
