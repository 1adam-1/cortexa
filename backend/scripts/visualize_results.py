import os
import pandas as pd

# Chemins absolus
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(current_dir, "../evaluation/predictions_ragas_results.csv")
html_path = os.path.join(current_dir, "../evaluation/rapport_evaluation.html")

def generate_report():
    if not os.path.exists(csv_path):
        print(f"Le fichier de résultats {csv_path} est introuvable.")
        return

    # Charger les résultats
    df = pd.read_csv(csv_path)

    # Fonction pour colorer les scores
    def color_score(val):
        if pd.isna(val): return 'background-color: lightgrey; color: black;'
        if isinstance(val, (int, float)):
            if val >= 0.8: return 'background-color: #d4edda; color: #155724; font-weight: bold;' # Vert
            elif val >= 0.5: return 'background-color: #fff3cd; color: #856404;' # Jaune
            else: return 'background-color: #f8d7da; color: #721c24; font-weight: bold;' # Rouge
        return ''

    # Appliquer le style aux colonnes de métriques
    metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']
    existing_metrics = [m for m in metrics if m in df.columns]

    # Définir le style CSS général du tableau
    properties = {
        'text-align': 'left', 
        'white-space': 'pre-wrap', 
        'max-width': '400px', 
        'vertical-align': 'top',
        'padding': '10px',
        'border': '1px solid #dee2e6'
    }
    
    headers_style = [{
        'selector': 'th', 
        'props': [
            ('background-color', '#343a40'), 
            ('color', 'white'), 
            ('font-size', '16px'),
            ('padding', '10px')
        ]
    }]

    # Création de l'objet Styler (gère applymap ou map selon la version de pandas)
    styler = df.style.set_properties(**properties).set_table_styles(headers_style)
    
    try:
        styled_df = styler.map(color_score, subset=existing_metrics)
    except AttributeError:
        styled_df = styler.applymap(color_score, subset=existing_metrics)

    # Calcul des moyennes pour l'affichage
    means_html = "<div style='margin-top: 30px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 20px rgba(0,0,0,0.1); display: inline-block;'>"
    means_html += "<h2>Moyennes des métriques (Scores finaux)</h2><ul style='list-style-type: none; padding-left: 0;'>"
    for m in existing_metrics:
        # Calcule la moyenne en ignorant les cases vides/NaN
        mean_val = df[m].mean()
        
        # Logique de couleur similaire au tableau pour la moyenne
        span_style = "color: black"
        if not pd.isna(mean_val):
            if mean_val >= 0.8: span_style = "background-color: #d4edda; color: #155724; padding: 3px 8px; border-radius: 4px; font-weight: bold;"
            elif mean_val >= 0.5: span_style = "background-color: #fff3cd; color: #856404; padding: 3px 8px; border-radius: 4px; font-weight: bold;"
            else: span_style = "background-color: #f8d7da; color: #721c24; padding: 3px 8px; border-radius: 4px; font-weight: bold;"
            means_html += f"<li style='margin-bottom: 15px; font-size: 18px;'><strong>{m.replace('_', ' ').title()} :</strong> <span style='{span_style}'>{mean_val:.4f}</span></li>"
        else:
            means_html += f"<li style='margin-bottom: 15px; font-size: 18px;'><strong>{m.replace('_', ' ').title()} :</strong> N/A</li>"
    means_html += "</ul></div>"

    # Exporter en HTML
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Rapport d'évaluation RAG</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f8f9fa; }}
            h1, h2 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; zoom: 0.9; margin-bottom: 20px; background-color: white; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
        </style>
    </head>
    <body>
        <h1>Rapport d'évaluation Ragas</h1>
        {styled_df.to_html()}
        {means_html}
    </body>
    </html>
    """

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"Rapport HTML généré avec succès dans : {html_path}")

if __name__ == "__main__":
    generate_report()