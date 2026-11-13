var project_groups = null;
var project_usr_groups = {};
var project_status = {};


const project_highlight_errors = function (ids) {
    for(const id of ids) {
        $('#' + id).addClass('error');
    }
    const done = function() {
        for(const id of ids) {
            $('#' + id).removeClass('error');
        }
    };
    setTimeout(done, base_tooltip_time * 1000);
}


const project_check_doable = function (action) {
    if(project_status.doable[action][0]) {
        return true;
    }
    let msgs = [];
    let ids = [];
    for(const [dep_type, dep] of project_status.doable[action][1]) {
        let id;
        if(dep_type == 'file') {
            msgs.push(Lang['err_file_required']);
            id = 'label-file-' + dep;
        } else if(dep_type == 'action') {
            msgs.push(Lang['err_action_required']);
            id = 'label-action-' + dep;
        }
        ids.push(id);
    }
    project_highlight_errors(ids);
    base_report(msgs, false);
    return false;
}


const project_new = function () {
    const data = {
        'action': 'new',
        'prj_code': base_input_value('prj_code')
    };
    const success = function(result) {
        const args = {
            'prj_id': result.data['prj_id']
        };
        const url = base_encode_url(Constants.path_project_page_main, args);
        base_relocate(url);
    };
    xhr_post_oper(Constants.path_project_oper_action, data, success);
}


const project_init = function () {
    const prj_id = base_input_value('prj_id');
    if(prj_id == '' || prj_id == null) {
        return;
    }
    const url = Constants.path_project_oper_get_status;
    const success = function(response) {
        project_status = response.data;

        // files
        const files = project_status.files;
        for(const [f, fdata] of Object.entries(files)) {
            const exists = fdata['exists'];
            const img = $('#img-file-' + f);
            if(exists) {
                const js = 'base_relocate(\'' + fdata['uri'] + '\')';
                img.removeClass('warning')
                    .addClass('btn')
                    .attr('onclick', 'javascript:' + js)
                    .attr('title', fdata['name'] + ' - ' + fdata['date']);
            } else {
                img.removeClass('btn')
                    .addClass('warning')
                    .attr('onclick', '')
                    .attr('title', fdata['name']);
            }
        }

        // doable
        const doable = project_status.doable;
        for(const [act, [d, msgs]] of Object.entries(doable)) {
            const img = $('#img-action-' + act);
            if(d) {
                img.removeClass('warning');
            } else {
                img.addClass('warning');
            }
        }

        const done = project_status.done;
    };
    const data = {
        'prj_id': prj_id
    };
    xhr_post(url, success, data);
}


const project_load = function () {
    const prj_id = base_input_value('prj_id');
    const div_project = $('#div-project');
    if(prj_id == null) {
        div_project.html('');
    } else {
        const url = Constants.path_project_page_project;
        const success = function(html) {
            div_project.html(html);
        };
        const data = {
            'prj_id': prj_id
        };
	xhr_post(url, success, data, 'html');
    }
}


const project_upload_action = function (action, file_id) {
    const file_content = $('#' + file_id).prop('files')[0];
    if(!(project_check_doable(action) && file_content)) {
        return;
    }
    const comp = async function() {
        const prj_id = base_input_value('prj_id');
        const form_data = new FormData();
        const url = Constants.path_project_oper_upload;
        const success = function(response) {
            base_report(response.msgs, response.success);
            project_init();
        }
        form_data.append('action', action);
        form_data.append('file_content', file_content);
        form_data.append('prj_id', prj_id);
        const query = {
            url: url,
            type: 'POST',
            data: form_data,
	    success: success,
	    error: xhr_error,
            contentType: false,
            processData: false
        };
        await $.ajax(query);
    };
    base_launch_computation(comp);
}


const project_action = function (action, params = null) {
    if(!project_check_doable(action)) {
        return;
    }
    const comp = async function () {
        const url = Constants.path_project_oper_action;
        const data = {
            'prj_id': base_input_value('prj_id'),
            'action': action
        };        
        const success = function(response) {
            base_report(response.msgs, response.success);
            if(action == 'delete') {
                const url = Constants.path_project_page_main;
                base_relocate(url);
            }
            else if(action != 'associate_manual') {
                project_init();
            }
        };
        if(params != null) {
            for(const [key, val] of Object.entries(params)) {
                data[key] = val;
            }
        }
        const query = {
            url: url,
            type: 'POST',
            data: JSON.stringify(data),
            success: success,
	    error: xhr_error,
            contentType: 'application/json; charset=utf-8',
            dataType: 'json'
        };
        await $.ajax(query);
    };
    const go = function () {
        base_launch_computation(comp);
    };
    if(project_status.warning[action]) {
        const txt = 'project_qst_confirmation_' + action;
        base_ask_confirmation(Lang[txt], go);
    } else {
        go();
    }
}


const project_manual_association_open = function () {
    if(!project_check_doable('associate_manual_prepare')) {
        return;
    }
    const prj_id = base_input_value('prj_id');
    const div_manual_association = $('#div-manual-association');
    if(prj_id != null) {
        const success = function(response) {
	    div_manual_association.html(response);
            div_manual_association.toggle();
        };
        const args = {
            'prj_id': prj_id
        };
        const url = base_encode_url(
            Constants.path_project_page_manual_association,
            args
        );
	xhr_get(url, success);
    }
}


const project_manual_association_close = function () {
    const div_manual_association = $('#div-manual-association');
    div_manual_association.html('');
    div_manual_association.toggle();
}


const project_associate_manual = function (student, copy) {
    const params = {
        'student': student,
        'copy': copy,
        'id_': base_input_value('assoc-' + student + '-' + copy)
    };
    project_action('associate_manual', params);
}


const project_add_group = function(grp_id, callback) {
    const values = {
        'pgp_grp': grp_id,
        'pgp_project': base_input_value('prj_id')
    };
    xhr_db_insert('prj_grp', values, callback);
}


const project_del_group = function(grp_id, callback) {
    const where = [
        { 'col': 'pgp_grp', 'op': '=', 'val': Number(grp_id) },
        { 'col': 'pgp_project', 'op': '=', 'val': base_input_value('prj_id') }
    ];
    xhr_db_delete('prj_grp', where, callback);
}
