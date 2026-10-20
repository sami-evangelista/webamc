var item_groups_loaded = new Set();
var item_db_items_loaded = new Set();
var item_db_packs = {};
var item_db_roots = new Set();
var item_db_table_filter_tag;


const item_add = function () {
    const success = function (response) {
        const url = Constants.path_item_page_main
              + "?sub_page=item_database"
              + "&itm_id=" + response.result['itm_id']
        ;
        base_relocate(url);
    };
    const data = base_input_values('#table-add-item');
    xhr_post_oper(Constants.path_item_oper_add, data, success);
}


const item_load_grp = function (db_grp_id) {
    const div_body = $('#div-group-body-' + db_grp_id);
    if(item_groups_loaded.has(db_grp_id)) {
        div_body.fadeToggle();
    } else {
        const success = function (result) {
            div_body.html(result).toggle().fadeIn();
            item_groups_loaded.add(db_grp_id);
        };
        const path = Constants.path_item_page_group + '?grp_id=' + db_grp_id;
        xhr_get(path, success);
    }
}


const item_db_on_children_update = function (db_itm_id) {
    const path = Constants.path_item_page_database_body
          + '?itm_id=' + db_itm_id
          + '&iti_num=1'
    ;
    const success = function (response) {
        $('#div-item-body-' + db_itm_id).html(response);
    };
    xhr_get(path, success);
}


const item_db_detach = function (db_itm_id, db_itm_id_parent) {
    const go = function () {
        const db_where = [
            {'op': '=', 'col': 'itr_parent', 'val': db_itm_id_parent},
            {'op': '=', 'col': 'itr_child', 'val': db_itm_id},
        ];
        const success = function() {
            item_db_on_children_update(db_itm_id_parent);
        };
        xhr_db_delete('item_relation', db_where, success);
    };
    base_ask_confirmation(Lang['qst_confirmation_item_detach'], go);
}


const item_db_delete = function (db_itm_id, db_itm_id_parent) {
    let success;
    if(db_itm_id_parent != null) {
        success = function() { item_db_on_children_update(db_itm_id_parent); };
    } else {
        success = function() { item_db_filter(); };
    }
    const go = function () {
        const db_where = {
            'op': '=',
            'col': 'itm_id',
            'val': db_itm_id
        };
        xhr_db_delete('item', [db_where], success);
    };
    base_ask_confirmation(Lang['qst_confirmation_item_deletion'], go);
}


const item_db_delete_recursively = function (db_itm_id, db_itm_id_parent) {
    let success;
    if(db_itm_id_parent != null) {
        success = function() { item_db_on_children_update(db_itm_id_parent); };
    } else {
        success = function() { item_db_filter(); };
    }
    if(db_itm_id_parent != null) {
        success = function() { item_db_on_children_update(db_itm_id_parent); };
    }
    const go = function () {
        const data = {
            'itm_id': db_itm_id
        };
        xhr_post(Constants.path_item_oper_recursive_deletion, success, data);
    };
    const txt = Lang['qst_confirmation_item_recursive_deletion'];
    base_ask_confirmation(txt, go);
}


const item_db_filters_init = function (div_id) {
    item_db_table_filter_tag = new TagTable(
        div_id, {}, true, null, true, null
    );
}


const item_db_code_click = function (db_itm_id, is_root, db_iti_num) {
    const div_body = $('#div-item-body-' + db_itm_id);
    const target_instance = db_iti_num || 1;
    const is_dropdown_change = (db_iti_num !== null);

    /* if we click on a root item we have to hide all other roots to
     * avoid duplicate items in the page referenced through different
     * roots */
    if(is_root) {
        if(item_db_items_loaded.has(db_itm_id)) {
            item_db_filter();
        } else {
            /* hide all other roots */
            const success = function (result) {
                item_db_items_loaded = new Set();
	        $('#div-item-list').html(result);
            };
            const url = Constants.path_item_page_database_list;
            const data = {'itm_id': db_itm_id, 'display_num_found': false};
            xhr_post(url, success, data, 'html');
        }
    } else {
        if(item_db_items_loaded.has(db_itm_id) && !is_dropdown_change) {
            div_body.fadeToggle();
        } else {
            const success = function (result) {
                div_body.html(result);
                if (!div_body.is(':visible')) {
                    div_body.hide().fadeIn();
                }
                item_db_items_loaded.add(db_itm_id);
            };
            const path = Constants.path_item_page_database_body
                  + '?itm_id=' + db_itm_id 
                  + '&iti_num=' + target_instance;
            xhr_get(path, success);
        }
    }
    return false;
};


