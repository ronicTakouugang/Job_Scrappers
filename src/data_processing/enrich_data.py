import pandas as pd
import re
import os

# --- Configuration des Mots-clés ---

KEYWORDS = {
    # Langages de programmation
    "Python": [r"python"],
    "SQL": [r"sql"],
    "R": [r"\bR\b", r"RStudio"],
    "Java": [r"\bjava\b"],
    "Scala": [r"scala"],
    "C++": [r"c\+\+"],
    "SAS": [r"\bsas\b"],
    "Matlab": [r"matlab"],
    "VBA": [r"\bvba\b"],

    # Data Engineering & Big Data
    "Spark": [r"spark", r"pyspark"],
    "Hadoop": [r"hadoop", "hdfs"],
    "Kafka": [r"kafka"],
    "Hive": [r"hive"],
    "Airflow": [r"airflow"],
    "dbt": [r"dbt"],
    "Snowflake": [r"snowflake"],
    "Databricks": [r"databricks"],
    "BigQuery": [r"bigquery", "big query"],
    "Redshift": [r"redshift"],
    
    # Data Science Libs
    "Pandas": [r"pandas"],
    "NumPy": [r"numpy"],
    "Scikit-learn": [r"scikit-learn", r"sklearn"],
    "TensorFlow": [r"tensorflow", r"tf"],
    "PyTorch": [r"pytorch"],
    "Keras": [r"keras"],
    "NLP": [r"nlp", "natural language processing", "traitement automatique du langage"],
    "Computer Vision": [r"computer vision", "vision par ordinateur", "opencv"],

    # Visualization
    "Power BI": [r"power bi", r"powerbi", r"dax"], # Re-added
    "Tableau": [r"tableau"],
    "Looker": [r"looker"],
    "Qlik": [r"qlik", r"qliksense", r"qlikview"],
    "Streamlit": [r"streamlit"],

    # Cloud & DevOps
    "AWS": [r"aws", "amazon web services"],
    "Azure": [r"azure"],
    "GCP": [r"gcp", "google cloud"],
    "Docker": [r"docker"],
    "Kubernetes": [r"kubernetes", r"k8s"],
    "Git": [r"git", "github", "gitlab"],
    "Linux": [r"linux"],
    "CI/CD": [r"ci/cd", "cicd", "jenkins", "gitlab ci"],

    # Soft Skills & Langues
    "Anglais": [r"anglais", "english"],
    "Agile": [r"agile", "scrum", "kanban"],
    "Communication": [r"communication"],
    "Rigueur": [r"rigueur", "rigoureux"],
    "Curiosité": [r"curiosité", "curieux"],
    "Travail d'équipe": [r"travail d'équipe", "team player", "esprit d'équipe"],
    "Gestion de projet": [r"gestion de projet", "chef de projet"]
}

EDUCATION_LEVELS = {
    "Bac+5": [r"bac\+5", r"master", r"ingénieur", r"msc", r"grande école"],
    "Bac+3/4": [r"bac\+3", r"bac\+4", r"licence", r"bachelor"],
    "PhD": [r"phd", r"doctorat", r"docteur"]
}

def extract_skills(text, keywords_dict):
    found_skills = {}
    if not isinstance(text, str):
        for k in keywords_dict:
            found_skills[k] = False
        return found_skills
    
    text_lower = text.lower()
    
    for skill, patterns in keywords_dict.items():
        found = False
        for pat in patterns:
            if re.search(pat, text_lower):
                found = True
                break
        found_skills[skill] = int(found)
        
    return found_skills

def extract_experience(text):
    if not isinstance(text, str):
        return "Non précisé"
    
    text_lower = text.lower()
    
    # Recherche de motifs "X années", "X ans"
    # Junior: < 2 ans, débutant
    # Confirmé: 2-5 ans
    # Senior: > 5 ans
    
    # Motifs explicites
    if re.search(r"débutant|junior|première expérience", text_lower):
        return "Junior"
    
    match_years = re.search(r"(\d+)\s*(?:ans|années|an|year)", text_lower)
    if match_years:
        try:
            years = int(match_years.group(1))
            if years < 2:
                return "Junior"
            elif years <= 5:
                return "Confirmé"
            else:
                return "Senior"
        except:
            pass
            
    if re.search(r"senior|expert|lead", text_lower):
        return "Senior"
        
    if re.search(r"confirmé|expérimenté", text_lower):
        return "Confirmé"
        
    return "Non précisé"

