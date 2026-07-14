"""Charge les couches bronze/silver/gold dans une base SQLite unique.

Permet de requêter le pipeline en SQL direct (`data/warehouse.db`) et de
connecter un outil BI (Tableau, DBeaver...) sans étape d'import manuelle.
"""
import sqlite3

from src.config import WAREHOUSE_DB


def load_table(df, table_name, db_path=WAREHOUSE_DB):
    with sqlite3.connect(db_path) as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    print(f"Table '{table_name}' chargée dans {db_path} ({len(df)} lignes)")
