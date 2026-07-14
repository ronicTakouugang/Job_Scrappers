"""Couche BRONZE — extraction brute des offres via l'API officielle Adzuna.

Écrit `offres_adzuna_raw.csv` sans transformation métier : le nettoyage
se fait en couche silver. Nécessite ADZUNA_APP_ID/ADZUNA_APP_KEY dans le
fichier `.env` à la racine du projet (voir `.env.example`) — inscription
gratuite et instantanée sur https://developer.adzuna.com/.
"""
import os
import time
from datetime import datetime

import pandas as pd
import requests
from dotenv import load_dotenv

from src.config import PROJECT_ROOT

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

COUNTRY = "fr"
BASE_URL = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search"
RESULTS_PER_PAGE = 50
MAX_PAGES_PER_KEYWORD = 20  # 20 * 50 = 1000 offres max par mot clé

SEARCH_KEYWORDS = [
    "Data Scientist", "Data Analyst", "Data Engineer",
    "Machine Learning", "Business Intelligence", "Big Data",
    "Intelligence Artificielle",
]

TIMEOUT = 15


def parse_offre(o, keyword):
    return {
        "titre": o.get("title"),
        "entreprise": (o.get("company") or {}).get("display_name"),
        "contrat": o.get("contract_type"),
        "localisation": (o.get("location") or {}).get("display_name"),
        "salaire": _format_salaire(o),
        "description": o.get("description"),
        "lien": o.get("redirect_url"),
        "date_publication": (o.get("created") or "")[:10],
        "date_scraping": datetime.now().strftime("%Y-%m-%d"),
        "source": "Adzuna",
        "mot_cle_recherche": keyword,
        "id_adzuna": o.get("id"),
    }


def _format_salaire(o):
    salary_min = o.get("salary_min")
    salary_max = o.get("salary_max")
    if not salary_min and not salary_max:
        return None
    if salary_min and salary_max and salary_min != salary_max:
        return f"{int(salary_min)}-{int(salary_max)}"
    return str(int(salary_min or salary_max))


def get_page(keyword, page):
    url = f"{BASE_URL}/{page}"
    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": RESULTS_PER_PAGE,
        "what": keyword,
        "content-type": "application/json",
    }
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json().get("results", [])
        print(f"  Erreur API {r.status_code}: {r.text[:200]}")
        return []
    except Exception as e:
        print(f"  Exception req: {e}")
        return []


def run_adzuna_scraper(bronze_dir):
    if not APP_ID or not APP_KEY:
        print("ADZUNA_APP_ID ou ADZUNA_APP_KEY manquant dans le fichier .env — scraper Adzuna ignoré.")
        return

    all_offers = []
    seen_ids = set()

    for kw in SEARCH_KEYWORDS:
        print(f"--- Recherche: {kw} ---")

        for page in range(1, MAX_PAGES_PER_KEYWORD + 1):
            results = get_page(kw, page)

            if not results:
                print("  Fin des résultats.")
                break

            new_in_page = 0
            for off in results:
                off_id = off.get("id")
                if off_id and off_id not in seen_ids:
                    seen_ids.add(off_id)
                    all_offers.append(parse_offre(off, kw))
                    new_in_page += 1

            print(f"  Page {page}: +{new_in_page} nouvelles offres (Total unique: {len(all_offers)})")
            time.sleep(0.5)  # Respect du taux d'appel de l'API gratuite

    print(f"Total offres récupérées : {len(all_offers)}")

    if all_offers:
        os.makedirs(bronze_dir, exist_ok=True)
        output = os.path.join(bronze_dir, "offres_adzuna_raw.csv")
        pd.DataFrame(all_offers).to_csv(output, index=False, encoding="utf-8-sig")
        print(f"Sauvegarde dans {output}")
    else:
        print("Aucune offre trouvée.")


if __name__ == "__main__":
    from src.config import BRONZE_DIR
    run_adzuna_scraper(BRONZE_DIR)
