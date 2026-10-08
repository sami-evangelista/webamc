class TagTable {

    constructor(
        container_id,
        tags,
        add_btn,
        add_fun,
        del_btn,
        del_fun
    ) {
        this.container_id = container_id;
        this.add_btn = add_btn;
        this.add_fun = add_fun;
        this.del_btn = del_btn;
        this.del_fun = del_fun;
        this.tags = {};
        for(const tag_id in tags) {
            this.tags[tag_id] = tags[tag_id];
        }
	this.html();
    }

    get_tag_ids() {
        let result = [];
        for(const tag_id in this.tags) {
            result.push(Number(tag_id));
        }
        return result;
    }

    get_tag_names() {
        let result = [];
        Object.entries(tag_table.tags).forEach(
            function ([tag_id, tag]) {
                result.push(tag['tag_name']);
            }
        );
        return result;
    }

    datalist_id() {
        return this.container_id + '-datalist';
    }

    tag_element_id(tag_id) {
        return this.container_id + "-tag-" + tag_id;
    }

    a_add_id() {
        return this.container_id + '-add';
    }

    input_id() {
        return this.container_id + '-input';
    }

    del_tag(tag_id) {
        if(tag_id in this.tags) {
            if(this.del_fun != null) {
                const _this = this;
                const del = function () {
                    delete _this.tags[tag_id];
                    _this.html();
                }
                this.del_fun(tag_id, del);
            } else {
                delete this.tags[tag_id];
                this.html();
            }
        }
    }

    add_tag() {
        const input_id = this.input_id();
        const  _this = this;
        const success = function (result) {
            for(const value of result.result.values) {
                const go = function () {
                    _this.tags[value.tag_id] = value;
                    $('#' + input_id).val('');
                    $('#' + input_id).focus();
                    _this.html();
                }
                if(!(value.tag_id in _this.tags)) {
                    if(_this.add_fun == null) {
                        go();
                    } else {
                        _this.add_fun(value['tag_id'], go);
                    }
                }
            }
        };
        const where = {
            'col': 'tag_name',
            'op': '=',
            'val': $('#' + input_id).val()
        };
        xhr_db_select('tag', [ where ], success);
    }

    tag_element(tag_id, tag) {
        var result = '';
        var style = 'box-sizing: border-box;';
        result += '<div class="tag-name"';
        result += ' id="' + this.tag_element_id(tag_id) + '"';
        if(tag.tag_color != null) {
            style += 'background-color: ' + tag.tag_color + ';';
        }
        if(this.del_btn != null) {
            style += 'cursor: pointer;';
        }
        if(style != '') {
            result += ' style="' + style + '"';
        }
        result += '>' + base_escape_html(tag.tag_name) + '</div>';
        result += '';
        return result;
    }

    input_add() {
        var result = '<div>';
        result += '<input type="text" id="' + this.input_id() + '" ';
        result += 'list="' + this.datalist_id() + '">';
        result += '</div>';
        return result;
    }

    empty_data_list () {
        $('#' + this.datalist_id()).empty();
    }

    input_keypressed () {
        const _this = this;
        const val = $('#' + this.input_id()).val();
        this.empty_data_list();
        if(val.length < 3) {
            return;
        }
        const dl = $('#' + this.datalist_id());
        const where = {
            'col': 'tag_name',
            'op': 'like',
            'val': '%' + val + '%'
        };
        this.empty_data_list();
        const success = function (result) {
            for(const val of result.result.values) {
                if(!(val.tag_id in _this.tags)) {
                    const opt = '<option value="' + val.tag_name + '">';
                    dl.append(opt);
                }
            }
        };
        xhr_db_select('tag', [ where ], success);
    }
    
    html() {
        var html = '<div>';
        if(this.add_btn) {
            html += this.input_add();
        }
        for(const tag_id in this.tags) {
            html += this.tag_element(tag_id, this.tags[tag_id]);
        }
        html += '</div>';
        html += '<datalist id="' + this.datalist_id() + '"></datalist>';
        $('#' + this.container_id).html(html);
        
        if(this.del_btn) {
            for(const tag_id in this.tags) {
                const _this = this;
                $('#' + this.tag_element_id(tag_id)).click(function () {
                    _this.del_tag(tag_id);
                });
            }
        }
        if(this.add_btn) {
            const _this = this;
            $('#' + this.a_add_id()).click(function () {
                _this.add_tag();
            });
            $('#' + this.input_id()).keypress(function () {
                _this.input_keypressed();
            });
            $('#' + this.input_id()).on('keyup', function (e) {
                if(e.key == "Enter") {
                    _this.add_tag();
                }
            });
        }
    }
}
