const admin_delete_row = function (tbl_name, pkey_name, pkey_val) {
    const go = function () {
        const where = [{
            'op': '=',
            'col': pkey_name,
            'val': pkey_val
        }];
        const success = function (result) {
            location.reload();
        };
        xhr_db_delete(tbl_name, where, success);
    };
    base_ask_confirmation(Lang['qst_item_row_confirmation'], go);
};


const admin_new_row_btn_click = function () {
    $('#tr_new_row').fadeToggle(base_anim_delay);
};


const admin_add_row = function (db_tbl, db_cols) {
    var values = {};
    for(const [db_col_name, input_id] of Object.entries(db_cols)) {
        var input = $("#" + input_id);
        if(input.is(':checkbox')) {
            value = input.prop('checked');
        } else {
            value = input.val();
        }
        values[db_col_name] = value;
    }
    const success = function(_) {
        window.location.reload();
    };
    xhr_db_insert(db_tbl, values, success);
}


const admin_table_filter = function () {
    const success = function (result) {
	$('#div-table-body').html(result);
    };
    const url = Constants.path_admin_page_table;
    const data = {
        'tbl_id': $('#tbl').val(),
        'page_num': $('#page_num').val(),
        'filters': base_input_values('#table-filters')
    }
    xhr_post(url, success, data, 'html');
}


const admin_table_change = function () {
    const url = Constants.path_admin_page_main
          + '?sub_page=database'
          + '&tbl_id=' + $('#tbl').val();
    base_relocate(url);
}


const admin_table_navigate = function (move) {
    var val = parseInt($('#page_num').val());
    const pages = $('#page_num option').length;
    val += move;
    if(val <= 0) {
	val = pages;
    } else if(val > pages) {
	val = 1;
    }
    $('#page_num').val(val);
    admin_table_filter();
}
