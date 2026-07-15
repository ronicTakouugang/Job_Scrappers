"""Tests de fumée pour les couches silver et gold.

Ne dépendent d'aucune donnée scrapée : tout est construit en mémoire pour
que la suite tourne en quelques secondes, sans réseau.
"""
import pandas as pd
import pytest

from src.gold.enrich import categorize_job_role, extract_skills, recover_missing_fields
from src.silver.clean import determine_region, standardise_contrat


@pytest.mark.parametrize("raw_value,expected", [
    ("CDI", "CDI"),
    ("cdd", "CDD"),
    ("Alternance / Apprentissage", "Alternance"),
    ("Stage de fin d'études", "Stage"),
    ("101888", "CDI"),  # code APEC
    ("permanent", "CDI"),  # Adzuna
    ("contract", "CDD"),  # Adzuna
    (None, "Non précisé"),
])
def test_standardise_contrat(raw_value, expected):
    assert standardise_contrat(raw_value) == expected


@pytest.mark.parametrize("localisation,expected_region", [
    ("paris", "Île-de-France"),
    ("75001", "Île-de-France"),
    ("lyon", "Auvergne-Rhône-Alpes"),
    ("marseille", "PACA"),
    ("ville inconnue", None),
])
def test_determine_region(localisation, expected_region):
    assert determine_region(localisation) == expected_region


def test_extract_skills_detects_only_present_skills():
    description = "Nous cherchons un profil maîtrisant Python et SQL, idéalement avec Power BI."
    skills = extract_skills(description)

    assert skills["Python"] == 1
    assert skills["SQL"] == 1
    assert skills["Power BI"] == 1
    assert skills["Java"] == 0
    assert skills["Spark"] == 0


def test_extract_skills_handles_non_string_input():
    skills = extract_skills(None)
    assert all(value == 0 or value is False for value in skills.values())


@pytest.mark.parametrize("description,expected_skill,expected_value", [
    # Faux positifs corrigés : substring dans un autre mot
    ("Transformation digitale de l'entreprise", "Git", 0),
    ("Architecture scalable sur le cloud", "Scala", 0),
    ("Maintenir une data platform robuste", "TensorFlow", 0),
    ("Réaliser des tableaux de bord mensuels", "Tableau", 0),
    # Vrais positifs : la compétence doit toujours être détectée
    ("Maîtrise de Git et GitHub requise", "Git", 1),
    ("Développement Scala sur Spark", "Scala", 1),
    ("Modèles de deep learning avec TensorFlow", "TensorFlow", 1),
    ("Reporting sous Power BI, Tableau ou Looker", "Tableau", 1),
    ("Le langage R et RStudio sont utilisés au quotidien", "R", 1),
])
def test_extract_skills_avoids_substring_false_positives(description, expected_skill, expected_value):
    assert extract_skills(description)[expected_skill] == expected_value


@pytest.mark.parametrize("titre,expected", [
    ("Ingénieur Data H/F", "Data Engineer"),
    ("Architecte Data H/F", "Data Engineer"),
    ("Data Architect - F/H", "Data Engineer"),
    ("Analytics Engineer F/H", "Data Engineer"),
    ("Tech Lead Data H/F", "Data Engineer"),
    ("Ingénieur IA F/H", "Data Scientist"),
    ("AI Engineer F/H", "Data Scientist"),
])
def test_categorize_job_role_recognises_common_title_variants(titre, expected):
    assert categorize_job_role(titre, "", "CDI") == expected


def test_recover_missing_fields_sets_remote_flag_from_description():
    row = pd.Series({
        "description": "Poste ouvert au télétravail partiel, 2 jours par semaine.",
        "localisation": "Paris",
        "job_type": "CDI",
        "is_remote_job": False,
    })
    result = recover_missing_fields(row)
    assert result["is_remote_job"] is True
