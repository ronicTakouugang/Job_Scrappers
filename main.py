import os
from src.scrapers.scraper_apec import get_apec_offers
from src.scrapers.scraper_francetravail import main as francetravail_main
from src.scrapers.scraper_wttj import main as wttj_main
from src.data_processing.merge_data import main as merge_data_main
from src.data_processing.clean_data import clean_data
from src.data_processing.enrich_data import main as enrich_data_main

# Définition centralisée du PROJECT_ROOT et DATA_DIR
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

def run_scrapers(data_dir_arg):
    print("--- Lancement des scrapers ---")
    get_apec_offers(data_dir_arg)
    francetravail_main(data_dir_arg)
    wttj_main(data_dir_arg)
    print("--- Scraping terminé ---")

def run_data_processing(data_dir_arg):
    print("--- Lancement du traitement des données ---")
    
    # 1. Fusion des données brutes
    print("\n--- Fusion des données brutes ---")
    merge_data_main(data_dir_arg)

    # 2. Nettoyage des données
    print("\n--- Nettoyage des données ---")
    input_clean_path = os.path.join(data_dir_arg, "offres_raw_merged.csv")
    output_clean_path = os.path.join(data_dir_arg, "offres_clean.csv")
    clean_data(input_clean_path, output_clean_path)

    # 3. Enrichissement des données
    print("\n--- Enrichissement des données ---")
    enrich_data_main(data_dir_arg)
    
    print("--- Traitement des données terminé ---")

def main():
    print("--- Démarrage du processus complet ---")
    # Créer le dossier data s'il n'existe pas
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # run_scrapers(DATA_DIR) # Commented out as requested
    run_data_processing(DATA_DIR)
    print("--- Processus complet terminé ---")

if __name__ == "__main__":
    main()
