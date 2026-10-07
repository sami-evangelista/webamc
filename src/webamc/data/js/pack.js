class Filter {
    constructor(id, parentid, op, pack, arg, rev) {
        this.id = id;
        this.parentid = parentid;
        this.op = op;
        this.pack = pack;
        this.arg = arg;
        this.rev = rev;
        this.div = null;
        this.content = [];
    }
    create_html() {
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
        case "difficulty":
            color = "bg-[#ff5733]";
            break;
        case "tag":
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
        textNode.innerHTML =
            `<strong>${this.op}</strong>${this.arg ? `
        (arg: ${this.arg}${this.rev ? ', rev: true' : ''})` : ''}`;
        
        const allDeleteButton = document.createElement("button");
        allDeleteButton.style.fontWeight = "bold";
        allDeleteButton.style.borderRadius = "9999px";
        allDeleteButton.style.display = "flex";
        allDeleteButton.style.alignItems = "center";
        allDeleteButton.style.justifyContent = "center";
        allDeleteButton.style.border = "none";
        allDeleteButton.style.cursor = "pointer";
        allDeleteButton.style.padding = "4px"; 
        allDeleteButton.style.backgroundColor = "#ff9800";
        allDeleteButton.style.color = "white";
        allDeleteButton.title = "Supprimer uniquement la boîte";
        allDeleteButton.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" fill="none"
          viewBox="0 0 24 24" stroke-width="2"
          stroke="currentColor" width="20" height="20">
          <path stroke-linecap="round" stroke-linejoin="round"
          d="M6 18L18 6M6 6l12 12"/>
        </svg>`;
        allDeleteButton.onclick = () => {
            this.remove_only_me();
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
        deleteButton.style.backgroundColor = "#ef4444";
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
            this.remove_filter();
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
            if(target_id != this.id
               && !this.is_my_ancestor(this.pack.filters, target_id)) {
                let target_filter = this.pack.remove_filter_by_id(
                    target_id, target_parentid
                );
                this.add_filter(target_filter);
                this.pack.update_html();
            }
        };
        this.content.forEach((childFilter) => {
            this.div.appendChild(childFilter.create_html());
        });
        return this.div;
    }
    remove_filter() {
        this.pack.remove_filter_by_id(this.id, this.parentid);
        this.pack.update_html();
    }
    remove_only_me() {
        this.pack.remove_only_filter(this.id, this.parentid);
        this.pack.update_html();
    }
    add_filter(filter) {
        filter.parentid = this.id;
        this.content.push(filter);
    }
    is_in_my_child_of_child(filters=this.content, id) {
        for (let f of filters) {
            if(f.id == id) {
                return true;
            }
            let found = f.is_in_my_child_of_child(f.content, id);
            if(found) {
                return true;
            }
        }
        return false;
    }
    is_my_ancestor(filters, id) {
        let ancestor = this.pack.get_filter_by_id(filters, id);
        if(ancestor) {
            if(ancestor.is_in_my_child_of_child(ancestor.content, this.id)) {
                return true;
            }
        }
        return false;
    }
    get_json() {
        return {
            "op": this.op,
            ...(this.op != "all" && this.op != "shuff" && this.arg != null ?
                {"arg": this.pack.format_array(this.arg)} : {}),
            ...(((this.op.includes("with")) || this.op == "sort")
                && this.rev != null ? {"rev": this.rev} : {}),
            ...(this.content.length > 0 ? 
                {"content": this.content.length > 1 ? 
                 this.content.filter(f => f !== null).map(f => f.get_json()):
                 this.content[0] != "null" ? this.content[0].get_json() : {}}
                : {})
        };
    }
}


class Pack {
    show_json_area() {
        let json_container = document.getElementById("jsonOutput");
        if(json_container.style.display == "none") {
            json_container.style.display = "block";
            $("#showjson-button").html("Masquer le JSON");
        } else {
            json_container.style.display = "none";
            $("#showjson-button").html("Afficher le JSON");
        }
    }
    format_array(array) {
        return array;
    }
    async ask_args_for_difficulty(text_arg) {
        return new Promise((resolve) => {
            let html = '<div class="flex justify-center items-center '
                + 'gap-4 p-4">';
            for(var i = 1; i <= 5; i ++) {
                html += '<div class="circle w-12 h-12 flex items-center '
                    + 'justify-center rounded-full border-2 cursor-pointer '
                    + 'text-black border-gray-300" '
                    + 'data-value="' + i + '">' + i + '</div>';
            }
            html += '</div>'
                + '<label class="flex items-center justify-center gap-2 mt-2">'
                + '<input type="checkbox" class="form-checkbox '
                + 'h-5 w-5 text-blue-600" id="swal-checkbox">'
                + 'Inverser la sélection ?</label>';

            const onyes = function (evt) {
                const selected = Array.from(
                    document.querySelectorAll(".circle.bg-blue-500"))
                      .map(el => parseInt(el.getAttribute("data-value")));
                const isChecked = document.getElementById("swal-checkbox").
                      checked;
                if(selected.length > 0) {
                    resolve({ value: selected, rev: isChecked });
                } else {
                    evt.cancel = true;
                    return;
                }
            };
            const onno = function() {
                resolve(null);
            }
            alertify.webamc_dialog(text_arg, html, onyes, onno);

            // attach events after display
            let selectedValues = [];
            const circles = document.querySelectorAll(".circle");
            circles.forEach(circle => {
                circle.addEventListener("click", function () {
                    const value = this.getAttribute("data-value");
                    this.classList.toggle("bg-blue-500");
                    this.classList.toggle("border-blue-500");
                    if(selectedValues.includes(value)) {
                        selectedValues = selectedValues.filter(
                            v => v !== value
                        );
                    } else {
                        selectedValues.push(value);
                    }
                });
            });
        });
    }
    async ask_args_for_tag(text_arg) {
        return new Promise(async (resolve) => {
            const html = `<div id="tags"></div>
              <label class="flex items-center justify-center
                gap-2 mt-3">
            <input type="checkbox" id="swal-checkbox" class="rounded">
              Inverser la sélection ?
            </label>`;
            const onyes = function(evt) {
                const tags = [];
                Object.entries(tag_table.tags).forEach(
                    function ([tag_id, tag]) {
                        tags.push(tag['tag_name']);
                    }
                );
                if(tags.length > 0) {
                    const data = {
                        'value': tags,
                        'rev': $('#swal-checkbox').prop('checked')
                    };
                    resolve(data);
                }
            };
            const onno = function(evt) {
                resolve(null);
            };
            alertify.webamc_dialog(text_arg, html, onyes, onno);
            const tag_table = new TagTable('tags', {}, true, null, true, null);
        });
    }
    async ask_args_for_sort(text_arg) {
        return new Promise((resolve) => {
            let selectedValue = null;
            let html = `
               <div class="flex gap-4 p-4 justify-center items-center">
                 <div class="rectangle w-24 h-12 flex items-center
                     justify-center rounded-lg border-2 cursor-pointer
                     text-black border-gray-300"
                   data-value="difficulty">Difficulté</div>
                 <div class="rectangle w-24 h-12 flex items-center
                     justify-center rounded-lg border-2 cursor-pointer
                     text-black border-gray-300"
                   data-value="code">Code</div>
               </div>
               <label class="flex items-center justify-center gap-2 mt-2">
                   <input type="checkbox" id="swal-checkbox"
                     class="form-checkbox h-5 w-5 text-blue-600">
                   Inverser la sélection ?
               </label>`;
            alertify.webamc_dialog(
                text_arg, html,
                function(evt) {
                    const isChecked = document.getElementById("swal-checkbox")
                          .checked;
                    if(!selectedValue) {
                        evt.cancel = true;
                        return;
                    }
                    resolve({ value: selectedValue, rev: isChecked });
                },
                function() { resolve(false); }
            );
            const rectangles = document.querySelectorAll(".rectangle");
            rectangles.forEach(rectangle => {
                rectangle.addEventListener("click", function () {
                    rectangles.forEach(
                        r => r.classList.remove(
                            "bg-blue-500", "border-blue-500", "text-white"));
                    this.classList.add(
                        "bg-blue-500", "border-blue-500", "text-white");
                    selectedValue = this.getAttribute("data-value");
                });
            });
        });
    }
    async ask_args_for_head(text) {
        return new Promise((resolve) => {
            const html = '<input type="number" id="head"/>';
            const onyes = function(evt) {
                const val = $('#head').val();
                if(!val) {
                    evt.cancel = true;
                } else {
                    resolve(val);
                }
            };
            const onno = function(evt) {
                resolve(null);
            };
            alertify.webamc_dialog(text, html, onyes, onno);
        });
    }
    async add_filter(op) {
        let arg_selected = false;
        let rev_asked = false;
        let args = null;
        switch (op) {
        case 'head':
            args = await this.ask_args_for_head(
                'Combien de questions souhaitez vous ? '
            );
            if(args == null) {
                return;
            }
            arg_selected = args;
            break;
        case 'difficulty':
            args = await this.ask_args_for_difficulty(
                'Quel est le niveau de difficulté ? '
            );
            if(args == null) {
                return;
            }
            arg_selected = args['value'];
            if(arg_selected) {
                rev_asked = args['rev'];
            }
            break; 
        case 'tag':
            args = await this.ask_args_for_tag('Choisir les tags disponibles');
            if(args == null) {
                return;
            }
            arg_selected = args['value'];
            if(arg_selected) {
                rev_asked = args['rev'];
            }
            break; 
        case 'sort':
            args = await this.ask_args_for_sort('Trier par');
            if(args == null) {
                return;
            }
            arg_selected = args['value'];
            if(arg_selected) {
                rev_asked = args['rev'];
            }
            break;
        default:
            arg_selected = false;
            break;
        }
        if(arg_selected == null) {
            return;
        }
        this.stack_filters();
        let new_filter = new Filter(
            this.ctr ++,
            'null',
            op,
            this,
            arg_selected,
            rev_asked == false ? null : true
        );
        new_filter.arg = arg_selected;
        this.filters.push(new_filter);
        this.update_html();
    }
    get_filter_by_id(filters, id) {
        for(let filter of filters) {
            if(filter.id == id) {
                return filter;
            }
            let found = this.get_filter_by_id(filter.content, id);
            if(found != null) {
                return found;
            }
        }
        return null;
    }
    remove_filter_by_id(id, parentid) {
        let removed_filter = null;
        if(parentid == 'null' || parentid == null) {
            let index = this.filters.findIndex(f => f.id == id);
            if(index != -1) {
                this.stack_filters();
                removed_filter = this.filters.splice(index, 1)[0];
            }
        } else {
            let parent_filter = this.get_filter_by_id(this.filters, parentid);
            if(parent_filter != 'null' || parent_filter != null) {
                let index = parent_filter.content.findIndex(f => f.id == id);
                if(index != -1) {
                    this.stack_filters();
                    removed_filter = parent_filter.content.splice(index, 1)[0];
                }
            }
        }
        return removed_filter;
    }
    remove_only_filter(id, parentid) {
        let removed_filter = null;
        let filter = this.get_filter_by_id(this.filters, id);
        let childs = filter.content.slice();
        for (let f of childs){
            f.parentid = parentid;
        }
        if(parentid == null || parentid == 'null') {
            this.filters = this.filters.concat(childs);
            let index = this.filters.findIndex(f => f.id == id);
            if(index != -1){
                this.stack_filters();
                removed_filter = this.filters.splice(index, 1)[0];
            }
        } else {
            let parent_filter = this.get_filter_by_id(this.filters, parentid);
            parent_filter.content = parent_filter.content.concat(childs);
            let index = parent_filter.content.findIndex(f => f.id == id);
            if(index != -1) {
                this.stack_filters();
                removed_filter = parent_filter.content.splice(index, 1)[0];
            }
        }
        return removed_filter;
    }
    update_html() {
        /*
        let download_button = document.getElementById('download_button');
        let save_button = document.getElementById('save_button');
        if(this.filters.length > 0) {
            if(this.filters.length > 1) {
                document
                    .getElementById('jsonOutput')
                    .textContent = JSON.stringify(
                        this.filters.map(f=>f.get_json()), null, 2
                    );
            } else {
                document
                    .getElementById('jsonOutput')
                    .textContent = JSON.stringify(
                        this.filters[0].get_json(), null, 2
                    );
            }
            download_button.disabled = false;
            save_button.disabled = false;
        } else {
            download_button.disabled = true;
            save_button.disabled = true;
            document.getElementById('jsonOutput').textContent = '';
            }
            */
        let container = this.filters_container();
        container.html('');
        this.filters.forEach(
            function (f) {
                container.append(f.create_html());
            }
        );
    }
    reset_filters() {
        this.stack_filters();
        this.filters = [];
        this.ctr = 0;
        this.update_html();
    }
    download_json() {
        const jsonContent = JSON.stringify(
            this.filters.map(f => f.get_json()), null, 2
        );
        const blob = new Blob([jsonContent], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = '_pack.json';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    import_json(json_object) {
        this.stack_filters();
        this.filters = [];
        idcounter = 0;
        for(let filter of json_object) {
            this.filters.push(this.get_filter_from_json(filter, null));
        }
        this.update_html();
    }
    add_imported_json(json_object) {
        this.stack_filters();
        for(let filter of json_object) {
            this.filters.push(this.get_filter_from_json(filter, null));
        }
        this.update_html();
    }
    get_filter_from_json(json_filter, parent_filter_id) {
        let op = json_filter.op;
        let arg = null;
        let rev = null;
        let content = null;
        if(json_filter.hasOwnProperty('arg')) {
            arg = json_filter.arg;
        }
        if(json_filter.hasOwnProperty('rev')) {
            rev = json_filter.rev;
        }
        if(json_filter.hasOwnProperty('content')) {
            content = json_filter.content;
        }
        this.ctr ++;
        let filter = new Filter(
            this.ctr,
            parent_filter_id,
            op,
            this,
            arg,
            rev
        );
        if(content != null) {
            content = Array.isArray(content) ? content : [content];
            for(jf of content) {
                let f = this.get_filter_from_json(jf, filter.id);
                filter.content.push(f);
            }
        }
        return filter;
    }
    async save() {
        let html = `
    <form id="qcm-form" method='POST'>
      <div style="margin-bottom: 15px;">
        <input type="text" id="title" name="title"
          style="width:100%; padding:8px; border:1px solid #ccc;
            border-radius:4px;"
          placeholder="Entrez le titre du QCM" required>
      </div>
      <div>
        <input type="text" id="code" name="code"
          style="width:100%; padding:8px; border:1px solid #ccc;
              border-radius:4px;" placeholder="Entrez le code du QCM" required>
      </div>
    </form>`;

        alertify.webamc_dialog(
            'Nouveau QCM', html, 
            function(evt) {
                const title = document.getElementById("title").value;
                const code = document.getElementById("code").value;
                const json = document.getElementById("jsonOutput").textContent;
                if(!title || !code) {
                    evt.cancel = true; 
                    return;
                }
                const pack = JSON.parse(json);
                const form_data = { title, code, pack };
                const success = function (_) {
                    this.reset_filters();
                    base_report_infos(['MCQ loaded']); 
                    alertify.success("Sauvegardé avec succès !"); 
                };
                xhr_post_oper(
                    Constants.path_item_oper_save_pack, form_data, success);
            },
            function() {}
        );
    }
    stack_filters() {
        if(this.filters != []) {
            if(this.filters_save == null) {
                this.filters_save = []
            } else {
                let filters_copy = this.copy_filters(
                    this.filters.slice()
                );
                this.filters_save.push(filters_copy);
            }
        } else {
            this.filters_save = null;
        }
    }
    copy_filters(filters) {
        for (let f of filters){
            f.content = f.content.slice();
            this.copy_filters(f.content);
        }
        return filters;
    }
    filters_container_id() {
        return this.id + '-filters';
    }
    button_id(btn) {
        return this.id + '-button-' + btn;
    }
    filters_container() {
        return $('#' + this.filters_container_id());
    }
    button(btn) {
        return $('#' + this.button_id(btn));
    }
    constructor(div_container_id, id) {
        let html = '';
        const _this = this;
        this.id = id;
        this.filters = [];
        this.ctr = 0;
        this.filters_save = [];
        this.div_container = $('#' + div_container_id);
        this.div_container.html(this.html());
        /*
        let download_button = document.getElementById('download_button');
        download_button.disabled = true;
        let save_button = document.getElementById('save_button');
        save_button.disabled = true;
        let json_container = document.getElementById('jsonOutput');
        json_container.style.display = 'none';
        document
            .getElementById('save_button')
            .addEventListener('click', async function(event){
                await this.save();
            });

        document
            .getElementById('import_button')
            .addEventListener('change', function(event) {
                const file = event.target.files[0];
                if(!file) return;
                const reader = new FileReader();
                reader.onload = function(event) {
                    try {
                        const jsonData = JSON.parse(event.target.result);
                        this.import_json(jsonData);
                    } catch (error) {
                        console.error(
                            'Erreur lors du parsing du JSON :', error);
                    }
                };
                reader.readAsText(file);
            });
        document
            .getElementById('add_import_button')
            .addEventListener('change', function(event) {
                const file = event.target.files[0];
                if(!file) {
                    return;
                }
                const reader = new FileReader();
                reader.onload = function(event) {
                    try {
                        const jsonData = JSON.parse(event.target.result);
                        this.add_imported_json(jsonData);
                    } catch (error) {
                        console.error(
                            'Erreur lors du parsing du JSON :', error);
                    }
                };
                reader.readAsText(file);
                });
        */
        this.filters_container().on(
            'ondragover',
            function (evt) {
                e.preventDefault()
            }
        );
        this.filters_container().on(
            'ondrop',
            function (evt) {
                evt.stopPropagation();
                evt.preventDefault();
                let target_id = evt.dataTransfer.getData('id');
                let target_parentid = evt.dataTransfer.getData('parentid');
                if(target_parentid != 'null' || target_parentid == null) {
                    let target_filter = this.remove_filter_by_id(
                        target_id, target_parentid
                    );
                    target_filter.parentid = null;
                    filters.push(target_filter);
                    this.update_html();
                }
            }
        );
        for (const [filter, _] of Object.entries(pack_filters)) {
            this.button(filter).on(
                'click',
                function (evt) {
                    _this.add_filter(filter);
                }
            );
        }
    }
    html() {
        let result = '<div class_="flex flex-wrap gap-2 mb-4">'
        for (const [filter, data] of Object.entries(pack_filters)) {
            result += `
             <button
               id="${this.button_id(filter)}"
               class="px-4 py-2 rounded ${data['class']}"
               title="${data['title']}">
               ${filter}
             </button>`
            ;
        }
        result += `
           </div>
           <div id="${this.filters_container_id()}" draggable="true"
             class="min-h-[100px] p-4 bg-gray-200 rounded mb-4">
           </div>`
        ;
        return result;
    }
}


const pack_filters = {
    'all': {
        'class': 'bg-blue-500',
        'title': 'Toutes les questions'
    },
    'shuf': {
        'class': 'bg-[#00ff9B]',
        'title': 'Mélanger les questions'
    },
    'head': {
        'class': 'bg-[#ffc300]',
        'title': 'Choisir un certain nombre de questions'
    },
    'difficulty': {
        'class': 'bg-[#ff5733]',
        'title': 'Choisir la difficulté'
    },
    'sort': {
        'class': 'bg-[#ff0080]',
        'title': 'Trier les questions'
    },
    'tag': {
        'class': 'bg-blue-700',
        'title': 'Choisir les tags des questions'
    }
};