const item_db_pack_load = function (pak_id, div_container_id, pak_spec) {
    const div_id = 'pack-' + pak_id;
    item_db_packs[pak_id] = new Pack(div_container_id, div_id, pak_spec);
}


const item_db_pack_update = function (pak_id) {
    const db_where = {
        'op': '=',
        'col': 'pak_id',
        'val': pak_id
    };
    const db_values = {
        'pak_spec': item_db_packs[pak_id].get_json()
    };
    xhr_db_update('pack', [db_where], db_values);
}


const item_db_init = function (db_itm_id, tags, grps, init_grps) {

    /* initialise the tag table */
    const table_tags_id = 'table-item-tags-' + db_itm_id;
    const add_tag_fun = function (db_tag_id, callback) {
        const values = { 'itg_tag': db_tag_id, 'itg_item': db_itm_id };
        xhr_db_insert('item_tag', values, callback);
    };
    const del_tag_fun = function (db_tag_id, callback) {
        const where = [
            { 'col': 'itg_tag',  'op': '=', 'val': Number(db_tag_id) },
            { 'col': 'itg_item', 'op': '=', 'val': Number(db_itm_id) }
        ];
        xhr_db_delete('item_tag', where, callback);
    };
    new TagTable(table_tags_id, tags, true, add_tag_fun, true, del_tag_fun);

    /* initialise the group table */
    const table_grps_id = 'table-mcq-grps-' + db_itm_id;
    if($('#' + table_grps_id).length > 0) {
        const add_grp_fun = function (db_grp_id, callback) {
            const values = { 'mgp_grp': db_grp_id, 'mgp_mcq': db_itm_id };
            xhr_db_insert('mcq_grp', values, callback);
        };
        const del_grp_fun = function (db_grp_id, callback) {
            const where = [
                { 'col': 'mgp_grp', 'op': '=', 'val': Number(db_grp_id) },
                { 'col': 'mgp_mcq', 'op': '=', 'val': Number(db_itm_id) }
            ];
            xhr_db_delete('mcq_grp', where, callback);
        };
        new GrpTable(
            table_grps_id, grps, init_grps,
            true, add_grp_fun, true, del_grp_fun
        );
    }
}


const item_db_add_child = function (db_itm_id) {
    const select_id = 'select-add-child-' + db_itm_id;
    const data = {
        'itr_parent': db_itm_id,
        'itr_child': base_input_value(select_id)
    };
    if(data['itr_child'] == null) {
        return;
    }
    const success = function () {
        item_db_on_children_update(db_itm_id);
    };
    xhr_post_oper(Constants.path_item_oper_add_child, data, success);
}


const item_db_filter = function (db_itm_id = null) {
    const success = function (result) {
        item_db_items_loaded = new Set();
	$('#div-item-list').html(result);
    };
    const url = Constants.path_item_page_database_list;
    const data = base_input_values('#table-item-filters');
    data['itm_id'] = db_itm_id;
    data['itm_type'] = $('#itm_type').val();
    data['itm_tags'] = item_db_table_filter_tag.get_tag_ids();
    xhr_post(url, success, data, 'html');
};


const item_db_move = function (db_itm_id, db_itm_id_parent, move) {
    const success = function () {
        item_db_on_children_update(db_itm_id_parent);
    };
    const data = {
        'itr_child': db_itm_id,
        'itr_parent': db_itm_id_parent,
        'move': move
    };
    xhr_post_oper(Constants.path_item_oper_move_child, data, success);
}
