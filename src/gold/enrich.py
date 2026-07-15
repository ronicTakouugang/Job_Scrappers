"""Couche GOLD — enrichissement métier et formats prêts pour l'analyse.

Lit `offres_clean.csv` (couche silver) et produit 2 livrables dans
`data/gold/` :
  - `offres_enriched.csv` : format large, LE dataset final (une colonne
    par compétence détectée) — c'est le livrable principal
  - `offres_skills_long.csv` : même donnée en format long (une ligne par
    couple offre/compétence détectée), pratique pour un `melt` côté
    Tableau/SQL ou une agrégation par compétence
"""
import os
import re

import pandas as pd

from src.config import EDUCATION_LEVELS, MAJOR_CITIES, REMOTE_KEYWORDS, SKILL_PATTERNS

RECOVERY_LOCATION_KEYWORDS = [c.lower() for c in MAJOR_CITIES] + REMOTE_KEYWORDS + ["france"]

BASE_COLUMNS = [
    "titre", "entreprise", "job_type", "localisation", "is_remote_job",
    "country", "salaire", "date_poste", "date_scraping", "date_publication",
    "source", "lien", "experience_estimee", "niveau_etude_estime",
    "job_category", "description", "region",
]


def extract_skills(text, patterns=SKILL_PATTERNS):
    if not isinstance(text, str):
        return {skill: False for skill in patterns}

    text_lower = text.lower()
    found_skills = {}
    for skill, regexes in patterns.items():
        found_skills[skill] = int(any(re.search(pat, text_lower) for pat in regexes))
    return found_skills


def extract_experience(text):
    if not isinstance(text, str):
        return "Non précisé"

    text_lower = text.lower()

    if re.search(r"débutant|junior|première expérience", text_lower):
        return "Junior"

    match_years = re.search(r"(\d+)\s*(?:ans|années|an|year)", text_lower)
    if match_years:
        years = int(match_years.group(1))
        if years < 2:
            return "Junior"
        if years <= 5:
            return "Confirmé"
        return "Senior"

    if re.search(r"senior|expert|lead", text_lower):
        return "Senior"
    if re.search(r"confirmé|expérimenté", text_lower):
        return "Confirmé"

    return "Non précisé"


def extract_education(text, levels=EDUCATION_LEVELS):
    if not isinstance(text, str):
        return "Non précisé"

    text_lower = text.lower()
    for level, patterns in levels.items():
        if any(re.search(pat, text_lower) for pat in patterns):
            return level
    return "Non précisé"


def categorize_job_role(title, description, job_type):
    title_lower = str(title).lower()
    description_lower = str(description).lower()
    job_type_lower = str(job_type).lower()

    if "alternance" in job_type_lower or "alternant" in title_lower or "apprentissage" in title_lower:
        return "Alternance"
    if "stage" in job_type_lower or "stagiaire" in title_lower:
        return "Stage"

    if re.search(r"data scientist|scientifique de données|science des données|ingénieur ia\b|\bai engineer\b", title_lower) or (
        re.search(r"machine learning|apprentissage automatique|ia|intelligence artificielle|deep learning", description_lower)
        and re.search(r"modélisation|statistique|algorithme|prédict", description_lower)
    ):
        return "Data Scientist"

    # "ingénieur data" (sans accent, très courant) en plus de "ingénieur données"
    if re.search(
        r"data engineer|ingénieur données|ingénieur.{0,3}data\b|ingénieur big data|devops data"
        r"|architecte data|data architect|analytics engineer|tech lead data",
        title_lower,
    ) or re.search(
        r"etl|pipeline de données|entrepôt de données|data warehouse|flux de données|spark|hadoop|kafka|airflow", description_lower
    ):
        return "Data Engineer"

    if re.search(r"data analyst|analyste données|business intelligence|bi analyst", title_lower) or re.search(
        r"analyse de données|reporting|dashboard|visualisation|excel|sql", description_lower
    ):
        return "Data Analyst"

    if re.search(r"data|données|bi", title_lower) or re.search(r"data|données|bi", description_lower):
        return "Autre rôle Data"

    return "Non spécifié"


