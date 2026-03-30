// const xhr_error = function (xhr) {
//     base_report_errors(['Error ' + xhr.status]);
// }

const xhr_error = function (xhr) {
    let msg = 'Erreur ' + xhr.status;
    
    if (xhr.responseJSON && xhr.responseJSON.detail) {
        msg += ' : ' + xhr.responseJSON.detail;
    } 
    else if (xhr.responseText) {
        let tempDiv = document.createElement("div");
        tempDiv.innerHTML = xhr.responseText;
        
        // On récupère le texte avec les retours à la ligne respectés
        let rawText = tempDiv.innerText || tempDiv.textContent || "";
        
        // On découpe ligne par ligne et on enlève les lignes vides
        let textLines = rawText.split('\n').map(l => l.trim()).filter(l => l.length > 0);
        
        if (textLines.length > 0) {
            // La vraie erreur Python est presque toujours la DERNIÈRE ligne !
            let realError = textLines[textLines.length - 1];
            
            // Si jamais la dernière ligne c'est le bouton "Retour" de notre page rouge, on prend l'avant-dernière
            if (realError.toLowerCase().includes("retour") && textLines.length > 1) {
                realError = textLines[textLines.length - 2];
            }
            
            if (realError.length > 150) {
                realError = realError.substring(0, 150) + "...";
            }
            msg += ' : ' + realError;
        }
    }
    
    base_report_errors([msg]);
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