def extract_education(text):
    if not isinstance(text, str):
        return "Non précisé"
    
    text_lower = text.lower()
    for level, patterns in EDUCATION_LEVELS.items():
        for pat in patterns:
            if re.search(pat, text_lower):
                return level
    return "Non précisé"

def categorize_job_role(title, description, job_type):
    title_lower = str(title).lower()
    description_lower = str(description).lower()
    job_type_lower = str(job_type).lower()

    if "alternance" in job_type_lower or "alternant" in title_lower or "apprentissage" in title_lower:
        return "Alternance"
    if "stage" in job_type_lower or "stagiaire" in title_lower:
        return "Stage"
        
    # Data Scientist
    if re.search(r"data scientist|scientifique de données|science des données", title_lower) or \
       re.search(r"machine learning|apprentissage automatique|ia|intelligence artificielle|deep learning", description_lower) and \
       re.search(r"modélisation|statistique|algorithme|prédict", description_lower):
        return "Data Scientist"
    
    # Data Engineer
    if re.search(r"data engineer|ingénieur données|ingénieur big data|devops data", title_lower) or \
       re.search(r"etl|pipeline de données|entrepôt de données|data warehouse|flux de données|spark|hadoop|kafka|airflow", description_lower):
        return "Data Engineer"
        
    # Data Analyst
    if re.search(r"data analyst|analyste données|business intelligence|bi analyst", title_lower) or \
       re.search(r"analyse de données|reporting|dashboard|visualisation|excel|sql", description_lower):
        return "Data Analyst"
        
    # Autres rôles Data (si pas déjà classés)
    if re.search(r"data|données|bi", title_lower) or \
       re.search(r"data|données|bi", description_lower):
        return "Autre rôle Data"

    return "Non spécifié"

