/**
 * global variables
 */
var filters = [];
var idCounter = 0;
var filters_save = [];
var container;
var download_button;
var save_button;
var jsonContainer;


class Filter {
    constructor(id, parentid, op, arg = null, rev = null, content = []) {
        this.id = id;
        this.parentid = parentid;
        this.op = op;
        this.arg = arg;
        this.rev = rev;
        this.content = content;
        this.div = null;
    }
    createHTML() {
        let color = "";
        switch (this.op) {
        case "all":
            color = "bg-blue-500";
            break;
        case "shuf":
            color = "bg-[#00ff9B]";
            break;
        case "head":
            color = "bg-[#ffc300]";
            break;
        case "with-difficulty":
            color = "bg-[#ff5733]";
            break;
        case "with-code":
            color = "bg-purple-500";
            break;
        case "with-tag":
            color = "bg-blue-700";
            break;
        case "sort":
            color = "bg-[#ff0080]"
            break;
        default:
            break;
        }
        this.div = document.createElement("div");
        this.div.className = "p-4 border rounded " + color
            + " shadow mb-2 cursor-move ml-"
            + (this.parentid !== null || this.parentid != "null" ? "6" : "0");
        this.div.draggable = true;
        this.div.setAttribute("data-id", this.id);
        this.div.setAttribute("data-parent", this.parentid);
        
        
        const filterContent = document.createElement("div");
        filterContent.className = "flex items-center";
        filterContent.style.width = "100%"; 
        
        const textNode = document.createElement("div");
        textNode.innerHTML = `<strong>${this.op}</strong>${this.arg ? ` (arg: ${this.arg}${this.rev ? ', rev: true' : ''})` : ''}`;
        
        const allDeleteButton = document.createElement("button");
        allDeleteButton.style.fontWeight = "bold";
        allDeleteButton.style.borderRadius = "9999px";
        allDeleteButton.style.display = "flex";
        allDeleteButton.style.alignItems = "center";
        allDeleteButton.style.justifyContent = "center";
        allDeleteButton.style.border = "none";
        allDeleteButton.style.cursor = "pointer";
        allDeleteButton.style.padding = "4px"; 
        allDeleteButton.style.backgroundColor = "#ff9800"; // Orange 
        allDeleteButton.style.color = "white"; // Icône en blanc
        allDeleteButton.title = "Supprimer uniquement la boîte";
        allDeleteButton.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" fill="none"
          viewBox="0 0 24 24" stroke-width="2"
          stroke="currentColor" width="20" height="20">
          <path stroke-linecap="round" stroke-linejoin="round"
          d="M6 18L18 6M6 6l12 12"/>
        </svg>`;
        allDeleteButton.onclick = () => {
            this.removeOnlyMe();
        };

        const deleteButton = document.createElement("button");
        deleteButton.style.fontWeight = "bold";
        deleteButton.style.borderRadius = "9999px";
        deleteButton.style.display = "flex";
        deleteButton.style.alignItems = "center";
        deleteButton.style.justifyContent = "center";
        deleteButton.style.border = "none";
        deleteButton.style.cursor = "pointer";
        deleteButton.style.padding = "4px"; 
        deleteButton.style.backgroundColor = "#ef4444"; // Rouge vif 
        deleteButton.style.color = "white";
        deleteButton.title = "Supprimer la boîte et les enfants";
        deleteButton.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" fill="none"
          viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"
          width="20" height="20">
          <path stroke-linecap="round" stroke-linejoin="round"
            d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m2 0v12a2 2 0
              01-2 2H8a2 2 0 01-2-2V6h12z"/>
        </svg>`;
        deleteButton.onclick = () => {
            this.removeFilter();
        };

        const deleteDiv = document.createElement("div");
        deleteDiv.appendChild(allDeleteButton);
        deleteDiv.appendChild(deleteButton);
        deleteDiv.className = "flex flex-row items-center"; 
        deleteDiv.style.gap = "8px"; 
        deleteDiv.style.marginLeft = "auto"; 

        filterContent.appendChild(textNode);
        filterContent.appendChild(deleteDiv);
        this.div.appendChild(filterContent);


        this.div.ondragstart = (e) => {
            e.dataTransfer.setData("id", this.id);
            e.dataTransfer.setData("parentid", this.parentid);
            e.stopPropagation();
        };
        this.div.ondragover = e => e.preventDefault();
        this.div.ondrop = (e) => {
            e.preventDefault();
            e.stopPropagation();
            let target_id = e.dataTransfer.getData("id");
            let target_parentid = e.dataTransfer.getData("parentid");
            if(target_id != this.id && !this.isMyAncestor(filters,target_id)) {
                let target_filter = pack_remove_filter_by_id(
                    target_id, target_parentid
                );
                this.addFilter(target_filter);
                pack_update_html();
            }
        };
        this.content.forEach((childFilter) => {
            this.div.appendChild(childFilter.createHTML());
        });
        return this.div;
    }
    removeFilter() {
        pack_remove_filter_by_id(this.id, this.parentid);
        pack_update_html();
    }
    removeOnlyMe() {
        pack_remove_only_filter(this.id, this.parentid);
        pack_update_html();
    }
    addFilter(filter) {
        filter.parentid = this.id;
        this.content.push(filter);
    }
    isInMyChildOfChild(filters=this.content, id) {
        for (let f of filters) {
            if(f.id == id) {
                return true;
            }
            let found = f.isInMyChildOfChild(f.content, id);
            if(found) {
                return true;
            }
        }
        return false;
    }
    isMyAncestor(filters, id) {
        let ancestor = pack_get_filter_by_id(filters, id);
        if(ancestor) {
            if(ancestor.isInMyChildOfChild(ancestor.content, this.id)) {
                return true;
            }
        }
        return false;
    }
    getJSON() {
        return {
            "op": this.op,
            ...(this.op != "all" && this.op != "shuff" && this.arg != null ?
                {"arg": pack_format_array(this.arg)} : {}),
            ...(((this.op.includes("with")) || this.op == "sort")
                && this.rev != null ? {"rev": this.rev} : {}),
            ...(this.content.length > 0 ? 
                {"content": this.content.length > 1 ? 
                 this.content.filter(f => f !== null).map(f => f.getJSON()):
                 this.content[0] != "null" ? this.content[0].getJSON() : {}}
                : {})
        };
    }
}


