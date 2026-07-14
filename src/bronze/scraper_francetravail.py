"""Couche BRONZE — extraction brute des offres France Travail via leur API OAuth2.

Écrit `offres_francetravail_raw.csv` sans transformation métier : le
nettoyage se fait en couche silver. Nécessite CLIENT_ID/CLIENT_SECRET
dans le fichier `.env` à la racine du projet (voir `.env.example`).
"""
import os
import time
from datetime import datetime

import pandas as pd
import requests
from dotenv import load_dotenv

from src.config import PROJECT_ROOT

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire"
API_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
SCOPE = "api_offresdemploiv2 o2dsoffre"

SEARCH_KEYWORDS = [
    "Data Scientist", "Data Analyst", "Data Engineer",
    "Machine Learning", "Business Intelligence", "Big Data",
    "Intelligence Artificielle",
]
PAGE_SIZE = 100
MAX_OFFERS_PER_KEYWORD = 600  # On vise ~2000 total

TIMEOUT = 15


def get_token():
    print("Authentification France Travail...")
    data = {"grant_type": "client_credentials", "scope": SCOPE}
    try:
        r = requests.post(
            TOKEN_URL,
            data=data,
            auth=(CLIENT_ID, CLIENT_SECRET),
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r.json()["access_token"]
    except requests.exceptions.HTTPError as e:
        print(f"Erreur Auth: {e}")
        print(r.text)
        raise


def get_offres(token, keyword, start, end):
    headers = {"Authorization": f"Bearer {token}"}
    params = {"motsCles": keyword, "range": f"{start}-{end}"}
    try:
        r = requests.get(API_URL, headers=headers, params=params, timeout=TIMEOUT)
        if r.status_code in (200, 206):
            return r.json().get("resultats", [])
        if r.status_code == 204:
            return []
        print(f"  Erreur API {r.status_code}: {r.text[:200]}")
        return []
    except Exception as e:
        print(f"  Exception req: {e}")
        return []


def parse_offre(o):
    return {
        "titre": o.get("intitule"),
        "entreprise": o.get("entreprise", {}).get("nom"),
        "contrat": o.get("typeContrat"),
        "localisation": o.get("lieuTravail", {}).get("libelle"),
        "salaire": o.get("salaire", {}).get("libelle"),
        "description": o.get("description"),
        "lien": o.get("origineOffre", {}).get("urlOrigine"),
        "date_publication": o.get("dateCreation", "")[:10],
        "date_scraping": datetime.now().strftime("%Y-%m-%d"),
        "source": "France Travail",
    }


def run_francetravail_scraper(bronze_dir):
    if not CLIENT_ID or not CLIENT_SECRET:
        print("CLIENT_ID ou CLIENT_SECRET manquant dans le fichier .env — scraper France Travail ignoré.")
        return

    try:
        token = get_token()
    except Exception:
        return

    all_offers = []
    seen_ids = set()

    for kw in SEARCH_KEYWORDS:
        print(f"--- Recherche: {kw} ---")

        for start in range(0, MAX_OFFERS_PER_KEYWORD, PAGE_SIZE):
            end = start + PAGE_SIZE - 1
            print(f"  Page {start}-{end}...")

            results = get_offres(token, kw, start, end)

            if not results:
                print("  Fin des résultats.")
                break

            new_in_page = 0
            for off in results:
                off_id = off.get("id")
                if off_id and off_id not in seen_ids:
                    seen_ids.add(off_id)
                    all_offers.append(parse_offre(off))
                    new_in_page += 1

            print(f"  + {new_in_page} nouvelles offres.")

            if len(results) < PAGE_SIZE:
                break

            time.sleep(1)  # Poil de politesse

    print(f"Total offres récupérées : {len(all_offers)}")

    if all_offers:
        os.makedirs(bronze_dir, exist_ok=True)
        output = os.path.join(bronze_dir, "offres_francetravail_raw.csv")
        pd.DataFrame(all_offers).to_csv(output, index=False, encoding="utf-8-sig")
        print(f"Sauvegarde dans {output}")
    else:
        print("Aucune offre trouvée.")


if __name__ == "__main__":
    from src.config import BRONZE_DIR
    run_francetravail_scraper(BRONZE_DIR)
