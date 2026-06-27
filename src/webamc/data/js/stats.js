// src/webamc/static/js/stats.js

// storing chart instance
let currentChartInstance = null;
let evolutionChartInstance = null;

// handling question change
function handleQuestionChange(qstId) {
    if (!qstId) return;

    fetch('/webamc/stats/oper/graph-data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ qst_id: parseInt(qstId) })
    })
    .then(async response => {
        if (!response.ok) throw new Error(`HTTP Error ${response.status}`);
        return response.json();
    })
    .then(data => {
        // updating chart
        updateChart(data.labels, data.data);
        
        // updating images
        updateDetails(qstId, data.choices_info);
    })
    .catch(error => console.error('Error:', error));
}

// updating question and choices images
function updateDetails(qstId, choicesInfo) {
    // showing main question image
    const qstImg = document.getElementById("qst_image");
    if (qstImg) {
        qstImg.src = "/webamc/img?itm_id=" + qstId + "&iti_num=1";
        qstImg.style.display = "block";
    }

    // building choices list with images
    const choicesDiv = document.getElementById("choices_container");
    if (choicesDiv && choicesInfo) {
        choicesDiv.innerHTML = "<h3>Answers detail:</h3>";
        
        const ul = document.createElement("ul");
        ul.style.listStyle = "none";
        ul.style.padding = "0";

        choicesInfo.forEach(choice => {
            const li = document.createElement("li");
            li.style.marginBottom = "15px";
            
            // adding answer letter and image
            li.innerHTML = `
                <strong>Answer ${choice.letter}:</strong><br>
                <img src="/webamc/img?itm_id=${choice.id}&iti_num=1" style="max-height: 80px; border: 1px solid #ddd; margin-top: 5px; border-radius: 4px;">
            `;
            ul.appendChild(li);
        });

        choicesDiv.appendChild(ul);
    }
}

// drawing the chart
function updateChart(labels, dataValues) {
    const element = document.getElementById("chart");
    if (!element) {
        console.error("Error: Cannot find the element with id='chart'");
        return;
    }

    // destroying previous chart if exists
    if (currentChartInstance) {
        currentChartInstance.destroy();
    }

    // creating new chart
    currentChartInstance = new Chart(element, {
        type: "bar",
        data: {
            labels: labels, 
            datasets: [{
                label: "Number of students", 
                data: dataValues, 
                backgroundColor: "#007bff"
            }]
        },
        options: {
            scales: { y: { beginAtZero: true } }
        }
    });
}
function triggerEvolutionChart() {
    const studentId = document.getElementById("evo_student_selector").value;
    const mcqId = document.getElementById("evo_mcq_selector").value;

    if (!studentId || !mcqId) return;

    fetch('/webamc/stats/oper/evolution-data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            student_id: parseInt(studentId),
            mcq_id: parseInt(mcqId)
        })
    })
    .then(async response => {
        if (!response.ok) throw new Error(`Erreur HTTP: ${response.status}`);
        return response.json();
    })
    .then(data => {
        drawEvolutionChart(data.labels, data.data);
    })
    .catch(error => console.error('Erreur:', error));
}

function drawEvolutionChart(labels, dataValues) {
    const element = document.getElementById("evolution_chart");
    if (!element) return;

    if (evolutionChartInstance) {
        evolutionChartInstance.destroy();
    }

    evolutionChartInstance = new Chart(element, {
        type: "line", 
        data: {
            labels: labels, 
            datasets: [{
                label: "Note obtenue", 
                data: dataValues, 
                borderColor: "#28a745", 
                backgroundColor: "rgba(40, 167, 69, 0.2)", 
                borderWidth: 2,
                pointBackgroundColor: "#17a2b8", 
                pointRadius: 5,
                fill: true,
                tension: 0.3 
            }]
        },
        options: {
            scales: { 
                y: { 
                    beginAtZero: true,
                    title: { display: true, text: 'Score' }
                },
                x: {
                    title: { display: true, text: 'Date de passage' }
                }
            }
        }
    });
}