# Analyse de l'Employabilité Data Science

Ce projet vise à analyser le marché de l'emploi en Data Science en France à travers la collecte et le traitement de données d'offres d'emploi.

## Objectifs

*   **Collecte de données** : Scraping automatisé d'offres d'emploi (Welcome to the Jungle, APEC, France Travail, etc.).
*   **Traitement** : Nettoyage, structuration et enrichissement des données.

## Structure du Projet

*   `main.py`: Point d'entrée principal pour lancer le scraping et le traitement des données.
*   `data/` : Contient les données brutes et traitées (`.csv`).
*   `src/` : Code source de l'application.
    *   `src/scrapers/` : Scripts Python pour le scraping des données.
    *   `src/data_processing/` : Scripts Python pour le nettoyage, la fusion et l'enrichissement des données.
    *   `src/__init__.py`: Fichier d'initialisation du package `src`.
*   `dev_scripts/`: Scripts utilitaires pour le débogage ou les tests.
*   `env/` : Environnement virtuel Python.
*   `README.md`: Ce fichier.

## Technologies Utilisées

*   **Python** (BeautifulSoup4, Selenium, Pandas, Requests)
*   **Git** (Gestion de version)

## Comment lancer le projet

1.  **Cloner le dépôt**
    ```bash
    git clone <URL_DU_DEPOT>
    cd <NOM_DU_DEPOT>
    ```
2.  **Créer et activer l'environnement virtuel**
    ```bash
    python -m venv env
    source env/bin/activate  # Sur Linux/macOS
    # ou .\env\Scripts\activate  # Sur Windows
    ```
3.  **Installer les dépendances**
    ```bash
    pip install -r requirements.txt
    ```
    (Note: Le fichier `requirements.txt` n'existe pas encore et devra être créé.)
4.  **Lancer le processus complet**
    ```bash
    python main.py
    ```

## Auteur

**Liza Bérénice Makani**
Étudiante Ingénieure - ESIEA (IA & Data Science)