const pack_show_json_area = function () {
    let jsonContainer = document.getElementById("jsonOutput");
    if(jsonContainer.style.display == "none") {
        jsonContainer.style.display = "block";
        $("#showjson-button").html("Masquer le JSON");
    } else {
        jsonContainer.style.display = "none";
        $("#showjson-button").html("Afficher le JSON");
    }
}


const pack_format_array = function (array) {
    return array;
}


// const pack_ask_args_for_difficulty = async function (textArg) {
//     let return_val = null;
//     let html = '<div class="flex justify-center items-center gap-4 p-4">';
//     for(var i = 1; i <= 5; i ++) {
//         html += '<div class="circle w-12 h-12 flex items-center justify-center rounded-full border-2 cursor-pointer text-black border-gray-300" data-value="' + i;
//         html += '">' + i + '</div>';
//     }
//     html += '</div>';
//     html += '<label class="flex items-center justify-center gap-2 mt-2">';
//     html += '<input type="checkbox" id="swal-checkbox"';
//     html += 'class="form-checkbox h-5 w-5 text-blue-600">';
//     html += 'Inverser la sélection ?</label>';
//     const { value, isConfirmed } = await Swal.fire({
//         title: textArg,
//         html: html,
//         showCancelButton: true,
//         confirmButtonText: "OK",
//         cancelButtonText: "Annuler",
//         didOpen: () => {
//             const circles = document.querySelectorAll(".circle");
//             let selectedValues = [];
//             circles.forEach(circle => {
//                 circle.addEventListener("click", function () {
//                     const value = this.getAttribute("data-value");
//                     this.classList.toggle("bg-blue-500");
//                     this.classList.toggle("border-blue-500");
//                     if(selectedValues.includes(value)) {
//                         selectedValues = selectedValues.filter(
//                             v => v !== value
//                         );
//                     } else {
//                         selectedValues.push(value);
//                     }
//                 });
//             });
//         },
//         preConfirm: () => {
//             const selected = Array.from(
//                 document.querySelectorAll(".circle.bg-blue-500")
//             ).map(el => parseInt(el.getAttribute("data-value")));
//             const isChecked = document.getElementById("swal-checkbox").checked;
//             if(selected.length === 0) {
//                 Swal.showValidationMessage(
//                     "Veuillez sélectionner au moins une difficulté"
//                 );
//                 return false;
//             }
//             return { selected, isChecked };
//         }
//     });
//     if(isConfirmed && value) {
//         return_val = {
//             value: value.selected,
//             rev: value.isChecked
//         };
//     }
//     return return_val !== null ? return_val : false;
// }

