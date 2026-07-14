"""Point d'entrée de l'ETL — orchestre les couches bronze -> silver -> gold.

Usage:
    python main.py --stage silver   # fusion + nettoyage
    python main.py --stage gold     # enrichissement
    python main.py --stage all      # bronze (si --with-bronze) + silver + gold

Chaque couche est aussi chargée dans data/warehouse.db (SQLite), sous les
tables bronze_offres / silver_offres / gold_offres, requêtables en SQL.
La couche gold est en plus modélisée en schéma en étoile (fact_offres +
dimensions), voir src/gold/star_schema.py.
"""
import argparse
import os

import pandas as pd

from src.bronze.scraper_adzuna import run_adzuna_scraper
from src.bronze.scraper_apec import run_apec_scraper
from src.bronze.scraper_francetravail import run_francetravail_scraper
from src.config import BRONZE_DIR, GOLD_DIR, SILVER_DIR
from src.gold.enrich import enrich_offers
from src.gold.star_schema import build_star_schema
from src.silver.clean import clean_offers
from src.silver.merge import merge_bronze_sources
from src.warehouse import load_table


def run_bronze():
    print("--- BRONZE : lancement des scrapers ---")
    run_apec_scraper(BRONZE_DIR)
    run_francetravail_scraper(BRONZE_DIR)
    run_adzuna_scraper(BRONZE_DIR)
    print("--- BRONZE : terminé ---")


def run_silver():
    print("--- SILVER : fusion des sources brutes ---")
    merge_bronze_sources(BRONZE_DIR, SILVER_DIR)
    merged_path = os.path.join(SILVER_DIR, "offres_raw_merged.csv")
    load_table(pd.read_csv(merged_path), "bronze_offres")

    print("\n--- SILVER : nettoyage et standardisation ---")
    clean_path = os.path.join(SILVER_DIR, "offres_clean.csv")
    clean_offers(merged_path, clean_path)
    load_table(pd.read_csv(clean_path), "silver_offres")
    print("--- SILVER : terminé ---")


def run_gold():
    print("--- GOLD : enrichissement métier ---")
    enrich_offers(SILVER_DIR, GOLD_DIR)
    enriched_path = os.path.join(GOLD_DIR, "offres_enriched.csv")
    df_enriched = pd.read_csv(enriched_path)
    load_table(df_enriched, "gold_offres")

    print("--- GOLD : construction du schéma en étoile (fait + dimensions) ---")
    build_star_schema(df_enriched)
    print("--- GOLD : terminé ---")


def main():
    parser = argparse.ArgumentParser(description="ETL Job Market Data Science (architecture médaillon).")
    parser.add_argument(
        "--stage", choices=["bronze", "silver", "gold", "all"], default="all",
        help="Étape du pipeline à exécuter (défaut: all).",
    )
    parser.add_argument(
        "--with-bronze", action="store_true",
        help="Avec --stage all, relance aussi le scraping (lent, soumis à l'anti-bot). Ignoré sinon.",
    )
    args = parser.parse_args()

    for directory in (BRONZE_DIR, SILVER_DIR, GOLD_DIR):
        os.makedirs(directory, exist_ok=True)

    if args.stage == "bronze":
        run_bronze()
    elif args.stage == "silver":
        run_silver()
    elif args.stage == "gold":
        run_gold()
    elif args.stage == "all":
        if args.with_bronze:
            run_bronze()
        else:
            print("--- BRONZE ignoré (passer --with-bronze pour relancer le scraping) ---")
        run_silver()
        run_gold()


if __name__ == "__main__":
    main()
