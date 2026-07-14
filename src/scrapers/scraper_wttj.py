import re
import time
import pandas as pd
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os

BASE_URL = "https://www.welcometothejungle.com"
KEYWORDS = [
    "Data Scientist",
    "Data Analyst",
    "Data Engineer",
    "Machine Learning Engineer",
    "Intelligence Artificielle"
]
PAGES_PER_KEYWORD = 10  # 5 pages * 30 offres = 150 par mot clé -> Total ~750

# Mots-clés pour détecter le type de contrat dans le titre
CONTRATS = ['alternance', 'stage', 'cdi', 'cdd', 'freelance', 'alternant']

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    )
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver

def parse_aria_label(aria_label):
    texte = aria_label.replace("Consultez l'offre ", "")
    if " | " in texte:
        parts = texte.split(" | ", 1)
        return parts[0].strip(), parts[1].strip()
    return texte.strip(), None

def detect_contrat(titre, contrat_aria):
    if contrat_aria:
        return contrat_aria
    titre_lower = titre.lower()
    for c in CONTRATS:
        if c in titre_lower:
            return c.capitalize()
    return "Non précisé"

def parse_entreprise(href):
    try:
        parties = href.split('/')
        if 'companies' in parties:
            idx = parties.index('companies')
            return parties[idx + 1].replace('-', ' ').title()
        return "N/A"
    except:
        return "N/A"

# NEW FUNCTION: extract_location_details
def extract_location_details(texte_carte):
    cities_list = [
        'Paris', 'Lyon', 'Marseille', 'Bordeaux', 'Toulouse', 'Nantes',
        'Lille', 'Strasbourg', 'Rennes', 'Grenoble', 'Montpellier',
        'Nice', 'Sophia', 'Saclay', 'Puteaux', 'Boulogne', 'Levallois',
        'La Défense', 'Massy', 'Vélizy'
    ]
    
    city = None
    is_remote = False
    country = None # Default to None, can be set to "France" if detected later

    texte_carte_lower = texte_carte.lower()

    # Check for remote/télétravail first
    if 'remote' in texte_carte_lower or 'télétravail' in texte_carte_lower:
        is_remote = True
        
    # Check for specific cities
    for c in cities_list:
        if c.lower() in texte_carte_lower:
            city = c
            break
            
    # If "France" is mentioned and no specific city, set country
    if "france" in texte_carte_lower and city is None:
        country = "France"

    # Fallback if no specific city but remote is true
    if city is None and is_remote:
        city = "Télétravail" # Use "Télétravail" as localisation if remote and no city
    elif city is None and country is None:
        city = "France" # Default to France if nothing more specific
        country = "France"
    elif city is None and country == "France":
        city = "France"

    return city, is_remote, country

def scrape_listing_page(driver, page, keyword):
    """Récupère les infos de base + liens d'une page de recherche."""
    # Encodage manuel simple pour l'URL
    kw_url = keyword.replace(" ", "+")
    url = f"{BASE_URL}/fr/jobs?query={kw_url}&aroundQuery=France&page={page}"
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, 'li[data-testid="search-results-list-item-wrapper"]')
            )
        )
    except:
        print(f"    Page {page}: timeout ou vide")
        return []

    time.sleep(2) # Chargement JS

    cartes = driver.find_elements(By.CSS_SELECTOR, 'li[data-testid="search-results-list-item-wrapper"]')
    print(f"    Page {page}: {len(cartes)} offres trouvées")

    offres_page = []
    for carte in cartes:
        try:
            lien_el = carte.find_element(By.CSS_SELECTOR, 'a[aria-label]')
            aria_label = lien_el.get_attribute('aria-label')
            href = lien_el.get_attribute('href')

            titre, contrat_aria = parse_aria_label(aria_label)
            contrat = detect_contrat(titre, contrat_aria)
            
            # Utiliser la nouvelle fonction pour extraire les détails de localisation
            localisation, is_remote_job, country_job = extract_location_details(carte.text)

            offres_page.append({
                'titre': titre,
                'entreprise': parse_entreprise(href), # Still parse entreprise from href
                'contrat': contrat,
                'localisation': localisation,
                'is_remote': is_remote_job,
                'country': country_job,
                'lien': href,
                'date_scraping': datetime.now().strftime('%Y-%m-%d'),
                'mot_cle_recherche': keyword,
                'source': 'WTTJ'
            })
        except Exception as e:
            print(f"Erreur lors de l'extraction d'une offre: {e}")
            continue
    return offres_page

