# CareerCollective — Quick User Guide / Guide utilisateur

## First launch (English)

**1. Set up your profile.** Click **My profile**. Specify your target roles, current skills, preferred industry/city and internship or apprenticeship preference. You may upload a *text-based* PDF, DOCX, or TXT CV. Click **Save profile**. Use the included fictional `data/example_cv.txt` for class demonstrations; no real CV is required.

**2. Find opportunities.** Click **Discover**. The 16 jobs provided at startup are **fictional demo listings**. Filter by free-text search, sector, contract and source. The recommendation score is **not a hiring probability**. Expand **Why this match?** to see skills supporting the match and additional skills to investigate.

**3. Add current opportunities.** Expand **Import current vacancies**, select Greenhouse or Lever, supply an employer's board/site identifier and click **Import public job listings**. There is no universal search; results depend on that specific employer. Alternatively, choose **Add a job manually** and enter an existing role with a verified job URL. All feed-derived posts carry a source tag.

**4. Save and track.** Click **Save opportunity** below an offer. In **My applications**, change its status from Saved to Applied, Interview, Offer, Rejected or Withdrawn. Edit your notes and a known deadline. You can also import existing CSV/XLSX tracker files with company/title columns (or Entreprise/Poste).

**5. Export before closing.** Click **Download Excel tracker** or **Download session backup (JSON)**. This version does not have a database or logins. Data can disappear on browser refresh or disconnection. Restoring the JSON backup recovers most manually entered demo records.

**6. Join the conversation.** Click **Community**. Explore demo threads, create a post or reply in the current session. Nothing is shared across user browsers. If a verified group invitation is supplied by your organizer, add it to **Optional external student-group link**.

**7. Change language.** Use English/Français in the sidebar. Recruitment source descriptions remain in their original language.

## Démarrage rapide (Français)

**1. Mon profil.** Renseignez les postes, compétences, secteurs, ville et type de contrat recherchés. Importez un CV PDF (texte sélectionnable), DOCX ou TXT, puis validez.

**2. Découvrir.** Filtrez les offres par secteur, contrat ou mots-clés. Les 16 offres initiales sont **fictives**. Le score représente une similarité indicative, jamais une probabilité de recrutement.

**3. Annonces actuelles.** Dans « Importer des offres actuelles », saisissez l'identifiant d'une entreprise sur Greenhouse ou Lever. Vous pouvez aussi saisir une offre manuellement avec un lien vérifié.

**4. Mes candidatures.** Enregistrez une offre, puis modifiez statut, dates et notes. Importez ou exportez un tableau Excel / CSV.

**5. Sauvegardez vos données.** Téléchargez le fichier Excel ou une sauvegarde JSON avant de fermer la session. Aucun stockage permanent n'est prévu dans cette version.

**6. Communauté.** Consultez et créez des discussions **dans cette session seulement**. Il ne s'agit pas d'une messagerie réelle multi-utilisateurs.

## What does a match score mean?

- Stage 1: the selected engine computes similarity between your goal/CV text and the job description.
- Stage 2: an auditable English/French skill list produces a small overlap bonus.
- Stage 3: city and contract preferences modify the ranking.
- An **80** means a score of 80 from this heuristic formula **relative to the current inputs**, not an 80% chance of getting an offer.
- Always validate the role, contract, eligibility, deadlines and company source before applying.

## Tracker import format

Recommended columns: `company,title,city,contract,url,deadline,status,applied_on,notes,source`. English or limited French aliases (`Entreprise`, `Poste`, `Ville`, `Contrat`, `Lien`, `Date limite`, `Statut`) are accepted. Dates use ISO `YYYY-MM-DD` or `DD/MM/YYYY`.

## Troubleshooting

- **AI model won't load:** ensure internet access on first run and install `requirements.txt`. The app explicitly switches to the fast TF-IDF baseline otherwise.
- **Nothing from an employer feed:** check the correct company board identifier; that employer may have no current internships or may not use the selected service.
- **Scanned CV appears blank:** enter your details manually; OCR is not part of this demo.
- **Saved records disappeared:** restore the session JSON backup; they were not stored permanently.