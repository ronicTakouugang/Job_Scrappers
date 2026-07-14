# Conventions de nommage

## Code

- Fichiers et fonctions Python : `snake_case`
- Une fonction d'entrée par module, nommée explicitement selon son rôle
  (`run_apec_scraper`, `merge_bronze_sources`, `clean_offers`,
  `enrich_offers`) — jamais `main()` générique, pour éviter les alias à
  l'import
- Chaque couche (`bronze/`, `silver/`, `gold/`) est un sous-package de
  `src/`, avec un fichier par source/étape

## Données

- Encodage CSV : toujours `utf-8-sig` (compatibilité Excel avec les
  accents français)
- Dates : `YYYY-MM-DD` (`date_scraping`, `date_publication`, `date_poste`)
- Un fichier brut par source en bronze (`offres_<source>_raw.csv`)
- Noms de colonnes métier en français (`titre`, `entreprise`,
  `localisation`...), cohérent avec la langue des données sources et des
  utilisateurs finaux (marché de l'emploi français)

## Dossiers de données

| Dossier | Contenu |
|---|---|
| `data/bronze/` | Sorties brutes des scrapers, non versionnées (regénérées à chaque run) |
| `data/silver/` | Données fusionnées et nettoyées |
| `data/gold/` | Livrables d'analyse (dataset enrichi, formats BI, heatmap) |
| `data/gold/legacy/` | Anciens exports manuels, référence historique uniquement, non versionné |
