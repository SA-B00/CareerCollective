# AI tool usage and prompt disclosure

## Tool disclosure

- **OpenAI ChatGPT (GPT-6)** was used to co-design the product concept, write and refine Python app code, draft bilingual interface text, devise tests, and prepare documentation.
- **Hugging Face / Sentence Transformers** supplies the pretrained multilingual sentence embedding model used **at runtime**, when enabled.
- **scikit-learn** supplies an auditable TF-IDF fallback and cosine similarity.
- Other tools such as Bard, Copilot, Kaggle, or Dataiku were **not** claimed as used.
- All code and copy require review by the student team; no fabricated live data or evaluation statistics should be reported.

## Prompt log  -  exact user prompts from this conversation

1. **Project brief (excerpt)**: "Overall goal: Create your own AI application with existing tools." The user supplied the complete project requirements including a five-minute demo, reproducible code, data, a user guide, and a prompt log.
2. **Initial product direction (excerpt)**: "The aim of our group is to create, what do you call, an app that helps people find internships and maybe apprenticeships, and maybe a tracker that can track the Excel sheets and the type of internships you're looking for, the tracks that are opening and closing dates of the offers, and maybe even a link to a group chat with other candidates."
3. **Confirmed scope (exact)**: "Here are my final decisions for building StagePilot AI:\n1. Who should StagePilot AI serve? All students, across industries (recommended)\n2. Where should it search for opportunities? France, with French and English support (recommended)\n3. How should the application find job opportunities? Live job sources + sample jobs + manual entry (recommended)\n4. Should multiple students have separate accounts? No login for version 1; demonstration mode (recommended)\n5. How would you like the app published? Choose whichever is easiest\nDeadline: 2026-10-06\nAdditional preferences: The interface for the community and lets come up with a rather different name, give me multiple suggestions before you start\nPlease build the functioning application with reproducible code and prepare it for deployment."
4. **Deadline update (exact)**: "27 october"
5. **Naming preference (exact)**: "no more names less appy but clear intention"
6. **Final selected name (exact)**: "CareerCollective"

## Design directives formulated with AI assistance

The following are **summary prompts**, not verbatim user messages. They record the implementation choices made to fulfill the user requests:

- "Implement a Python Streamlit bilingual internship/apprenticeship dashboard across industries, starting with France, using documented public employer-specific APIs, fictional seed data and manual input."
- "Support TXT/PDF/DOCX CV extraction, multilingual semantic sentence embeddings plus a transparent fallback, explainable fit reasons, and honest qualification of recommendation scores."
- "Include a session-only community demonstration with threads, questions, and replies. Explicitly avoid pretending there is shared persistent messaging."
- "Add editable application status tracking with CSV/XLSX import/export, ISO deadlines only when explicitly known, backup and restore, privacy limitations and reproducible local/cloud setup."
- "Create a five-minute demo script, beginner's guide, attribution, and deterministic unit tests mocking third-party job APIs."

## Recommended team entries before submission

Include any additional actual prompts sent to AI services by group members, what each response was used for, and the team member responsible for verification and integration. Do not report imaginary tests or tools.


## Upgrade prompts and work (26 October 2026)

- User instruction: "Okay can we go with a white and blue interface upload actual listings and the ability to search for them and also remove emojis, its unprofessional"
- Work performed with ChatGPT: rebuild UI styling in white/navy/blue, remove decorative emojis, design a searchable bilingual vacancy browser, identify public employer boards, implement concurrent Greenhouse/Lever feed import with error disclosure and caching, add a separate CSV of previously observed real employer URLs, document source verification limits, and create mock API tests.
- AI generated draft Python changes were reviewed with Python compilation, pandas CSV parsing and a pytest regression suite before uploading. Full browser runtime / external provider uptime cannot be verified offline.

### Demonstration dataset and user interface enhancement (26 October 2026)
**Prompt (summary, user supplied):** "Create a fictional CV already uploaded, populate saved and sent applications, community involvement and deadlines. Remove all long dashes from text."
**AI assistance:** Drafted a fictional candidate CV and PDF, created reproducible CSV and JSON fixtures, seeded session-only tracker and community actions, added prominent fictional-demo labeling, updated Python app code and tests. No external applications or posts were actually made.