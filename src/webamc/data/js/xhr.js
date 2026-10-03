const xhr_error = function (xhr) {
    base_report_errors(['Error ' + xhr.status]);
}


const xhr_get = function (url, success) {
    if(url == null) {
	console.error('No url specified !');
	return;
    }
    const settings = {
        url: url,
        type: 'GET',
        success: success,
	error: xhr_error
    };
    $.ajax(url, settings);
}


const xhr_post = function (
    url,
    success,
    data,
    dataType='json',  /* type of data expected from the server */
    complete=null
) {
    if(url == null) {
	console.error('No url specified !');
	return;
    }
    const settings = {
        url: url,
        type: 'POST',
        success: success,
	error: xhr_error,
        complete: complete,
        dataType: dataType,  /* type of data expected from the server */
        data: JSON.stringify(data),  /* data sent */
        contentType: 'application/json; charset=utf-8'  /* type of data sent */
    };
    $.ajax(url, settings);
}


const xhr_post_oper = function (url, data, success = null) {
    const success_wrap = function (result) {
        if(!result.success) {
            base_report_errors(result.msgs);
        } else if(success == null) {
                base_report_infos(result.msgs);
        } else {
            success(result);
        }
    };
    xhr_post(url, success_wrap, data);
}


const xhr_db = function (data, success = null) {
    xhr_post_oper(Constants.path_db_oper_query, data, success);
}


const xhr_db_delete = function (db_tbl, db_where, success = null) {
    const data = {
        'type': 'delete',
        'table': db_tbl,
        'where': db_where
    };
    xhr_db(data, success);
}


const xhr_db_insert = function (db_tbl, db_values, success = null) {
    const data = {
        'type': 'insert',
        'table': db_tbl,
        'values': db_values
    };
    xhr_db(data, success);
}


const xhr_db_select = function (db_tbl, db_where, success = null) {
    const data = {
        'type': 'select',
        'table': db_tbl,
        'where': db_where
    };
    xhr_db(data, success);
}


const xhr_db_update = function (
    db_tbl, db_where, db_values, success = null
) {
    const data = {
        'type': 'update',
        'table': db_tbl,
        'where': db_where,
        'values': db_values
    };
    xhr_db(data, success);
}