const pack_ask_args_for_difficulty = async function (textArg) {
    return new Promise((resolve) => {
        let html = '<div class="flex justify-center items-center gap-4 p-4">';
        for(var i = 1; i <= 5; i ++) {
            html += '<div class="circle w-12 h-12 flex items-center justify-center rounded-full border-2 cursor-pointer text-black border-gray-300" data-value="' + i + '">' + i + '</div>';
        }
        html += '</div>';
        html += '<label class="flex items-center justify-center gap-2 mt-2">';
        html += '<input type="checkbox" id="swal-checkbox" class="form-checkbox h-5 w-5 text-blue-600">';
        html += 'Inverser la sélection ?</label>';

        alertify.confirm(textArg, html, 
            function(evt) { // Bouton OK
                const selected = Array.from(document.querySelectorAll(".circle.bg-blue-500"))
                                      .map(el => parseInt(el.getAttribute("data-value")));
                const isChecked = document.getElementById("swal-checkbox").checked;
                
                if(selected.length === 0) {
                    alertify.error("Veuillez sélectionner au moins une difficulté");
                    evt.cancel = true; // Empêche la fenêtre de se fermer
                    return;
                }
                resolve({ value: selected, rev: isChecked });
            }, 
            function() { // Bouton Annuler
                resolve(false);
            }
        ).set('labels', {ok:'OK', cancel:'Annuler'});

        // Attache les événements APRES l'affichage
        let selectedValues = [];
        const circles = document.querySelectorAll(".circle");
        circles.forEach(circle => {
            circle.addEventListener("click", function () {
                const value = this.getAttribute("data-value");
                this.classList.toggle("bg-blue-500");
                this.classList.toggle("border-blue-500");
                if(selectedValues.includes(value)) {
                    selectedValues = selectedValues.filter(v => v !== value);
                } else {
                    selectedValues.push(value);
                }
            });
        });
    });
}


const pack_ask_args_for_code = async function (textArg) {
    return new Promise((resolve) => {
        let html = `
            <input id="swal-input" type="text" style="width:100%; padding:8px; margin-bottom:15px; border:1px solid #ccc; border-radius:4px;" placeholder="Entrez une valeur">
            <label style="display: flex; align-items: center; justify-content:center; gap:10px;">
            <input type="checkbox" id="swal-checkbox"> Inverser la sélection ?
            </label>
        `;
        
        alertify.confirm(textArg, html, 
            function(evt) {
                const inputValue = document.getElementById("swal-input").value;
                const isChecked = document.getElementById("swal-checkbox").checked;
                if(!inputValue) {
                    alertify.error("Veuillez entrer une valeur !");
                    evt.cancel = true;
                    return;
                }
                resolve({ value: inputValue, rev: isChecked });
            }, 
            function() {
                resolve(false);
            }
        ).set('labels', {ok:'OK', cancel:'Annuler'});
    });
}


