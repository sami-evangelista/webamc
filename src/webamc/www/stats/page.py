#!/usr/bin/env python3
# pylint: disable-all

"""
from webamc.www import html_elements as he
from webamc.www import base


def generate_stats_page(stats_data) -> he.Element:
    "Generate the statistics as a pie chart using Chart.js"
  
    # Prépare les données pour le graphique 
    labels = [entry['tag'] for entry in stats_data]
    correct_data = [entry['correct'] for entry in stats_data]
    incorrect_data = [entry['incorrect'] for entry in stats_data]
    
    # HTML de la page avec un graphique camembert
    return he.Html(
        he.Head(he.Title("Statistiques des Réponses")),
        he.Body(
            he.H1("Statistiques des Réponses par Tag"),
            he.Canvas(id="statsPieChart"),  # Canvas pour Chart.js
            he.Script(src="https://cdn.jsdelivr.net/npm/chart.js"),  # Lien vers Chart.js
            he.Script("
                const statsData = " + json.dumps({
                    "labels": labels,
                    "correct": correct_data,
                    "incorrect": incorrect_data
                }) + ";
                
                const ctx = document.getElementById('statsPieChart').getContext('2d');
                new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: statsData.labels,
                        datasets: [{
                            data: statsData.correct.concat(statsData.incorrect),
                            backgroundColor: ['green', 'red'],
                            label: 'Réponses'
                        }]
                    },
                    options: {
                        responsive: true
                    }
                });
            ")  # Script JS pour Chart.js
        )
    )

"""
