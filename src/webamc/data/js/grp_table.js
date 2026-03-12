class GrpTable {

    constructor(
        container_id,
        grps,
        init_grps,
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
        this.grps = {};
        for(const grp_id in grps) {
            this.grps[parseInt(grp_id)] = grps[grp_id];
        }
        this.value = [];
        for(const grp_id of init_grps) {
            this.value.push(parseInt(grp_id));
        };
	this.html();
    }

    select_id() {
        return this.container_id + '-select';
    }

    add_grp() {
        const _this = this;
        const grp_id = parseInt($('#' + this.select_id()).val());
        if(isNaN(grp_id) || this.value.includes(grp_id)) {
            return;
        }
        const go = function () {
            for(var i = 0; i < _this.value.length; i ++) {
                if(_this.grps[_this.value[i]] > _this.grps[grp_id]) {
                    break;
                }
            }
            _this.value.splice(i, 0, grp_id);
            _this.html();
        };
        if(this.add_fun == null) {
            go();
        } else {
            this.add_fun(grp_id, go);
        }
    }

    del_grp(grp_id) {
        const _this = this;
        const go = function () {
            const idx = _this.value.indexOf(grp_id);
            _this.value.splice(idx, 1);
            _this.html();
        };
        if(this.del_fun == null) {
            go();
        } else {
            const _this = this;
            this.del_fun(grp_id, go);
        }
    }

    select() {
        var result = '<select id="' + this.select_id() + '">';
        result += '<option value=""></option>';
        for(const [grp_id, grp_name] of Object.entries(this.grps)) {
            if(this.value.indexOf(parseInt(grp_id)) < 0) {
                result += '<option value="' + grp_id + '">';
                result += grp_name + '</option>';
            }
        }
        result += '</select>';
        return result;
    }

    group_element_id(grp_id) {
        return this.container_id + '-grp-' + grp_id;
    }
    
    html() {
        var html = '<div>';
        const _this = this;
        if(this.add_btn) {
            html += this.select();
        }
        for(const grp_id of this.value) {
            html += '<div class="group-name"';
            html += ' id="' + this.group_element_id(grp_id) + '"';
            if(this.del_btn) {
                html += ' style="cursor: pointer;"';
            }
            html += '>' + base_escape_html(this.grps[grp_id]) + '</div>';
        }
        html += '</div>';
        $('#' + this.container_id).html(html);
        if(this.add_btn) {
            $('#' + this.select_id()).click(function () {
                _this.add_grp();
            });
        }
        if(this.del_btn) {
            for(const grp_id of this.value) {
                $('#' + this.group_element_id(grp_id)).click(function () {
                    _this.del_grp(grp_id);
                });
            }
        }
    }
}