const pack_ask_args_for_tag = async function (textArg) {
    return new Promise(async (resolve) => {
        let tagsHTML = "";
        let tags = false;
        try {
            const response = await fetch("/webamc/item/oper/get-pack");
            
            // On vérifie si le serveur répond un code d'erreur (ex: 404 Not Found)
            if (!response.ok) {
                throw new Error(`Le serveur a répondu avec une erreur ${response.status}`);
            }

            const data = await response.json();
            
            if(data.length > 0) {
                tags = true
                for (let tag of data) {
                    tagsHTML += `
                        <div id="${tag.tag_id}"
                          class="tag inline-block px-4 py-2 mx-2 border border-gray-300 rounded cursor-pointer hover:bg-blue-500 hover:text-white">
                            ${tag.tag_name}
                        </div>
                    `;
                }
            } else {
                tagsHTML = "<p>La base de données des tags est vide pour le moment.</p>";
            }
        } catch (error) {
            console.error("Erreur détaillée :", error);
            // On affiche la vraie erreur à l'écran !
            tagsHTML = `<p style="color: red; font-weight: bold;">Erreur : ${error.message}</p>`;
        }

        let html = `
            <div id="swal-tags-container">${tagsHTML}</div>
            ${tags ? `<label class="flex items-center justify-center gap-2 mt-3">
            <input type="checkbox" id="swal-checkbox" class="rounded"> Inverser la sélection ?
            </label>
            <style>
            .tag.selected { background-color: #3182ce; color: white; border-color: #3182ce; }
            </style>` : ""}
        `;

        alertify.confirm(textArg, html,
            function() {
                if (tags) {
                    const selectedTags = document.querySelectorAll('.tag.selected');
                    const selectedTagData = [];
                    selectedTags.forEach(tagEl => {
                        selectedTagData.push({ tag_id: tagEl.id, tag_name: tagEl.textContent.trim() });
                    });
                    const rev = document.getElementById('swal-checkbox').checked;
                    resolve({ value: selectedTagData, rev: rev });
                } else {
                    resolve(true);
                }
            },
            function() {
                resolve(false);
            }
        ).set('labels', {ok:'OK', cancel:'Annuler'});

        if (tags) {
            const tagsElements = document.querySelectorAll('.tag');
            tagsElements.forEach(tagEl => {
                tagEl.addEventListener('click', () => { tagEl.classList.toggle('selected'); });
            });
        }
    });
}


const pack_ask_args_for_sort = async function (textArg) {
    return new Promise((resolve) => {
        let selectedValue = null;
        let html = `<div class="flex gap-4 p-4 justify-center items-center">
                 <div class="rectangle w-24 h-12 flex items-center justify-center rounded-lg border-2 cursor-pointer text-black border-gray-300"
                   data-value="difficulty">Difficulté</div>
                 <div class="rectangle w-24 h-12 flex items-center justify-center rounded-lg border-2 cursor-pointer text-black border-gray-300"
                   data-value="code">Code</div>
               </div>
               <label class="flex items-center justify-center gap-2 mt-2">
                   <input type="checkbox" id="swal-checkbox" class="form-checkbox h-5 w-5 text-blue-600">
                   Inverser la sélection ?
               </label>`;

        alertify.confirm(textArg, html,
            function(evt) {
                const isChecked = document.getElementById("swal-checkbox").checked;
                if(!selectedValue) {
                    alertify.error("Veuillez sélectionner un critère de tri");
                    evt.cancel = true;
                    return;
                }
                resolve({ value: selectedValue, rev: isChecked });
            },
            function() { resolve(false); }
        ).set('labels', {ok:'OK', cancel:'Annuler'});

        const rectangles = document.querySelectorAll(".rectangle");
        rectangles.forEach(rectangle => {
            rectangle.addEventListener("click", function () {
                rectangles.forEach(r => r.classList.remove("bg-blue-500", "border-blue-500", "text-white"));
                this.classList.add("bg-blue-500", "border-blue-500", "text-white");
                selectedValue = this.getAttribute("data-value");
            });
        });
    });
}


const pack_ask_args_for_head = async function(text, input="number") {
    return new Promise((resolve) => {
        alertify.prompt(text, "Entrez la valeur :", "", 
            function(evt, value) {
                if(!value) {
                    alertify.error("Veuillez entrer une valeur");
                    evt.cancel = true;
                } else {
                    resolve(value);
                }
            }, 
            function() { resolve(null); }
        ).set('type', input).set('labels', {ok:'OK', cancel:'Annuler'});
    });
}

const pack_ask_args_for_rev = async function (text) {
    return new Promise((resolve) => {
        alertify.confirm("Confirmation", text, 
            function() { resolve(true); },
            function() { resolve(false); }
        ).set('labels', {ok:'Oui', cancel:'Non'});
    });
}

const pack_add_filter = async function (op) {
    arg_selected = false;
    rev_asked = false;
    switch (op) {
    case "head":
        arg_selected = await pack_ask_args_for_head(
            "Combien de questions souhaitez vous ? "
        );
        break;
    case "with-difficulty":
        args = await pack_ask_args_for_difficulty(
            "Quel est le niveau de difficulté ? "
        );
        if(args == false) return;
        arg_selected = args["value"];
        if(arg_selected) {
            rev_asked = args["rev"];
        }
        break; 
    case "with-code":
        args = await pack_ask_args_for_code(
            "Entrer le code du QCM : ", "text"
        );
        if(args == false) return;
        arg_selected = args["value"];
        if(arg_selected) {
            rev_asked = args["rev"];
        }
        break; 
    case "with-tag":
        args = await pack_ask_args_for_tag("Choisir les tags disponibles");
        if(args == false) return;
        arg_selected = args["value"].map(tag => tag.tag_name);
        if(arg_selected) {
            rev_asked = args["rev"];
        }
        break; 
    case "sort":
        args = await pack_ask_args_for_sort("Trier par");
        if(args == false) return;
        arg_selected = args["value"];
        if(arg_selected) {
            rev_asked = args["rev"];
        }
        break;
    default:
        arg_selected = false;
        break;
    }

    if(arg_selected == null) return;
    pack_stack_filters();
    let newFilter = new Filter(
        idCounter++, "null", op, arg_selected, rev_asked==false ? null : true
    );
    newFilter.arg = arg_selected;
    filters.push(newFilter);
    pack_update_html();
}


const pack_get_filter_by_id = function (filters, id) {
    for(let filter of filters) {
        if(filter.id == id) {
            return filter;
        }
        let found = pack_get_filter_by_id(filter.content, id);
        if(found != null) {
            return found;
        }
    }
    return null;
}


const pack_remove_filter_by_id = function (id, parentid) {
    let removedFilter = null;
    if(parentid == "null" || parentid == null) {
        let index = filters.findIndex(f => f.id == id);
        if(index != -1) {
            pack_stack_filters();
            removedFilter = filters.splice(index, 1)[0];
        }
    } else {
        let parentFilter = pack_get_filter_by_id(filters, parentid);
        if(parentFilter != "null" || parentFilter != null) {
            let index = parentFilter.content.findIndex(f => f.id == id);
            if(index != -1) {
                pack_stack_filters();
                removedFilter = parentFilter.content.splice(index, 1)[0];
            }
        }
    }
    return removedFilter;
}


const pack_remove_only_filter = function (id, parentid) {
    let removedFilter = null;
    let filter = pack_get_filter_by_id(filters, id);
    let childs = filter.content.slice();
    for (let f of childs){
        f.parentid = parentid;
    }
    if(parentid == null || parentid == "null") {
        filters = filters.concat(childs);
        let index = filters.findIndex(f => f.id == id);
        if(index != -1){
            pack_stack_filters();
            removedFilter = filters.splice(index, 1)[0];
            console.log("Filters after removing: ", filters);
        }
    } else {
        let parentFilter = pack_get_filter_by_id(filters, parentid);
        parentFilter.content = parentFilter.content.concat(childs);
        let index = parentFilter.content.findIndex(f => f.id == id);
        if(index != -1) {
            pack_stack_filters();
            removedFilter = parentFilter.content.splice(index, 1)[0];
        }
    }
    return removedFilter;
}


const pack_update_html = function() {
    let download_button = document.getElementById("download_button");
    let save_button = document.getElementById("save_button");
    if(filters.length > 0) {
        if(filters.length > 1) {
            document
                .getElementById("jsonOutput")
                .textContent = JSON.stringify(
                    filters.map(f=>f.getJSON()), null, 2
                );
        } else {
            document
                .getElementById("jsonOutput")
                .textContent = JSON.stringify(
                    filters[0].getJSON(), null, 2
                );
        }
        download_button.disabled = false;
        save_button.disabled = false;
    } else {
        download_button.disabled = true;
        save_button.disabled = true;
        document.getElementById("jsonOutput").textContent = "";
    }
    let container = document.getElementById("filtersContainer");
    container.innerHTML = "";
    filters.forEach(f => {
        container.appendChild(f.createHTML());
    });
}


const pack_reset_filters = function () {
    pack_stack_filters();
    filters = [];
    idCounter = 0;
    pack_update_html();
}


const pack_download_json = function () {
    const jsonContent = JSON.stringify(filters.map(f => f.getJSON()), null, 2);
    const blob = new Blob([jsonContent], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = '_pack.json';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}


const pack_import_json = function (jsonObject) {
    pack_stack_filters();
    filters = [];
    idcounter = 0;
    for(let filter of jsonObject) {
        filters.push(pack_get_filter_from_json(filter, null));
    }
    pack_update_html();
}


const pack_add_imported_json = function (jsonObject) {
    pack_stack_filters();
    for(let filter of jsonObject) {
        filters.push(pack_get_filter_from_json(filter, null));
    }
    pack_update_html();
}


const pack_get_filter_from_json = function (jsonFilter, parentFilterId) {
    let op = jsonFilter.op;
    let arg = null;
    let rev = null;
    let content = null;
    if(jsonFilter.hasOwnProperty("arg")) arg = jsonFilter.arg;
    if(jsonFilter.hasOwnProperty("rev")) rev = jsonFilter.rev;
    if(jsonFilter.hasOwnProperty("content")) content = jsonFilter.content;
    let filter = new Filter(idCounter++, parentFilterId, op, arg, rev);
    if(content != null) {
        content = Array.isArray(content) ? content : [content];
        for(jf of content) {
            let f = pack_get_filter_from_json(jf, filter.id);
            filter.content.push(f);
        }
    }
    return filter;
}


const pack_save = async function () {
    let html = `
    <form id="qcm-form" method='POST'>
      <div style="margin-bottom: 15px;">
        <input type="text" id="title" name="title" style="width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;" placeholder="Entrez le titre du QCM" required>
      </div>
      <div>
        <input type="text" id="code" name="code" style="width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;" placeholder="Entrez le code du QCM" required>
      </div>
    </form>
    `;

    alertify.confirm('Nouveau QCM', html, 
        function(evt) {
            const title = document.getElementById("title").value;
            const code = document.getElementById("code").value;
            const json = document.getElementById("jsonOutput").textContent;
            
            if(!title || !code) {
                alertify.error("Veuillez remplir tous les champs");
                evt.cancel = true; 
                return;
            }

            const pack = JSON.parse(json);
            const formData = { title, code, pack };

            const success = function (_) {
                pack_reset_filters();
                base_report_infos(['MCQ loaded']); // Alerte native du créateur
                alertify.success("Sauvegardé avec succès !"); // Petit toast vert
            };
            xhr_post_oper(Constants.path_item_oper_save_pack, formData, success);
        },
        function() {} // Annuler
    ).set('labels', {ok:'Sauvegarder', cancel:'Annuler'});
}


const pack_stack_filters = function () {
    if(filters != []) {
        if(filters_save == null) {
            filters_save = []
        } else {
            let filters_copy = pack_copy_filters(filters.slice());
            filters_save.push(filters_copy);
        }
    } else {
        filters_save = null;
    }
}


const pack_copy_filters = function (filters) {
    for (let f of filters){
        f.content = f.content.slice();
        pack_copy_filters(f.content);
    }
    return filters;
}


const pack_init = function () {
    filters = [];
    idCounter = 0;
    filters_save = [];
    container = document.getElementById("filtersContainer");
    download_button = document.getElementById("download_button");
    download_button.disabled = true;
    save_button = document.getElementById("save_button");
    save_button.disabled = true;
    jsonContainer = document.getElementById("jsonOutput");
    jsonContainer.style.display = "none";
    document
        .getElementById("save_button")
        .addEventListener("click", async function(event){
            await pack_save();
        });

    document
        .getElementById("import_button")
        .addEventListener("change", function(event) {
            const file = event.target.files[0];
            if(!file) return;
            const reader = new FileReader();
            reader.onload = function(event) {
                try {
                    const jsonData = JSON.parse(event.target.result);
                    pack_import_json(jsonData);
                } catch (error) {
                    console.error("Erreur lors du parsing du JSON :", error);
                }
            };
            reader.readAsText(file);
        });
    
    document
        .getElementById("add_import_button")
        .addEventListener("change", function(event) {
            const file = event.target.files[0];
            if(!file) return;
            const reader = new FileReader();
            reader.onload = function(event) {
                try {
                    const jsonData = JSON.parse(event.target.result);
                    pack_add_imported_json(jsonData);
                } catch (error) {
                    console.error("Erreur lors du parsing du JSON :", error);
                }
            };
            reader.readAsText(file);
        });

    container.ondragover = e => e.preventDefault();
    container.ondrop = (e) => {
    e.stopPropagation();
        e.preventDefault();
        let target_id = e.dataTransfer.getData("id");
        let target_parentid = e.dataTransfer.getData("parentid");
        if(target_parentid != "null" || target_parentid == null) {
            let target_filter = pack_remove_filter_by_id(
                target_id, target_parentid
            );
            target_filter.parentid = null;
            filters.push(target_filter);
            pack_update_html();
        }
    };
}
