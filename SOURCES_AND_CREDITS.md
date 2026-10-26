# Sources, package citations, model and dataset credits

## Public API documentation

1. Greenhouse, *Job Board API*, https://docs.greenhouse.io/job-board.html — public employer-specific GET endpoints, request syntax and availability.
2. Lever, *Public Postings API*, official code examples/documentation at https://github.com/lever/postings-api — public job listings, global and EU API hosts, field structure.
3. Streamlit, *Session state*, https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state — app state is tied to the connection and may be lost on refresh.
4. Streamlit, *Deploy your app*, https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app — deployment procedure and dependencies.

## AI and Python dependencies

- **Sentence Transformers**, https://www.sbert.net/ — multilingual text embeddings with cosine similarity.
- **Model:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, Hugging Face model page https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 — model downloaded at first runtime use; model licence and upstream terms apply.
- **scikit-learn**, https://scikit-learn.org/ — `TfidfVectorizer` and `cosine_similarity`.
- **pandas**, https://pandas.pydata.org/ — CSV and tabular transformations.
- **Streamlit**, https://streamlit.io/ — web interface.
- **requests**, https://requests.readthedocs.io/ — HTTP requests.
- **Beautiful Soup**, https://www.crummy.com/software/BeautifulSoup/bs4/doc/ — HTML text extraction.
- **pypdf**, https://pypdf.readthedocs.io/ — PDF text extraction.
- **python-docx**, https://python-docx.readthedocs.io/ — DOCX parsing.
- **openpyxl**, https://openpyxl.readthedocs.io/ — Excel workbook creation.

## Data provenance

- `data/sample_jobs.csv` — 16 **synthetic/fictional** postings created for this educational demo, with fictional employer names and hypothetical deadline dates. NOT scraped from real job sources.
- `data/sample_discussions.csv` — 6 **fictional** discussions and usernames for illustrative community content.
- `data/example_cv.txt`, `data/example_tracker.csv` — **fictional** example inputs for repeatable demonstrations and tests.
- Any listings loaded through the UI from Greenhouse or Lever at runtime are **live employer-published listings as of the most recent successful fetch**. CareerCollective does not own those descriptions and only displays them for the user's exploration; follow original links for authoritative details.

## Responsible AI statement

CareerCollective does not determine eligibility, predict recruiter decisions, process protected characteristics in a scoring model, rank people for employers, or automate job applications. Recommendation scores should be treated as suggestions. The bilingual matching pipeline may reproduce bias from pretrained text and cannot ensure fair outcomes across languages or experience levels.