"""Tests de fumée pour les couches silver et gold.

Ne dépendent d'aucune donnée scrapée : tout est construit en mémoire pour
que la suite tourne en quelques secondes, sans réseau.
"""
import pandas as pd
import pytest

from src.gold.enrich import extract_skills
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
