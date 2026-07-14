import pandas as pd

# Charger le fichier CSV
df = pd.read_csv('jobs_dataset_final_v5.csv')

tech_skills = ['Python', 'SQL', 'Power BI', 'Azure', 'Git', 'Java', 'GCP', 'NLP', 
               'AWS', 'Docker', 'R', 'Spark', 'CI/CD']

# Colonnes techniques réellement présentes
tech_cols_present = [c for c in tech_skills if c in df.columns]

df_tech_pivot = df.melt(
    id_vars=['titre', 'entreprise', 'job_category_clean', 'localisation', 
             'job_type', 'experience_estimee'],
    value_vars=tech_cols_present,
    var_name='Tech Skill',
    value_name='Presence Tech'
)

# Sauvegarde en Excel
df_tech_pivot.to_excel('jobs_heatmap_data.xlsx', index=False)

print(f"Fichier créé : {len(df_tech_pivot)} lignes, colonnes : {df_tech_pivot.columns.tolist()}")