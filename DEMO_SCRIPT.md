# CareerCollective — 5-minute video plan

**Target runtime: 5:00; do not exceed the assignment's ±10% tolerance.** Screen capture the working Streamlit interface and narrate over it. Test AI model download **before** recording so that the demo focuses on functionality.

## 0:00–0:35 — Problem (35 seconds)
"Finding an internship should not require 20 tabs, scattered spreadsheets and missed deadlines. Even when students find openings, keyword searches often overlook transferable skills. And navigating applications can feel isolating."

## 0:35–1:05 — Product promise (30 seconds)
"Meet CareerCollective: one bilingual platform to discover opportunities, track applications and learn from other students. We're building it for students across sectors, beginning with France."

## 1:05–2:35 — Demonstrate actual AI (90 seconds)
1. Open **My profile**, show a sample profile or upload the **fictional** `data/example_cv.txt` and click Save.
2. Open **Discover**. Choose **Multilingual pretrained transformer (AI)**, if running successfully, and show the named engine below filters.
3. Show two different opportunities and reveal **Why this match?**, including shared skills and skills to develop.
4. Explain that a pretrained multilingual transformer compares career goals to job descriptions semantically, while a transparent bilingual skill checklist improves explainability.
5. Briefly switch to the **Fast baseline**, compare ordering and explain why semantic matching goes beyond keyword search. Do **not** claim statistically proved superiority without test evidence.

## 2:35–3:45 — Tracker + freshness (70 seconds)
1. Save a demo role and navigate to **My applications**.
2. Update its status to **Applied**, add a note, show a published deadline, and download an Excel tracker.
3. Mention that existing Excel trackers can be imported.
4. Show **Import current vacancies**: Greenhouse and Lever are supported **for an identified employer board**, not a universal search index. If network is reliable, import a tested board in advance; otherwise clearly show the import UI and explain limitations, rather than pretending a feed is live.

## 3:45–4:25 — Community and technical stack (40 seconds)
1. Show sample threads and create a short session-only question.
2. Explain: Streamlit/Python UI; Hugging Face multilingual embeddings; scikit-learn baseline; Pandas/openpyxl Excel pipeline; selected public company APIs.
3. State clearly: group communication is **demo-only**, because persistent cross-user messaging requires authentication and a backend.

## 4:25–5:00 — Impact and ethics (35 seconds)
"At scale, CareerCollective could help students discover roles beyond their original search terms, organize every application and support one another. Our prototype is reproducible: code, sample data, user guide, and prompts are included. We label fictional listings, never invent closing dates, and treat match scores as suggestions — not hiring probabilities. CareerCollective: find your next opportunity, together."

## Practical video production

- Record at 1920×1080, zoom browser to 90–100%, cursor visible.
- Split speaking time: one narrator for opening, one for AI, one for tracker, one for community, one for close/tech; rehearse transitions.
- Keep visible app use predominant; only 1–2 title slides if desired.
- On the closing slide show each group member's name and an attribution screen.
- Use demo data only. Avoid personal CVs and personal chat links in recordings.

## Optional evaluation test

Ask 3–5 volunteer students to rank 6–8 example roles for a fictional profile, then compare the selected match engine's top-3 precision to the baseline against their judgments. Record your actual test results and disclose the small sample size. Do not invent statistics.


## Updated live-listings demonstration (26 October 2026)

For the final video, begin in **Discover > Employer listings** (not Demonstration data). Show the text-only white-and-blue navigation. Search `marketing` and then select `Paris`, or show `data` to compare sources and matching scores. Explain that public Greenhouse/Lever employer feeds are queried at runtime and that `PREVIOUSLY OBSERVED — VERIFY` links are real previously observed employer job pages, not a claim of active availability. Open an official employer listing, save it to **My applications**, change its status, and export the Excel tracker. Switch to **Demonstration data** only if you wish to show the clearly fictional sample scenario. Show semantic AI matching using the sidebar selector when time permits; the fast TF-IDF mode is the fallback.