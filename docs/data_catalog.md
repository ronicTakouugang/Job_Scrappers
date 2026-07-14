# Data Catalog — couche Gold

**`offres_enriched.csv` est le dataset final** (= table SQL `gold_offres`
dans `data/warehouse.db`) : une ligne par offre, toutes les colonnes
ci-dessous. `offres_skills_long.csv` est un format dérivé, pas un second
dataset (voir plus bas).

## Colonnes de base

| Colonne | Type | Description |
|---|---|---|
| `titre` | string | Titre de l'offre, nettoyé (balises HTML retirées) |
| `entreprise` | string | Nom de l'entreprise, ou "Confidentiel" |
| `job_type` | string | Type de contrat standardisé : `CDI`, `CDD`, `Stage`, `Alternance`, `Freelance`, `Intérim/Mission`, `VIE`, `Non précisé` |
| `localisation` | string | Ville ou "Flexible" (remote sans ville précisée) |
| `is_remote_job` | bool | Offre en télétravail (total ou partiel détecté) |
| `country` | string | Pays, "France" par défaut |
| `region` | string | Région française déduite (`src/config.py:REGION_KEYWORDS`), ou `Télétravail` / `France Entière (Non précisé)` / `Autre` |
| `salaire` | string | Salaire brut tel que remonté par la source (texte libre, ex. `"45 - 55 K€"`) ; rempli sur ~52% des offres (Adzuna et APEC le renseignent souvent, France Travail rarement) |
| `date_scraping` | date (YYYY-MM-DD) | Date de collecte |
| `date_publication` | date (YYYY-MM-DD) | Date de publication sur le site source, si disponible |
| `date_poste` | date (YYYY-MM-DD) | `date_publication` si connue, sinon `date_scraping` |
| `source` | string | `APEC`, `France Travail` ou `Adzuna` |
| `lien` | string (URL) | Lien vers l'offre originale |
| `description` | string | Texte complet de l'offre, nettoyé |
| `experience_estimee` | string | `Junior`, `Confirmé`, `Senior`, ou `Non précisé` — déduit du texte |
| `niveau_etude_estime` | string | `Bac+3/4`, `Bac+5`, `PhD`, ou `Non précisé` |
| `job_category` | string | `Data Scientist`, `Data Engineer`, `Data Analyst`, `Alternance`, `Stage`, `Autre rôle Data`, `Non spécifié` |

## Colonnes de compétences

Une colonne booléenne (0/1) par compétence détectée dans la description,
générées depuis `src/config.py:SKILL_PATTERNS` (~45 colonnes : `Python`,
`SQL`, `Spark`, `Power BI`, `AWS`, `Docker`, `Agile`, `Anglais`, ...).

## `offres_skills_long.csv` (format dérivé, long)

| Colonne | Description |
|---|---|
| `id_offre` | Identifiant technique (index) |
| `titre`, `entreprise`, `source` | Repris de la couche large |
| `Competence` | Nom de la compétence détectée |

Une ligne par couple (offre, compétence détectée) — uniquement les
compétences présentes. Pratique pour un `GROUP BY Competence` en SQL ou
un `melt` côté Tableau, sans recalculer quoi que ce soit : c'est la même
donnée que `offres_enriched.csv`, juste pivotée.

## Schéma en étoile (`data/warehouse.db`)

En plus du format plat, la même donnée est modélisée en fait + dimensions
(voir [`docs/architecture.md`](docs/architecture.md#schéma-en-étoile-srcgoldstar_schemapy)
pour le diagramme et le détail) :

| Table | Type | Clé | Contenu |
|---|---|---|---|
| `fact_offres` | Fait | `offre_id` | Mesures (`salaire_min`, `salaire_max`) + FK vers les dimensions |
| `dim_entreprise` | Dimension | `entreprise_id` | Nom d'entreprise |
| `dim_localisation` | Dimension | `localisation_id` | Ville, région, pays, remote |
| `dim_source` | Dimension | `source_id` | APEC / France Travail / Adzuna |
| `dim_date` | Dimension | `date_id` | Date, année, mois, trimestre |
| `dim_competence` | Dimension | `competence_id` | Une des ~45 compétences |
| `fact_offre_competence` | Table pont | `offre_id`, `competence_id` | Relation many-to-many offre↔compétence |

`salaire_min`/`salaire_max` sont extraits du champ `salaire` texte libre
par `_parse_salaire()` (`src/gold/star_schema.py`), qui normalise les 3
formats sources (raccourci "k€" pour APEC, "Mensuel"/"Annuel" en euros
complets pour France Travail, euros complets sans période pour Adzuna) en
un montant annuel comparable.

## Écart avec `data/gold/legacy/jobs_dataset_final_v5.csv`

Ce fichier historique contient 3 colonnes que le pipeline actuel ne
génère toujours pas :

| Colonne absente du pipeline | Raison |
|---|---|
| `job_category_clean` | Variante manuelle de `job_category`, jamais implémentée en code |
| `duree_contrat` | Jamais calculée dans le code versionné |
| `region_standardisee` | Doublon manuel de `region` |

Ces colonnes ont été ajoutées à la main (notebook/Excel) sur un export
ponctuel. Elles ne sont pas reproduites par le pipeline actuel — piste
d'amélioration possible plutôt que dette cachée.

`salaire_estime` (jamais implémentée dans le fichier legacy) est en
revanche désormais couverte : l'ajout de la source Adzuna a introduit un
vrai champ `salaire` en couche gold, rempli sur ~52% des offres.
