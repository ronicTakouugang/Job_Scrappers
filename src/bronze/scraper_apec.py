"""Couche BRONZE — extraction brute des offres APEC via leur API JSON publique.

Écrit `offres_apec_raw.csv` sans transformation métier : le nettoyage se
fait en couche silver.
"""
import os
import random
import re
import time
from datetime import datetime

import pandas as pd
import requests

SEARCH_KEYWORDS = [
    "Data Scientist",
    "Data Analyst",
    "Data Engineer",
    "Machine Learning Engineer",
    "Intelligence Artificielle",
    "Business Intelligence",
    "Data Steward",
]
NUM_PAGES_PER_KEYWORD = 80  # 80 * 20 = 1600 offres potentielles par mot clé
SEARCH_URL = "https://www.apec.fr/cms/webservices/rechercheOffre"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.apec.fr",
}


def clean_html(raw_html):
    if not isinstance(raw_html, str):
        return ""
    cleantext = re.sub(re.compile('<.*?>'), ' ', raw_html)
    return re.sub(r'\s+', ' ', cleantext).strip()


def run_apec_scraper(bronze_dir):
    os.makedirs(bronze_dir, exist_ok=True)
    output_final = os.path.join(bronze_dir, "offres_apec_raw.csv")

    all_offers = []
    seen_ids = set()

    print(f"--- Démarrage du Scraping API APEC (Cible: {len(SEARCH_KEYWORDS) * NUM_PAGES_PER_KEYWORD * 20} offres max) ---")

    for kw in SEARCH_KEYWORDS:
        print(f"\nRecherche: {kw}")
        empty_pages_consecutive = 0

        for page in range(NUM_PAGES_PER_KEYWORD):
            if empty_pages_consecutive > 2:
                print("  -> Fin des résultats pour ce mot clé.")
                break

            try:
                payload = {
                    "motsCles": kw,
                    "pagination": {"range": 20, "startIndex": page * 20},
                    "activeFiltre": False,
                }

                time.sleep(random.uniform(0.5, 1.5))  # Délai respectueux

                r = requests.post(SEARCH_URL, headers=HEADERS, json=payload, timeout=15)

                if r.status_code == 200:
                    data = r.json()
                    if "resultats" in data and len(data["resultats"]) > 0:
                        empty_pages_consecutive = 0
                        new_count = 0

                        for off in data["resultats"]:
                            if off['numeroOffre'] not in seen_ids:
                                seen_ids.add(off['numeroOffre'])
                                new_count += 1

                                part1 = off.get("texteOffre") or ""
                                part2 = off.get("descriptifPoste") or ""
                                part3 = off.get("profilRecherche") or ""
                                description_clean = clean_html(f"{part1} {part2} {part3}")

                                all_offers.append({
                                    "titre": off.get("intituleSurbrillance") or off.get("intitule"),
                                    "entreprise": off.get("nomCommercial"),
                                    "contrat": off.get("typeContratLibelle"),
                                    "localisation": off.get("lieuTravailLibelle"),
                                    "salaire": off.get("salaireTexte"),
                                    "description": description_clean,
                                    "lien": f"https://www.apec.fr/candidat/recherche-emploi.html/emploi/detail-offre/{off['numeroOffre']}",
                                    "date_scraping": datetime.now().strftime("%Y-%m-%d"),
                                    "source": "APEC",
                                    "mot_cle_recherche": kw,
                                    "id_apec": off['numeroOffre'],
                                    # Tronqué à la date (YYYY-MM-DD) pour rester cohérent avec
                                    # France Travail/Adzuna : l'API renvoie un datetime avec fuseau
                                    # horaire ("...T08:24:50.000+0000") qui, mélangé à des dates
                                    # sans fuseau dans le même parsing pandas, fait échouer silencieusement
                                    # le parsing de CES AUTRES dates (elles deviennent NaT).
                                    "date_publication": (off.get("datePublication") or off.get("dateCreation") or "")[:10] or None,
                                })

                        print(f"  Page {page + 1}: +{new_count} nouvelles offres (Total unique: {len(all_offers)})")
                    else:
                        empty_pages_consecutive += 1
                else:
                    print(f"  Erreur API Page {page + 1}: {r.status_code}")
                    break

            except Exception as e:
                print(f"  Exception Page {page + 1}: {e}")
                time.sleep(2)

    print(f"\n--- Sauvegarde de {len(all_offers)} offres dans {output_final} ---")
    df = pd.DataFrame(all_offers)

    cols = ["titre", "entreprise", "contrat", "localisation", "salaire", "description", "lien", "date_scraping", "date_publication", "source", "mot_cle_recherche"]
    for c in cols:
        if c not in df.columns:
            df[c] = ""

    df = df[cols]
    df.to_csv(output_final, index=False, encoding="utf-8-sig")
    print("Terminé.")


if __name__ == "__main__":
    from src.config import BRONZE_DIR
    run_apec_scraper(BRONZE_DIR)
