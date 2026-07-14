"""Modélise la couche gold en schéma en étoile dans data/warehouse.db,
en plus du dataset plat `offres_enriched.csv` / table `gold_offres`.

Grain de fact_offres : une ligne par offre. Les attributs à forte
cardinalité ou réutilisés ailleurs (entreprise, localisation, date,
source, compétence) sont dimensionnés. Les attributs catégoriels simples
(job_type, job_category, expérience, niveau d'étude) restent en
dimensions dégénérées sur le fait — les dimensionner séparément
ajouterait des tables sans réel bénéfice sur un projet de cette taille.
"""
import re

import pandas as pd

from src.config import SKILL_PATTERNS
from src.warehouse import load_table


def _build_dimension(df, column, id_name):
    values = sorted(df[column].dropna().unique())
    return pd.DataFrame({id_name: range(1, len(values) + 1), column: values})


def _parse_salaire(salaire):
    """Extrait un min/max numérique annuel d'un salaire texte libre.

    Les 3 sources ont des formats différents : APEC utilise un raccourci
    "k€" (ex. "55 - 70 k€ brut annuel"), France Travail précise "Mensuel"
    ou "Annuel" en euros complets, Adzuna donne des euros complets sans
    indication de période. On ne multiplie par 1000 que si "k" apparaît
    explicitement dans le texte — sinon un salaire d'alternance comme
    "984-1858" (déjà en euros) serait faussé en "984 000-1 858 000".
    """
    if pd.isna(salaire):
        return None, None
    text = str(salaire).lower()
    text = re.sub(r"\s+sur\s+\d+.*$", "", text)  # retire "sur 12 mois" (durée, pas un montant)
    numbers = [float(n) for n in re.findall(r"\d+(?:[.,]\d+)?", text.replace(",", "."))]
    if not numbers:
        return None, None
    if "k" in text:
        numbers = [n * 1000 for n in numbers]
    if "mensuel" in text:
        numbers = [n * 12 for n in numbers]
    numbers = [int(n) for n in numbers]
    return min(numbers), max(numbers)


def build_star_schema(df_enriched):
    df = df_enriched.reset_index(drop=True).copy()
    df["offre_id"] = df.index + 1

    dim_entreprise = _build_dimension(df, "entreprise", "entreprise_id")
    dim_source = _build_dimension(df, "source", "source_id")

    dim_localisation = df[["localisation", "region", "country", "is_remote_job"]].drop_duplicates().reset_index(drop=True)
    dim_localisation.insert(0, "localisation_id", dim_localisation.index + 1)

    dim_date = df[["date_poste"]].dropna().drop_duplicates().reset_index(drop=True)
    dim_date.insert(0, "date_id", dim_date.index + 1)
    parsed_dates = pd.to_datetime(dim_date["date_poste"], errors="coerce")
    dim_date["annee"] = parsed_dates.dt.year
    dim_date["mois"] = parsed_dates.dt.month
    dim_date["trimestre"] = parsed_dates.dt.quarter

    skill_cols = [c for c in SKILL_PATTERNS if c in df.columns]
    dim_competence = pd.DataFrame({"competence_id": range(1, len(skill_cols) + 1), "competence": skill_cols})

    df["salaire_min"], df["salaire_max"] = zip(*df["salaire"].apply(_parse_salaire))

    fact = df.merge(dim_entreprise, on="entreprise", how="left")
    fact = fact.merge(dim_localisation, on=["localisation", "region", "country", "is_remote_job"], how="left")
    fact = fact.merge(dim_source, on="source", how="left")
    fact = fact.merge(dim_date, on="date_poste", how="left")

    fact_offres = fact[[
        "offre_id", "titre", "job_type", "job_category", "experience_estimee",
        "niveau_etude_estime", "salaire_min", "salaire_max",
        "entreprise_id", "localisation_id", "source_id", "date_id", "lien",
    ]]

    fact_offre_competence = df[["offre_id"] + skill_cols].melt(
        id_vars="offre_id", value_vars=skill_cols, var_name="competence", value_name="present"
    )
    fact_offre_competence = fact_offre_competence[fact_offre_competence["present"] == 1]
    fact_offre_competence = fact_offre_competence.merge(dim_competence, on="competence")[["offre_id", "competence_id"]]

    load_table(dim_entreprise, "dim_entreprise")
    load_table(dim_localisation, "dim_localisation")
    load_table(dim_source, "dim_source")
    load_table(dim_date[["date_id", "date_poste", "annee", "mois", "trimestre"]], "dim_date")
    load_table(dim_competence, "dim_competence")
    load_table(fact_offres, "fact_offres")
    load_table(fact_offre_competence, "fact_offre_competence")
