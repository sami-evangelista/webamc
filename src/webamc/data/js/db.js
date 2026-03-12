const db_xhr = function (db_args, val) {
    const db_where = {
        'op': '=',
        'col': db_args['pkey_name'],
        'val': db_args['id']
    };
    const db_values = {};
    db_values[db_args['col_name']] = val;
    xhr_db_update(db_args['tbl_name'], [ db_where ], db_values);
}


const db_checkbox = function (input_id, init_val, disabled, db_args) {
    $('#' + input_id).prop('checked', init_val);
    $('#' + input_id).attr('disabled', disabled);
    if(db_args != null) {
        const update_fun = function () {
            db_xhr(db_args, $('#' + input_id).is(':checked'));
        };
        $('#' + input_id).change(update_fun);
    }
}


const db_color = function (input_id, init_val, disabled, db_args) {
    $('#' + input_id).attr('value', init_val);
    $('#' + input_id).attr('disabled', disabled);
    if(db_args != null) {
        const update_fun = function () {
            db_xhr(db_args, $('#' + input_id).val());
        };
        $('#' + input_id).change(update_fun);
    }
}


const db_col_toggle = function (db_id, db_col, db_id_col) {
    const div_id = 'div-' + db_col + '-' + db_id;
    $('#' + div_id + '-link').toggle();
    $('#' + div_id + '-input').toggle();
}


const db_col_show_input = function (db_id, db_col, db_id_col) {
    const div_id = 'div-' + db_col + '-' + db_id;
    const url = Constants.path_db_page_input
          + '?id_=' + db_id
          + '&col=' + db_col
          + '&col_id=' + db_id_col;
    const input_received = function (result) {
        $('#' + div_id + '-input').html(result);
        db_col_toggle(db_id, db_col, db_id_col);
    };
    xhr_get(url, input_received);
}


const db_col_send_update = function (db_tbl, db_id, db_col, db_id_col) {
    const val = $('#update-' + db_id + '-' + db_col).val();
    const db_where = [{'col': db_id_col, 'op': '=', 'val': db_id}];
    const db_values = {};
    db_values[db_col] = val;
    const success = function(result) {
        const val_id = 'div-' + db_col + '-' + db_id + '-val';
        $('#' + val_id).html(result.result.readable_values[0][db_col]);
        db_col_toggle(db_id, db_col, db_id_col);
    }
    xhr_db_update(db_tbl, db_where, db_values, success);
}