def scrape_job_details(driver, url):
    """Visite une page d'offre pour récupérer la description et la date de publication."""
    description = ""
    date_publication = None
    try:
        driver.get(url)
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )
        time.sleep(1) 

        main_content = driver.find_element(By.TAG_NAME, "main")
        description = main_content.text

        # Tenter d'extraire la date de publication
        try:
            date_element = driver.find_element(By.TAG_NAME, "time")
            date_publication = date_element.get_attribute("datetime")
            if date_publication:
                # WTTJ dates are often like "YYYY-MM-DDTHH:MM:SS.sssZ", we only need YYYY-MM-DD
                date_publication = date_publication.split("T")[0]
        except Exception as e:
            # print(f"  Pas de balise <time> trouvée pour la date de publication: {e}")
            pass # Pas de date trouvée, ce n'est pas critique
            
    except Exception as e:
        # print(f"Erreur description ou chargement page: {e}") 
        pass
    
    return description, date_publication

def main(data_dir_arg):
    driver = init_driver()
    all_results = []
    seen_links = set()

    print("Démarrage du scraping WTTJ complet...")

    try:
        # 1. Récupération de tous les liens (Phase Listing)
        for kw in KEYWORDS:
            print(f"\n--- Recherche: {kw} ---")
            for page in range(1, PAGES_PER_KEYWORD + 1):
                offres = scrape_listing_page(driver, page, kw)
                if not offres:
                    break
                
                # Ajout seulement si pas déjà vu (dédoublonnage immédiat)
                for off in offres:
                    if off['lien'] not in seen_links:
                        seen_links.add(off['lien'])
                        all_results.append(off)
                
                time.sleep(random.uniform(2, 4))
        
        print(f"\nPhase 1 terminée: {len(all_results)} offres uniques trouvées.")
        
        # Sauvegarde intermédiaire des listings (au cas où)
        os.makedirs(data_dir_arg, exist_ok=True)
        pd.DataFrame(all_results).to_csv(os.path.join(data_dir_arg, "offres_wttj_listings_only.csv"), index=False, encoding='utf-8-sig')
        print("Sauvegarde intermédiaire: offres_wttj_listings_only.csv")

        print("Démarrage de la Phase 2: Récupération des descriptions et dates de publication...")
        
        output_path = os.path.join(data_dir_arg, "offres_wttj_raw.csv")
        # Initialiser le fichier final avec headers
        if not os.path.exists(output_path):
            pd.DataFrame(columns=[
                "titre", "entreprise", "contrat", "localisation", "is_remote", "country", "lien", 
                "date_scraping", "date_publication", "source", "mot_cle_recherche", "description"
            ]).to_csv(output_path, index=False, encoding="utf-8-sig")

        # 2. Récupération des détails (Phase Détail)
        for i, offre in enumerate(all_results):
            if i % 5 == 0:
                print(f"  Traitement offre {i}/{len(all_results)}...")
            
            description, date_publication = scrape_job_details(driver, offre['lien'])
            offre['description'] = description
            offre['date_publication'] = date_publication
            
            # Sauvegarde incrémentale
            df_one = pd.DataFrame([offre])
            df_one.to_csv(output_path, mode='a', header=False, index=False, encoding='utf-8-sig')

            # Délai respectueux (augmenté pour éviter blocage)
            time.sleep(random.uniform(2.0, 5.0))

    finally:
        driver.quit()

    print(f"Scraping terminé. Données sauvegardées dans {output_path}")

if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    data_dir = os.path.join(project_root, "data")
    main(data_dir)