def recover_missing_fields(row):
    """Best-effort : déduit job_type/localisation depuis la description si absents."""
    desc = str(row.get("description", "")).lower()

    if pd.isna(row.get("job_type")) or str(row.get("job_type")).strip() == "":
        if "cdi" in desc:
            row["job_type"] = "CDI"
        elif "cdd" in desc:
            row["job_type"] = "CDD"
        elif "stage" in desc:
            row["job_type"] = "Stage"
        elif "alternance" in desc or "contrat pro" in desc or "apprentissage" in desc:
            row["job_type"] = "Alternance"
        elif "freelance" in desc or "indépendant" in desc:
            row["job_type"] = "Freelance"
        elif "intérim" in desc:
            row["job_type"] = "Intérim"

    if pd.isna(row.get("localisation")) or str(row.get("localisation")).strip() == "":
        for keyword in RECOVERY_LOCATION_KEYWORDS:
            if keyword in desc:
                row["localisation"] = keyword.title()
                break

    # La couche silver ne détecte le télétravail que via le champ
    # localisation structuré ; nos 3 sources n'y mettent quasi jamais un
    # signal remote (c'est mentionné dans la description à la place), donc
    # is_remote_job y était toujours False. On complète ici avec le texte.
    if not row.get("is_remote_job") and any(k in desc for k in REMOTE_KEYWORDS):
        row["is_remote_job"] = True

    return row


def enrich_offers(silver_dir, gold_dir):
    input_path = os.path.join(silver_dir, "offres_clean.csv")
    if not os.path.exists(input_path):
        print(f"Fichier silver introuvable : {input_path}")
        return

    os.makedirs(gold_dir, exist_ok=True)

    print(f"Chargement de {input_path}...")
    df = pd.read_csv(input_path)

    # Le texte (HTML, espaces) est déjà nettoyé par la couche silver ;
    # ici on ne fait que compléter les champs manquants depuis la description.
    print("Récupération des données manquantes...")
    df["description"] = df["description"].fillna("")
    df["titre"] = df["titre"].fillna("")
    df["entreprise"] = df["entreprise"].fillna("")
    df = df.apply(recover_missing_fields, axis=1)

    nb_desc = df[df["description"].str.len() > 20].shape[0]
    print(f"Nombre d'offres avec description > 20 caractères : {nb_desc} / {len(df)}")

    print("Extraction des compétences techniques...")
    skills_df = pd.DataFrame(df["description"].apply(extract_skills).tolist())
    df_enriched = pd.concat([df.reset_index(drop=True), skills_df.reset_index(drop=True)], axis=1)

    print("Extraction expérience, formation et catégorisation du poste...")
    df_enriched["experience_estimee"] = df_enriched["description"].apply(extract_experience)
    df_enriched["niveau_etude_estime"] = df_enriched["description"].apply(extract_education)
    df_enriched["job_category"] = df_enriched.apply(
        lambda row: categorize_job_role(row["titre"], row["description"], row["job_type"]), axis=1
    )

    df_enriched["date_poste"] = df_enriched["date_publication"].fillna(df_enriched["date_scraping"])
    df_enriched["date_poste"] = pd.to_datetime(df_enriched["date_poste"], errors="coerce").dt.strftime("%Y-%m-%d")

    # 1. Format large : livrable principal
    cols_final = [c for c in df_enriched.columns if c in BASE_COLUMNS or c in SKILL_PATTERNS]
    df_final = df_enriched[cols_final]
    output_wide = os.path.join(gold_dir, "offres_enriched.csv")
    df_final.to_csv(output_wide, index=False, encoding="utf-8-sig")
    print(f"Fichier enrichi sauvegardé : {output_wide} ({len(df_final)} lignes)")

    # 2. Format long : une ligne par couple (offre, compétence détectée)
    df_enriched["id_offre"] = df_enriched.index
    skills_present = [c for c in SKILL_PATTERNS if c in df_enriched.columns]
    df_long = pd.melt(
        df_enriched,
        id_vars=["id_offre", "titre", "entreprise", "source"],
        value_vars=skills_present,
        var_name="Competence",
        value_name="Present",
    )
    df_long = df_long[df_long["Present"] == 1].drop(columns=["Present"])
    output_long = os.path.join(gold_dir, "offres_skills_long.csv")
    df_long.to_csv(output_long, index=False, encoding="utf-8-sig")
    print(f"Fichier Skills Long sauvegardé : {output_long} ({len(df_long)} lignes)")


if __name__ == "__main__":
    from src.config import GOLD_DIR, SILVER_DIR
    enrich_offers(SILVER_DIR, GOLD_DIR)
