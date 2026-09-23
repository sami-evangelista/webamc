var item_table_filter_tag;
var item_groups_loaded = new Set();
var item_admin_items_loaded = new Set();


const item_delete = function (itm_id) {{
    const go = function () {
        const where = [{
            'op': '=',
            'col': 'itm_id',
            'val': itm_id
        }];
        xhr_db_delete('item', where, function (_) { item_filter() });
    };
    const question = Lang['qst_item_deletion_confirmation'];
    base_ask_confirmation(question, go);
}};


const item_filter = function (itm_id = null) {
    const success = function (result) {
        item_admin_items_loaded = new Set();
	$('#div-item-list').html(result);
    };
    const url = Constants.path_item_page_database_list;
    const data = base_input_values('#table-item-filters');
    data['itm_id'] = itm_id;
    data['itm_type'] = $('#itm_type').val();
    data['itm_tags'] = Object.keys(item_table_filter_tag.tags);
    xhr_post(url, success, data, 'html');
};


const item_filters_init = function (div_id) {
    item_table_filter_tag = new TagTable(div_id, {}, true, null, true, null);
}


const item_load_grp = function (db_grp_id) {
    const div_body = $('#div-group-body-' + db_grp_id)
    if(!item_groups_loaded.has(db_grp_id)) {
        const success = function (result) {
            div_body.html(result).toggle().fadeIn();
            item_groups_loaded.add(db_grp_id);
        };
        const path = Constants.path_item_page_group + '?grp_id=' + db_grp_id;
        xhr_get(path, success);
    } else {
        div_body.fadeToggle();
    }
}

const item_admin_code_click = function (db_itm_id, iti_num = null) {
    const div_body = $('#div-item-body-' + db_itm_id);
    const target_instance = iti_num || 1;
    const is_dropdown_change = (iti_num !== null);
    if(item_admin_items_loaded.has(db_itm_id) && !is_dropdown_change) {
        div_body.fadeToggle();
    } else {
        const success = function (result) {
            div_body.html(result);
            if (!div_body.is(':visible')) {
                div_body.hide().fadeIn();
            }
            item_admin_items_loaded.add(db_itm_id);
        };
        const path = Constants.path_item_page_database_body
              + '?itm_id=' + db_itm_id 
              + '&iti_num=' + target_instance;
        xhr_get(path, success);
    }
    return false;
};


const item_init_admin = function (db_itm_id, tags, grps, init_grps) {

    /* initialise the tag table */
    const table_tags_id = 'table-item-tags-' + db_itm_id;
    const add_tag_fun = function (db_tag_id, callback) {
        const values = { 'itg_tag': db_tag_id, 'itg_item': db_itm_id };
        xhr_db_insert('item_tag', values, callback);
    };
    const del_tag_fun = function (db_tag_id, callback) {
        const where = [
            { 'col': 'itg_tag',  'op': '=', 'val': db_tag_id },
            { 'col': 'itg_item', 'op': '=', 'val': db_itm_id }
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
                { 'col': 'mgp_grp', 'op': '=', 'val': db_grp_id },
                { 'col': 'mgp_mcq', 'op': '=', 'val': db_itm_id }
            ];
            xhr_db_delete('mcq_grp', where, callback);
        };
        new GrpTable(
            table_grps_id, grps, init_grps,
            true, add_grp_fun, true, del_grp_fun
        );
    }
}


const item_update_pack = function (pak_id, pak_spec) {
    const db_where = {
        'op': '=',
        'col': 'pak_id',
        'val': pak_id
    };
    const db_values = {
        'pak_spec': pak_spec
    };
    xhr_db_update('pack', [db_where], db_values);
}
