"""Constantes métier partagées par les couches bronze/silver/gold.

Centralise ce qui était auparavant dupliqué ou éparpillé dans chaque
script (listes de villes, mots-clés de contrat, compétences techniques...).
"""
import os

# --- Chemins ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
BRONZE_DIR = os.path.join(DATA_DIR, "bronze")
SILVER_DIR = os.path.join(DATA_DIR, "silver")
GOLD_DIR = os.path.join(DATA_DIR, "gold")
WAREHOUSE_DB = os.path.join(DATA_DIR, "warehouse.db")

# --- Contrats ---
CONTRACT_KEYWORDS = ["alternance", "stage", "cdi", "cdd", "freelance", "alternant"]

ADZUNA_CONTRACT_MAP = {
    "permanent": "CDI",
    "contract": "CDD",
}

APEC_CONTRACT_CODES = {
    "101888": "CDI",
    "101887": "CDD",
    "597137": "Intérim/Mission",
    "597141": "Alternance",
}

# --- Localisation ---
MAJOR_CITIES = [
    "Paris", "Lyon", "Marseille", "Bordeaux", "Toulouse", "Nantes",
    "Lille", "Strasbourg", "Rennes", "Grenoble", "Montpellier", "Nice",
    "Sophia Antipolis", "Saclay", "Puteaux", "Boulogne", "Levallois",
    "La Défense", "Massy", "Vélizy", "Courbevoie", "Issy",
]

REMOTE_KEYWORDS = ["télétravail", "remote", "à distance"]

IDF_KEYWORDS = [
    "paris", "boulogne", "levallois", "puteaux", "massy", "vélizy",
    "saclay", "versailles", "saint-cloud", "neuilly", "issy", "montrouge",
    "courbevoie", "nanterre", "défense", "suresnes", "rueil", "clichy",
    "ivry", "pantin", "saint-denis", "bagneux", "fontenay", "vincennes",
    "creteil", "cergy",
]
IDF_POSTAL_PREFIXES = r"\b(75|92|93|94|91|95|77|78)\d{0,3}\b"

# Ordre = priorité de correspondance (le premier match l'emporte),
# reproduisant l'ordre du if/elif d'origine dans clean_data.py.
REGION_KEYWORDS = {
    "Île-de-France": IDF_KEYWORDS,
    "Auvergne-Rhône-Alpes": ["lyon", "villeurbanne", "69", "grenoble", "38"],
    "PACA": ["marseille", "aix", "sophia", "nice", "06", "13"],
    "Nouvelle-Aquitaine": ["bordeaux", "merignac", "pessac", "33"],
    "Occitanie": ["toulouse", "blagnac", "31", "montpellier", "34"],
    "Pays de la Loire": ["nantes", "44"],
    "Bretagne": ["rennes", "35"],
    "Hauts-de-France": ["lille", "villeneuve", "59"],
    "Grand Est": ["strasbourg", "67"],
}

# --- Compétences techniques (couche gold) ---
SKILL_PATTERNS = {
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
    "Power BI": [r"power bi", r"powerbi", r"dax"],
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
    "Gestion de projet": [r"gestion de projet", "chef de projet"],
}

EDUCATION_LEVELS = {
    "Bac+5": [r"bac\+5", r"master", r"ingénieur", r"msc", r"grande école"],
    "Bac+3/4": [r"bac\+3", r"bac\+4", r"licence", r"bachelor"],
    "PhD": [r"phd", r"doctorat", r"docteur"],
}
