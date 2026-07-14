"""Couche SILVER (étape 1/2) — fusion des offres brutes des 3 sources.

Concatène les CSV bronze en un seul fichier, sans encore nettoyer les
valeurs. Le nettoyage proprement dit est fait par `silver/clean.py`.
"""
import os

import pandas as pd


def merge_bronze_sources(bronze_dir, silver_dir):
    os.makedirs(silver_dir, exist_ok=True)
    output_path = os.path.join(silver_dir, "offres_raw_merged.csv")

    sources = [
        (os.path.join(bronze_dir, "offres_apec_raw.csv"), "APEC"),
        (os.path.join(bronze_dir, "offres_francetravail_raw.csv"), "France Travail"),
        (os.path.join(bronze_dir, "offres_adzuna_raw.csv"), "Adzuna"),
    ]

    dfs_to_merge = []
    counts = {}

    for path, source_name in sources:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            df = pd.read_csv(path)
            if df.empty:
                counts[source_name] = 0
                continue
            print(f"Chargement de {path}")
            if "source" not in df.columns:
                df["source"] = source_name
            dfs_to_merge.append(df)
            counts[source_name] = len(df)
        else:
            print(f"ATTENTION: Fichier bronze introuvable ou vide, ignoré pour la fusion: {path}")
            counts[source_name] = 0

    if not dfs_to_merge:
        print("Aucun fichier bronze trouvé ou chargé. Impossible de fusionner.")
        return

    df_merged = pd.concat(dfs_to_merge, ignore_index=True)
    df_merged.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"Fusion terminée : {len(df_merged)} offres au total.")
    for source_name, count in counts.items():
        print(f" - {source_name} : {count}")
    print(f"Sauvegardé dans : {output_path}")


if __name__ == "__main__":
    from src.config import BRONZE_DIR, SILVER_DIR
    merge_bronze_sources(BRONZE_DIR, SILVER_DIR)
