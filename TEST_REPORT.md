# CareerCollective — Verification report (2026-10-26)

## Checks performed

- `python -m pytest -q` — **11 tests passed**.
- `python -m compileall -q app.py core.py sources.py evaluate_matching.py` — **passed**.
- `python evaluate_matching.py` — **ran** against the 16 fictional sample roles and 3 synthetic profiles.
- PDF guide rendered and visually checked; final document has **2 pages**.

## What tests cover

- Conservative parsing of explicitly published deadlines and date formats.
- Internship/apprenticeship classification and French/English skills vocabulary.
- Scoring logic, a fake/mock semantic encoder, filters, deduplication.
- Import/export round trip for an Excel tracker and French CSV columns.
- Safe URL handling and plain-text CV extraction.
- Mocked Greenhouse and Lever feed parsing.
- Correctly uncertain wording for no-longer-listed positions.

## Toy evaluation (synthetic, NOT actual performance validation)

The reproducible fallback produced top-3 precision scores of 1.00 (events), 0.67 (technology), and 0.33 (finance) against subjectively selected labels in a *fictional* dataset, or a mean of **0.67**. These are not evidence of accuracy on real job boards, applicant success, or fairness. The script `evaluate_matching.py --semantic` can be used on a machine where the pretrained model has been downloaded to compare AI embeddings on exactly the same examples.

## Not tested in this environment

- The full Streamlit browser interface was **not launched**, because Streamlit was not installed and the sandbox could not reach Python package download servers.
- The pretrained Hugging Face model was **not downloaded here**, so the actual transformer inference path still requires a first-run test in the target environment.
- Third-party live API endpoints were **not called from the execution sandbox**; feed extraction was verified with mocked responses only.
- GitHub deployment and the resulting public Streamlit URL have **not** been created; they require connected GitHub/Streamlit account actions.

## Required pre-submission smoke test

1. Install dependencies in a normal internet-connected environment.
2. Run `streamlit run app.py`.
3. Use `data/example_cv.txt` to test the CV/profile feature.
4. Switch AI engine and confirm that the page explicitly says **Multilingual pretrained transformer** rather than fallback.
5. Save a role; edit its tracker row; export/open Excel.
6. Post and reply in Community; confirm these are session-only.
7. Optionally import a real employer-specific Greenhouse/Lever board, after confirming its board identifier and permitted access.
8. Deploy to Streamlit Community Cloud and open the resulting shareable URL in an incognito browser.