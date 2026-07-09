// src/webamc/static/js/stats.js

// storing chart instance
let currentChartInstance = null;
let evolutionChartInstance = null;

// handling question change
function handleQuestionChange(qstId) {
    if (!qstId) {
        console.error("Annulation : qstId est vide.");
        return;
    }

    const urlParams = new URLSearchParams(window.location.search);
    let examId = urlParams.get("exam_id");

    // fallback: if exam_id is not in URL, get it from the overview selector
    if (!examId) {
        const overviewSelector = document.getElementById("overview_exam_selector");
        if (overviewSelector) {
            examId = overviewSelector.value;
        }
    }


    // safety check
    if (!examId) {
        console.error("Error: exam_id introuvable ni dans l'URL ni dans le selecteur.");
        return;
    }

    fetch('/webamc/stats/oper/graph-data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(
            { 
                qst_id: parseInt(qstId),
                exam_id: parseInt(examId)
            }
        )
    })
    .then(async response => {
        if (!response.ok) throw new Error(`HTTP Error ${response.status}`);
        return response.json();
    })
    .then(data => {
        const backgroundColors = [];
        
        const redShades = ["#dc3545", "#e4606d", "#ef8a93", "#f6b4b9"];
        let redIndex = 0;

        data.choices_info.forEach(choice => {
            if (choice.is_no_response){
                choice.exactColor = "#6c757d"; }
            else if (choice.is_correct) {
                choice.exactColor = "#28a745"; 
            } else {
                choice.exactColor = redShades[redIndex % redShades.length];
                redIndex++;
            }
            backgroundColors.push(choice.exactColor);
        });

        // updating chart
        updateChart(data.labels, data.data, data.total_students, backgroundColors);
        
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

    const choicesDiv = document.getElementById("choices_container");
    if (choicesDiv && choicesInfo) {
        const translatedTitle = choicesDiv.getAttribute("data-title") || "Détail des réponses :";
        const translatedAnswer = choicesDiv.getAttribute("data-answer") || "Réponse";

        choicesDiv.innerHTML = `<h3>${translatedTitle}</h3>`;
        
        const ul = document.createElement("ul");
        ul.style.listStyle = "none";
        ul.style.padding = "0";

        choicesInfo.forEach(choice => {
            const li = document.createElement("li");
            li.style.marginBottom = "15px";
            const textColor = choice.exactColor;

            if (choice.is_no_response) {
                li.innerHTML = `
                    <strong style="color: ${textColor};">${translatedAnswer} ${choice.letter} :</strong>
                    <span style="color: #666; font-style: italic; margin-left: 10px;">(Aucune réponse)</span>
                `;}
            else{
            li.innerHTML = `
                <strong style="color: ${textColor};">${translatedAnswer} ${choice.letter} :</strong>
                <img src="/webamc/img?itm_id=${choice.id}&iti_num=1" style="max-height: 80px; border: 1px solid #ddd; margin-top: 5px; border-radius: 4px;">
            `;}
            ul.appendChild(li);
        });

        choicesDiv.appendChild(ul);
    }
}

// drawing the chart
function updateChart(labels, dataValues, totalStudents,colors) {
    const element = document.getElementById("chart");
    if (!element) {
        console.error("Error: Cannot find the element with id='chart'");
        return;
    }

    // destroying previous chart if exists
    if (currentChartInstance) {
        currentChartInstance.destroy();
    }

    const yAxisMax = totalStudents > 0 ? totalStudents : 10;

    // creating new chart
    currentChartInstance = new Chart(element, {
        type: "bar",
        data: {
            labels: labels, 
            datasets: [{
                label: "Number of students", 
                data: dataValues, 
                backgroundColor: colors ||"#007bff",
                maxBarThickness: 50
            }]
        },
        options: {
            maintainAspectRatio: false,
            scales: { 
                y: { 
                    beginAtZero: true,
                    max: yAxisMax,
                    ticks: {
                        stepSize: 1
                    } 
                } 
            }
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
        drawEvolutionChart(data.labels, data.data, data.max_score);
    })
    .catch(error => console.error('Erreur:', error));
}

function drawEvolutionChart(labels, dataValues, maxScore) {
    const element = document.getElementById("evolution_chart");
    if (!element) return;

    if (evolutionChartInstance) {
        evolutionChartInstance.destroy();
    }

    const yAxisMax = maxScore > 0 ? maxScore : 10;

    let calculatedStepSize = 1;
    if (yAxisMax > 8) {
        calculatedStepSize = yAxisMax / 8; 
    }

    evolutionChartInstance = new Chart(element, {
        type: "bar", 
        data: {
            labels: labels, 
            datasets: [{
                label: "Note obtenue", 
                data: dataValues, 
                backgroundColor: "#007bff", 
                maxBarThickness: 50,
                minBarLength: 5 
            }]
        },
        options: {
            maintainAspectRatio: false,
            scales: { 
                y: { 
                    beginAtZero: true,
                    max: yAxisMax, 
                    ticks: {
                        stepSize: calculatedStepSize,
                        autoSkip: false,
                        callback: function(value) {
                            return value.toFixed(1); 
                        }
                    },
                    title: { display: true, text: 'Score' }
                },
                x: {
                    title: { display: true, text: 'Date de passage' }
                }
            }
        }
    });
}



// storing mcq overview chart instance
let mcqChartInstance = null;

// fetching data and drawing the MCQ overview chart
function loadMcqOverview(examId) {
    if (!examId) return;

    fetch('/webamc/stats/oper/mcq-overview-data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exam_id: parseInt(examId) })
    })
    .then(async response => {
        if (!response.ok) throw new Error(`HTTP Error ${response.status}`);
        return response.json();
    })
    .then(data => {
        const barColors = [];

        data.data.forEach(percentage => {
            if (percentage >= 80) {
                barColors.push("#28a745"); 
            } else if (percentage >= 60) {
                barColors.push("#85c85b"); 
            } else if (percentage >= 40) {
                barColors.push("#ffc107"); 
            } else if (percentage >= 20) {
                barColors.push("#fd7e14"); 
            } else {
                barColors.push("#dc3545"); 
            }
        });
        // data.labels -> ["Question A", "Question B", ...]
        // data.data -> [85, 42, ...] (success percentage)
        // data.qst_ids -> [12, 15, ...] (real question IDs from DB)
        drawMcqChart(data.labels, data.data, data.qst_ids,barColors);
    })
    .catch(error => console.error('Error:', error));
}

// drawing the mcq overview chart
function drawMcqChart(labels, dataValues, qstIds, colors) {
    const element = document.getElementById("mcq_overview_chart"); 
    if (!element) return;

    // destroying previous chart if exists
    if (mcqChartInstance) {
        mcqChartInstance.destroy();
    }

    // creating new chart
    mcqChartInstance = new Chart(element, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Success rate (%)", 
                data: dataValues,
                backgroundColor: colors|| "#28a745", 
                maxBarThickness: 50
            }]
        },
        options: {
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100 //
                },
                x: {
                    ticks: {
                        maxRotation: 90,
                        minRotation: 90 
                    }
                }
            },
            // handling click event on bars
            // handling click event on bars
            onClick: (event, activeElements) => {
                if (activeElements.length > 0) {
                    const dataIndex = activeElements[0].index;
                    const clickedQstId = qstIds[dataIndex];
                    
                    const qstSelector = document.getElementById("qst_selector");
                    if (qstSelector) {
                        qstSelector.value = clickedQstId;
                    }

                    handleQuestionChange(clickedQstId);
                } else {
                    console.log("Clic dans le vide (pas sur une barre).");
                }
            }
        }
    });
}