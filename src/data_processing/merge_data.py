
import pandas as pd
import os

def main(data_dir_arg):
    data_dir = data_dir_arg
    
    wttj_path = os.path.join(data_dir, "offres_wttj_raw.csv")
    apec_path = os.path.join(data_dir, "offres_apec_raw.csv")
    output_path = os.path.join(data_dir, "offres_raw_merged.csv")

    dfs_to_merge = []

    # Check and load WTTJ data
    if os.path.exists(wttj_path):
        print(f"Chargement de {wttj_path}")
        df_wttj = pd.read_csv(wttj_path)
        if "source" not in df_wttj.columns:
            df_wttj["source"] = "WTTJ"
        dfs_to_merge.append(df_wttj)
    else:
        print(f"ATTENTION: Le fichier WTTJ raw n'a pas été trouvé: {wttj_path}. Ignoré pour la fusion.")
        df_wttj = pd.DataFrame() # Initialize as empty DataFrame
        
    # Check and load APEC data
    if os.path.exists(apec_path):
        print(f"Chargement de {apec_path}")
        df_apec = pd.read_csv(apec_path)
        if "source" not in df_apec.columns:
            df_apec["source"] = "APEC"
        dfs_to_merge.append(df_apec)
    else:
        print(f"ATTENTION: Le fichier APEC raw n'a pas été trouvé: {apec_path}. Ignoré pour la fusion.")
        df_apec = pd.DataFrame() # Initialize as empty DataFrame

    # Check and load France Travail data (assuming it's similar)
    francetravail_path = os.path.join(data_dir, "offres_francetravail_raw.csv")
    if os.path.exists(francetravail_path):
        print(f"Chargement de {francetravail_path}")
        df_francetravail = pd.read_csv(francetravail_path)
        if "source" not in df_francetravail.columns:
            df_francetravail["source"] = "France Travail"
        dfs_to_merge.append(df_francetravail)
    else:
        print(f"ATTENTION: Le fichier France Travail raw n'a pas été trouvé: {francetravail_path}. Ignoré pour la fusion.")
        df_francetravail = pd.DataFrame() # Initialize as empty DataFrame

    if not dfs_to_merge:
        print("Aucun fichier raw trouvé ou chargé. Impossible de fusionner.")
        return

    # Concatenate
    df_merged = pd.concat(dfs_to_merge, ignore_index=True)
    
    # Save
    df_merged.to_csv(output_path, index=False, encoding="utf-8-sig")
    
    print(f"Fusion terminée : {len(df_merged)} offres au total.")
    print(f" - WTTJ : {len(df_wttj)}")
    print(f" - APEC : {len(df_apec)}")
    print(f" - France Travail : {len(df_francetravail)}")
    print(f"Sauvegardé dans : {output_path}")

if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    data_dir = os.path.join(project_root, "data")
    main(data_dir)
