import pandas as pd
import os
import re

def clean_data(input_path, output_path):
    print(f"Début du nettoyage des données depuis: {input_path}")
    df = pd.read_csv(input_path)
    print(f"avant nettoyage: {len(df)} lignes")


    # 1. Supprimer les vrais doublons
    df = df.drop_duplicates(subset=['titre', 'entreprise'])
    print(f"apres deduplication: {len(df)} lignes")


    # 2. Nettoyer les valeurs manquantes et initialiser de nouvelles colonnes
    df['entreprise'] = df['entreprise'].fillna('Confidentiel')
    df['localisation'] = df['localisation'].fillna('') # Initialiser à vide pour traitement
    df['contrat'] = df['contrat'].fillna('Non précisé')
    df['titre'] = df['titre'].fillna('N/A')
    
    # Nouvelles colonnes du scraper WTTJ
    # Initialiser 'is_remote' column if not present and then process
    if 'is_remote' not in df.columns:
        df['is_remote'] = False
    df['is_remote'] = df['is_remote'].fillna(False).astype(bool)

    # Initialize 'country' column if not present and then process
    if 'country' not in df.columns:
        df['country'] = 'France'
    df['country'] = df['country'].fillna('France') # fillna for any NaN values from existing column


    # 3. Standardiser les types de contrat
    def standardise_contrat(c):
        if pd.isna(c):
            return 'Non précisé'
        c = str(c).lower().strip()
        
        # Mapping APEC codes
        if '101888' in c: return 'CDI'
        if '101887' in c: return 'CDD'
        if '597137' in c: return 'Intérim/Mission'
        if '597141' in c: return 'Alternance' # Possible code
        
        if 'alternance' in c or 'alternant' in c or 'alter' in c or 'appr' in c:
            return 'Alternance'
        if 'stage' in c or 'intern' in c:
            return 'Stage'
        if 'cdi' in c or 'durée indéterminée' in c:
            return 'CDI'
        if 'cdd' in c or 'durée déterminée' in c:
            return 'CDD'
        if 'freelance' in c or 'indep' in c:
            return 'Freelance'
        if 'vie' in c:
            return 'VIE'
        return 'Non précisé'

    df['contrat'] = df['contrat'].apply(standardise_contrat)
    df.rename(columns={'contrat': 'job_type'}, inplace=True)


    # 4. Traitement de la localisation et détermination de la région
    def clean_and_categorize_location(row):
        loc = str(row['localisation']).lower().strip()
        is_remote_flag = row['is_remote'] # Utilise le flag is_remote de WTTJ

        # Déterminer si le job est remote via texte ou flag
        if is_remote_flag or 'télétravail' in loc or 'remote' in loc:
            is_remote_flag = True
            # Nettoyer la localisation pour ne garder que la ville si présente, sinon vide
            loc = re.sub(r'(télétravail|remote|à distance)', '', loc).strip()
            # Si après nettoyage il ne reste rien ou juste "france", on peut laisser vide ou marquer "Flexible"
            if not loc or loc == 'france':
                loc = 'Flexible' # Ou vide, selon préférence pour la ville réelle
            
        final_city = loc.title() if loc and loc != 'france' else ''
        if final_city == "Flexible" and not is_remote_flag: # Correction si "Flexible" sans remote flag
            final_city = ""


        region = 'Autre'
        country = row['country'] if row['country'] else 'France' # Garder le pays si défini, sinon France

        # Détermination de la région basée sur la localisation nettoyée
        loc_for_region = final_city.lower()
        
        idf_keys = [
            'paris', 'boulogne', 'levallois', 'puteaux', 'massy', 'vélizy', 'saclay', 
            'versailles', 'saint-cloud', 'neuilly', 'issy', 'montrouge', 'courbevoie', 
            'nanterre', 'défense', 'suresnes', 'rueil', 'clichy', 'ivry', 'pantin',
            'saint-denis', 'bagneux', 'fontenay', 'vincennes', 'creteil', 'cergy'
        ]
        if any(k in loc_for_region for k in idf_keys): region = 'Île-de-France'
        elif re.search(r'\b(75|92|93|94|91|95|77|78)\d{0,3}\b', loc_for_region): region = 'Île-de-France'
        elif 'lyon' in loc_for_region or 'villeurbanne' in loc_for_region or '69' in loc_for_region: region = 'Auvergne-Rhône-Alpes'
        elif 'marseille' in loc_for_region or 'aix' in loc_for_region or 'sophia' in loc_for_region or 'nice' in loc_for_region or '06' in loc_for_region or '13' in loc_for_region: region = 'PACA'
        elif 'bordeaux' in loc_for_region or 'merignac' in loc_for_region or 'pessac' in loc_for_region or '33' in loc_for_region: region = 'Nouvelle-Aquitaine'
        elif 'toulouse' in loc_for_region or 'blagnac' in loc_for_region or '31' in loc_for_region: region = 'Occitanie'
        elif 'nantes' in loc_for_region or '44' in loc_for_region: region = 'Pays de la Loire'
        elif 'rennes' in loc_for_region or '35' in loc_for_region: region = 'Bretagne'
        elif 'lille' in loc_for_region or 'villeneuve' in loc_for_region or '59' in loc_for_region: region = 'Hauts-de-France'
        elif 'strasbourg' in loc_for_region or '67' in loc_for_region: region = 'Grand Est'
        elif 'montpellier' in loc_for_region or '34' in loc_for_region: region = 'Occitanie'
        elif 'grenoble' in loc_for_region or '38' in loc_for_region: region = 'Auvergne-Rhône-Alpes'
        elif 'france' in loc_for_region or not final_city and not is_remote_flag: region = 'France Entière (Non précisé)' # Si pas de ville et pas remote
        elif is_remote_flag: region = 'Télétravail' # Si remote et pas de ville spécifique
            
        return pd.Series([final_city, is_remote_flag, region, country], index=['localisation_clean', 'is_remote_job', 'region', 'country'])

    df[['localisation_clean', 'is_remote_job', 'region', 'country']] = df.apply(clean_and_categorize_location, axis=1)
    df.rename(columns={'localisation_clean': 'localisation'}, inplace=True) # Remplacer l'ancienne colonne

    # 5. Ajouter une colonne séniorité
    def get_seniorite(titre):
        if pd.isna(titre):
            return 'Non précisé'
        titre = str(titre).lower()
        if 'senior' in titre or 'lead' in titre or 'principal' in titre:
            return 'Senior'
        if 'junior' in titre or 'débutant' in titre:
            return 'Junior'
        if 'manager' in titre or 'head' in titre or 'directeur' in titre:
            return 'Manager'
        if 'alternance' in titre or 'alternant' in titre or 'stage' in titre:
            return 'Junior'
        return 'Confirmé'

    df['seniorite'] = df['titre'].apply(get_seniorite)


    # 6. Nettoyage des titres (supprimer balises HTML résiduelles)
    df['titre'] = df['titre'].str.replace(r'<.*?>', '', regex=True).str.strip()


    # Résumé final
    print(f"\naprès nettoyage: {len(df)} lignes")
    print(f"\ndistribution job_type:\n{df['job_type'].value_counts()}")
    print(f"\ndistribution régions:\n{df['region'].value_counts()}")
    print(f"\ndistribution séniorité:\n{df['seniorite'].value_counts()}")
    print(f"\ndistribution is_remote_job:\n{df['is_remote_job'].value_counts()}")


    # Sélection des colonnes finales pour la sauvegarde
    final_cols = ['titre', 'entreprise', 'job_type', 'localisation', 'is_remote_job', 'region', 'country', 'salaire', 'description', 'lien', 'date_scraping', 'date_publication', 'seniorite', 'mot_cle_recherche', 'source']
    
    # Assurer que toutes les colonnes requises existent, sinon les ajouter vides
    for col in final_cols:
        if col not in df.columns:
            df[col] = None # Ou une valeur par défaut appropriée

    df = df[final_cols]
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\nsauvegarde: {output_path}")

if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    data_dir = os.path.join(project_root, "data")
    input_path = os.path.join(data_dir, "offres_raw_merged.csv")
    output_path = os.path.join(data_dir, "offres_clean.csv")
    clean_data(input_path, output_path)