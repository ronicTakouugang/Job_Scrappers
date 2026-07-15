"""Couche SILVER (étape 2/2) — nettoyage et standardisation des offres fusionnées.

Déduplique, standardise les types de contrat, détermine la région à
partir de la localisation, et estime la séniorité à partir du titre.
Lit `offres_raw_merged.csv`, écrit `offres_clean.csv`.
"""
import re

import pandas as pd

from src.config import ADZUNA_CONTRACT_MAP, APEC_CONTRACT_CODES, IDF_POSTAL_PREFIXES, REGION_KEYWORDS

FINAL_COLUMNS = [
    "titre", "entreprise", "job_type", "localisation", "is_remote_job",
    "region", "country", "salaire", "description", "lien", "date_scraping",
    "date_publication", "mot_cle_recherche", "source",
]


def sanitize_text(text):
    """Nettoyage de texte pur (aucune règle métier) : HTML, espaces, séparateur CSV."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    text = text.replace(";", ",")  # évite les conflits avec le séparateur CSV
    return re.sub(r"\s+", " ", text).strip()


def standardise_contrat(raw_value):
    if pd.isna(raw_value):
        return "Non précisé"
    value = str(raw_value).lower().strip()

    for code, label in APEC_CONTRACT_CODES.items():
        if code in value:
            return label

    if value in ADZUNA_CONTRACT_MAP:
        return ADZUNA_CONTRACT_MAP[value]

    if any(k in value for k in ("alternance", "alternant", "alter", "appr")):
        return "Alternance"
    if "stage" in value or "intern" in value:
        return "Stage"
    if "cdi" in value or "durée indéterminée" in value:
        return "CDI"
    if "cdd" in value or "durée déterminée" in value:
        return "CDD"
    if "freelance" in value or "indep" in value:
        return "Freelance"
    if "vie" in value:
        return "VIE"
    return "Non précisé"


def determine_region(loc_for_region):
    """Retourne la région française déduite de la localisation, ou None si aucune ne correspond."""
    if any(k in loc_for_region for k in REGION_KEYWORDS["Île-de-France"]):
        return "Île-de-France"
    if re.search(IDF_POSTAL_PREFIXES, loc_for_region):
        return "Île-de-France"

    for region, keywords in REGION_KEYWORDS.items():
        if region == "Île-de-France":
            continue
        if any(k in loc_for_region for k in keywords):
            return region

    return None


def clean_and_categorize_location(row):
    loc = str(row["localisation"]).lower().strip()
    is_remote_flag = row["is_remote"]

    if is_remote_flag or "télétravail" in loc or "remote" in loc:
        is_remote_flag = True
        loc = re.sub(r"(télétravail|remote|à distance)", "", loc).strip()
        if not loc or loc == "france":
            loc = "Flexible"

    final_city = loc.title() if loc and loc != "france" else ""
    if final_city == "Flexible" and not is_remote_flag:
        final_city = ""

    country = row["country"] if row["country"] else "France"

    region = determine_region(final_city.lower())
    if region is None:
        if "france" in final_city.lower() or (not final_city and not is_remote_flag):
            region = "France Entière (Non précisé)"
        elif is_remote_flag:
            region = "Télétravail"
        else:
            region = "Autre"

    return pd.Series(
        [final_city, is_remote_flag, region, country],
        index=["localisation_clean", "is_remote_job", "region", "country"],
    )


def clean_offers(input_path, output_path):
    print(f"Début du nettoyage des données depuis: {input_path}")
    df = pd.read_csv(input_path)
    print(f"avant nettoyage: {len(df)} lignes")

    # 1. Supprimer les vrais doublons
    df = df.drop_duplicates(subset=["titre", "entreprise"])
    print(f"apres deduplication: {len(df)} lignes")

    # 2. Nettoyer les valeurs manquantes et initialiser de nouvelles colonnes
    df["entreprise"] = df["entreprise"].fillna("Confidentiel")
    df["localisation"] = df["localisation"].fillna("")
    df["contrat"] = df["contrat"].fillna("Non précisé")
    df["titre"] = df["titre"].fillna("N/A")

    if "is_remote" not in df.columns:
        df["is_remote"] = False
    df["is_remote"] = df["is_remote"].fillna(False).astype(bool)

    if "country" not in df.columns:
        df["country"] = "France"
    df["country"] = df["country"].fillna("France")

    # 3. Standardiser les types de contrat
    df["contrat"] = df["contrat"].apply(standardise_contrat)
    df.rename(columns={"contrat": "job_type"}, inplace=True)

    # 4. Traitement de la localisation et détermination de la région
    df[["localisation_clean", "is_remote_job", "region", "country"]] = df.apply(
        clean_and_categorize_location, axis=1
    )
    df.rename(columns={"localisation_clean": "localisation"}, inplace=True)

    # 5. Nettoyage de texte (HTML, espaces) — hygiène pure, pas de règle métier
    df["titre"] = df["titre"].apply(sanitize_text)
    df["entreprise"] = df["entreprise"].apply(sanitize_text)
    df["description"] = df["description"].apply(sanitize_text)

    # Résumé final
    print(f"\naprès nettoyage: {len(df)} lignes")
    print(f"\ndistribution job_type:\n{df['job_type'].value_counts()}")
    print(f"\ndistribution régions:\n{df['region'].value_counts()}")
    print(f"\ndistribution is_remote_job:\n{df['is_remote_job'].value_counts()}")

    for col in FINAL_COLUMNS:
        if col not in df.columns:
            df[col] = None

    df = df[FINAL_COLUMNS]
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\nsauvegarde: {output_path}")


if __name__ == "__main__":
    import os
    from src.config import SILVER_DIR

    clean_offers(
        os.path.join(SILVER_DIR, "offres_raw_merged.csv"),
        os.path.join(SILVER_DIR, "offres_clean.csv"),
    )