def main(data_dir_arg):
    data_dir = data_dir_arg
    
    # 1. Charger les fichier bruts (selon ce qui existe)
    dfs = []
    
    # Après le nettoyage, le fichier 'offres_clean.csv' sera le principal.
    # Pour l'enrichissement, on ne devrait charger que le fichier clean.
    files = ["offres_clean.csv"] # On ne charge plus les raw files ici
    
    for f in files:
        path = os.path.join(data_dir, f)

        if os.path.exists(path):
            print(f"Chargement de {f}...")
            # Try/except pour utf-8 vs cp1252 si besoin, mais pandas gère souvent bien
            try:
                df_tmp = pd.read_csv(path)
            except UnicodeDecodeError:
                df_tmp = pd.read_csv(path, encoding='cp1252')
            
            # Standardisation immédiate des colonnes clés
            df_tmp.columns = [c.lower().strip() for c in df_tmp.columns] # tout en minuscule et strip
            
            # Remove duplicate columns if any (prevents concat crash)
            if df_tmp.columns.duplicated().any():
                print(f"  -> Parsing: Removing duplicate columns in {f}: {df_tmp.columns[df_tmp.columns.duplicated()].tolist()}")
                df_tmp = df_tmp.loc[:, ~df_tmp.columns.duplicated()]
            
            print(f"  -> Colonnes trouvées (normalisées): {list(df_tmp.columns)}")

            # Renommage spécifique si besoin (ex: 'post_description' -> 'description')
            # Le fichier clean.csv devrait déjà avoir les bonnes colonnes
            rename_map = {}
            for col in df_tmp.columns:
                if 'desc' in col and 'description' not in rename_map.values():
                    rename_map[col] = 'description'
                if 'titre' in col or 'title' in col:
                     rename_map[col] = 'titre'
                if 'company' in col or 'entreprise' in col:
                     rename_map[col] = 'entreprise'
                if 'link' in col or 'lien' in col or 'url' in col:
                     rename_map[col] = 'lien'
                if 'contract' in col or 'job_type' in col:
                     rename_map[col] = 'job_type'
                if 'location' in col or 'localisation' in col:
                     rename_map[col] = 'localisation'
                if 'is_remote' in col: # New from WTTJ raw, clean_data renames to is_remote_job
                    rename_map[col] = 'is_remote_job'
                if 'country' in col:
                    rename_map[col] = 'country'
                if 'date_scraping' in col: # Explicitly map date_scraping
                     rename_map[col] = 'date_scraping'
                if 'date_publication' in col: # Explicitly map date_publication
                     rename_map[col] = 'date_publication'

            print(f"  -> Mapping: {rename_map}")
            df_tmp.rename(columns=rename_map, inplace=True)
            
            # Re-dedup columns after rename (rename can create duplicates!)
            if df_tmp.columns.duplicated().any():
                print(f"  -> Parsing: Removing duplicate columns after rename: {df_tmp.columns[df_tmp.columns.duplicated()].tolist()}")
                df_tmp = df_tmp.loc[:, ~df_tmp.columns.duplicated()]
            
            # --- RECUPERATION DES DONNEES MANQUANTES ---
            # Cette partie devrait être principalement gérée par clean_data.py
            # On la garde au cas où mais elle devrait avoir moins d'impact
            def recover_data(row):
                desc = str(row.get('description', '')).lower()
                
                # Recuperation Job Type
                if pd.isna(row.get('job_type')) or str(row.get('job_type')).strip() == '':
                    if 'cdi' in desc: row['job_type'] = 'CDI'
                    elif 'cdd' in desc: row['job_type'] = 'CDD'
                    elif 'stage' in desc: row['job_type'] = 'Stage'
                    elif 'alternance' in desc or 'contrat pro' in desc or 'apprentissage' in desc: row['job_type'] = 'Alternance'
                    elif 'freelance' in desc or 'indépendant' in desc: row['job_type'] = 'Freelance'
                    elif 'intérim' in desc: row['job_type'] = 'Intérim'
                
                # Recuperation Localisation
                if pd.isna(row.get('localisation')) or str(row.get('localisation')).strip() == '':
                    # Liste des grandes villes et hubs tech
                    cities = ['paris', 'lyon', 'bordeaux', 'lille', 'nantes', 'toulouse', 'marseille', 'rennes', 'strasbourg', 'montpellier', 'nice', 'sophia antipolis', 'la défense', 'boulogne', 'courbevoie', 'levallois', 'issy', 'télétravail', 'remote', 'france']
                    for city in cities:
                        if city in desc:
                            row['localisation'] = city.title()
                            break # On prend la première trouvée
                            
                return row

            print("  -> Tentative de récupération des données manquantes (Job Type/Loc)...")
            df_tmp = df_tmp.apply(recover_data, axis=1)

            # Debug stats colonnes
            if 'job_type' in df_tmp.columns:
                print(f"  -> Job Type non-null (apres recovery): {df_tmp['job_type'].notna().sum()} / {len(df_tmp)}")
            if 'localisation' in df_tmp.columns:
                print(f"  -> Localisation non-null (apres recovery): {df_tmp['localisation'].notna().sum()} / {len(df_tmp)}")
            
            # Ajouter colonne source si absente
            if 'source' not in df_tmp.columns:
                if 'apec' in f:
                    df_tmp['source'] = 'APEC'
                elif 'wttj' in f:
                    df_tmp['source'] = 'WTTJ'
                elif 'francetravail' in f:
                    df_tmp['source'] = 'France Travail'
            
            print(f"  -> {len(df_tmp)} offres chargées. Colonnes: {list(df_tmp.columns)}")
            dfs.append(df_tmp)
    
    if not dfs:
        print("Aucun fichier de données trouvé dans data/")
        return

    df_full = pd.concat(dfs, ignore_index=True)
    print(f"Total offres brutes concaténées : {len(df_full)}")
    
    # Deduplicate columns globally (failsafe)
    if df_full.columns.duplicated().any():
        print(f"CRITICAL: Found duplicate columns in combined DF: {df_full.columns[df_full.columns.duplicated()].tolist()}")
        df_full = df_full.loc[:, ~df_full.columns.duplicated()]
        print("CRITICAL: Removed duplicate columns.")

    # Deduplication rows (Priorité au premier chargé -> Enhanced)
    if 'lien' in df_full.columns:
        before = len(df_full)
        df_full.drop_duplicates(subset=['lien'], keep='first', inplace=True)
        print(f"Deduplication (sur lien) : {before} -> {len(df_full)} (-{before - len(df_full)})")
    
    # 2. Nettoyage de base
    def sanitize_text(text):
        if not isinstance(text, str):
            return ""
        # Nettoyage HTML residuel
        text = re.sub(r'<[^>]+>', ' ', text)
        # Remplacer sauts de ligne et tabulations par des espaces
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        # Remplacer les points virgules (conflit CSV parfois) par des virgules
        text = text.replace(';', ',')
        # Enlever les espaces multiples
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    # S'assurer que 'description' existe
    if 'description' not in df_full.columns:
        print("ATTENTION: Colonne 'description' introuvable après standardisation. Création vide.")
        df_full['description'] = ""
    
    # Remplir description vide et nettoyer
    df_full['description'] = df_full['description'].fillna("").astype(str).apply(sanitize_text)
    df_full['titre'] = df_full['titre'].fillna("").astype(str).apply(sanitize_text)
    df_full['entreprise'] = df_full['entreprise'].fillna("").astype(str).apply(sanitize_text)
    
    # Check stats descriptions
    nb_desc = df_full[df_full['description'].str.len() > 20].shape[0]
    print(f"Nombre d'offres avec description > 20 chars : {nb_desc} / {len(df_full)}")
    
    # 3. Enrichissement
    print("Enrichissement en cours (Extraction des compétences)...")
    
    # Reset index pour alignement parfait
    df_full = df_full.reset_index(drop=True)
    
    # Appliquer extraction skills
    skills_data = df_full['description'].apply(lambda x: extract_skills(x, KEYWORDS))
    df_skills = pd.DataFrame(skills_data.tolist())
    
    # Fusionner via assignation directe (plus robuste que concat axis=1)
    df_enriched = df_full.copy()
    for col in df_skills.columns:
        df_enriched[col] = df_skills[col]
        
    print(f"Fusion compétences terminée. Shape: {df_enriched.shape}")
    
    # Extraire Expérience & Formation
    df_enriched['experience_estimee'] = df_enriched['description'].apply(extract_experience)
    df_enriched['niveau_etude_estime'] = df_enriched['description'].apply(extract_education)

    # Catégorisation des postes
    print("Catégorisation des rôles de poste...")
    df_enriched['job_category'] = df_enriched.apply(
        lambda row: categorize_job_role(row['titre'], row['description'], row['job_type']), 
        axis=1
    )

    # Consolidation de la date de publication
    print("Consolidation de la date de publication...")
    df_enriched['date_poste'] = df_enriched['date_publication'].fillna(df_enriched['date_scraping'])
    df_enriched['date_poste'] = pd.to_datetime(df_enriched['date_poste'], errors='coerce').dt.strftime('%Y-%m-%d')
    
    # 4. Sauvegarde Format Large (Tout en un)
    # On garde les colonnes principales + skills
    cols_base = ['titre', 'entreprise', 'job_type', 'localisation', 'is_remote_job', 'country', 'date_poste', 'date_scraping', 'date_publication', 'source', 'lien', 'experience_estimee', 'niveau_etude_estime', 'job_category', 'description']
    
    # Ajouter toutes les colonnes skills
    cols_final = []
    for c in df_enriched.columns:
        if c in cols_base or c in KEYWORDS.keys():
            cols_final.append(c)
    
    # Assurer que toutes les colonnes de base sont là (même vides)
    for c in cols_base:
        if c not in df_enriched.columns:
             df_enriched[c] = None

    # Garder aussi région si dispo
    if 'region' in df_enriched.columns:
         cols_final.append('region')

    df_final = df_enriched[cols_final]

    output_wide = os.path.join(data_dir, "offres_enriched.csv")
    df_final.to_csv(output_wide, index=False, encoding='utf-8-sig')
    print(f"Fichier enrichi sauvegardé : {output_wide}")
    
    # Re-added the generation of Power BI long format for skills
    print("Génération du format 'Skills Long' pour Power BI...")
    
    # On doit avoir un identifiant unique. Si 'lien' est vide ou dupliqué, on crée un ID
    df_enriched['id_offre'] = df_enriched.index
    
    skills_cols = list(KEYWORDS.keys())
    
    # Vérifier que les skills sont bien dans le df
    present_skills = [c for c in skills_cols if c in df_enriched.columns]
    
    if not present_skills:
        print("Erreur : Aucune colonne compétence trouvée pour le pivot.")
        return

    df_long = pd.melt(df_enriched, 
                      id_vars=['id_offre', 'titre', 'entreprise', 'source'], 
                      value_vars=present_skills, 
                      var_name='Competence', 
                      value_name='Present')
    
    # Garder que les lignes où Present = 1
    df_long = df_long[df_long['Present'] == 1].drop(columns=['Present'])
    
    output_long = os.path.join(data_dir, "skills_powerbi.csv")
    df_long.to_csv(output_long, index=False, encoding='utf-8-sig')
    print(f"Fichier Skills Long sauvegardé : {output_long} ({len(df_long)} lignes)")

if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    data_dir = os.path.join(project_root, "data")
    main(data_dir)
