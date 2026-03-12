function toggleReponses(index) {
    document.getElementById(`reponses-${index}`).classList.toggle("hidden");
}

async function save_answers_points()
{
    let string = "";
    let jsonAns = {}
    let points = document.getElementsByClassName("input-ans-point");
    for (let p of points){
        let id_html = p.id;
        let value = p.value;

        let id = id_html.split("-").pop();
        if (!(id in jsonAns)){
            jsonAns[id] = {"pos_point":0, "neg_point":0};
        }
        if (id_html.split("-").includes("pos"))
        {
            jsonAns[id]["pos_point"] = parseInt(value);
        }else{
            jsonAns[id]["neg_point"] = parseInt(value);
        }
    }

    const response = await fetch("/webamc/my_questions/save", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({"jsonAns":jsonAns})
    });
    res = await response.json();
    console.log(res);
    
    if (res.status == "success")
    {
        await Swal.fire({
            title: 'Succès !',
            text: "Vos réponses ont bien été enregistrée",
            icon: 'success',
            confirmButtonText: 'OK',
            confirmButtonColor: '#3085d6', // Couleur du bouton
            background: '#fff', // Couleur de fond
        });
    }else{
        await Swal.fire({
            title: 'Erreur !',
            text: "Un problème est survenu",
            icon: 'error',
            confirmButtonText: 'OK',
            confirmButtonColor: '#3085d6', // Couleur du bouton
            background: '#fff', // Couleur de fond
        });
    }

}


var filter_type = "tag";
var questionsDiv = null;
var filterMode = false;
function initData()
{
    questionsDiv = document.getElementsByClassName("questions-list-div");
    questionsDiv = Array.from(questionsDiv);
    questionsDiv.forEach((e)=> {
        e = e.cloneNode(true);
    });

    document.getElementById("remove-filter-btn").disabled = !filterMode;
    console.log("Data initialized");
}

function toggleFilterOptions() {
    let filterDiv = document.getElementById("filter-options");
    filterDiv.style.display = (filterDiv.style.display === "none" || filterDiv.style.display === "") ? "block" : "none";
}

function toggleFilterType(type) {
    filter_type = type;
    document.getElementById('filter-tag-container').style.display = (type === 'tag') ? 'block' : 'none';
    document.getElementById('filter-code-container').style.display = (type === 'code') ? 'block' : 'none';
}


function applyFilter() {
    let filterType = filter_type;
    let filterValue = document.getElementById(`filter-${filterType}`);
    let value = filterValue.value;
    let questionsListContainer = document.getElementById("questions-list-container");

    let questionsListDiv = questionsDiv.slice();

    let filteredQuestionsList = []; 

    console.log("Len of questionsDiv before : ", questionsDiv.length); // Collection originale

    if (filterType == "tag") {
        filteredQuestionsList = filterByTags(value, questionsListDiv);

    } else {
        filteredQuestionsList = filterByCode(value, questionsListDiv);
    }
    questionsListContainer.innerHTML = '';  // On vide d'abord le conteneur
    questionsListContainer.append(...filteredQuestionsList);  // Ajoute les éléments filtrés
    console.log("Len of filteredQuestionsList after : ", filteredQuestionsList.length); // Liste filtrée

    if (!filterMode)
    {
        filterMode = true;
        document.getElementById("remove-filter-btn").disabled = !filterMode;
    }
}

function filterByTags(acceptedTag, questionsListDiv) {
    let filteredQuestionsList = [];
    for (let qd of questionsListDiv) {
        // Récupère l'attribut 'data-tags' et effectue la recherche pour le tag
        let attrs = qd.getAttribute("data-tags").split(",");
        if (attrs.includes(acceptedTag)) {
            filteredQuestionsList.push(qd);
        }
    }
    return filteredQuestionsList;
}

function filterByCode(code, questionsListDiv) {
    let filteredQuestionsList = [];
    let str1 = "";
    let str2 = "";
    for (let qd of questionsListDiv) {
        // Récupère l'attribut 'data-tags' et effectue la recherche pour le tag
        let attrs = qd.getAttribute("data-qst-code");
        str1 = attrs.toLowerCase();
        str2 = code.toLowerCase();
        if (str1.includes(str2)) {
            filteredQuestionsList.push(qd);
        }
    }
    return filteredQuestionsList;
}


function removeFilter()
{
    let questionsListContainer = document.getElementById("questions-list-container");
    questionsListContainer.innerHTML = '';
    questionsListContainer.append(...questionsDiv);

    filterMode = false;
    document.getElementById("remove-filter-btn").disabled = !filterMode;
}