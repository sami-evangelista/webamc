var project_computing = false;
var project_wait_modal = null;
var project_groups = null;
var project_usr_groups = {};
var project_status = {};


const project_start_computation = function () {
    project_computing = true;
    project_wait_modal = alertify
        .alert(Lang['info_please_wait'])
        .set('modal', true)
        .set('closable', false)
        .set('frameless', true);
    project_wait_modal.elements.dialog.classList.add('please_wait');
}


const project_end_computation = function () {
    project_computing = false
    if(project_wait_modal) {
        project_wait_modal.close();
        project_wait_modal = null;
    }
}


const project_highlight_errors = function (ids) {
    for(const id of ids) {
        $('#' + id).addClass('error');
    }
    setTimeout(
        function() {
            for(const id of ids) {
                $('#' + id).removeClass('error');
            }
        },
        base_tooltip_time * 1000
    );
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
        } else if(dep_type == 'data') {
            msgs.push(Lang['err_data_required']);
            id = dep;
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
        'action_params': {},
        'project_code': $('#new_project_code').val()
    };
    const success = function(_) {
        const url = Constants.path_project_page_main;
        base_relocate(url);
    };
    xhr_post_oper(Constants.path_project_oper_action, data, success);
}


const project_init = function () {
    const project_code = $('#project_code').val();
    if(project_code == '' || project_code == null) {
        return;
    }
    const url = Constants.path_project_oper_get_status;
    const success = function(response) {
        project_status = response.result;
        const data = project_status.data;
        const done = project_status.done;
        const doable = project_status.doable;
        const files = project_status.files;
        const groups = data['groups'] ? data['groups'] : [];

        // data
	for(const [key, val] of Object.entries(data)) {
            $('#' + key).val(val);
        }
        project_groups = new GrpTable(
            'div-grps', project_usr_groups, groups, true, null, true, null
        );

        // files
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
        for(const [act, [d, msgs]] of Object.entries(doable)) {
            const img = $('#img-action-' + act);
            if(d) {
                img.removeClass('warning');
            } else {
                img.addClass('warning');
            }
        }
    };
    const data = {
        'project_code': project_code
    };
    xhr_post(url, success, data);
}


const project_load_project = function () {
    const project_code = $('#project_code').val();
    const div_project = $('#div-project');
    if(project_code == '' || project_code == null) {
        div_project.html('');
    } else {
        const url = Constants.path_project_page_project;
        const success = function(html) { div_project.html(html); };
        const data = { 'project_code': project_code };
	xhr_post(url, success, data, 'html');
    }
}


const project_upload_action = function (action, file_id) {
    const file_content = $('#' + file_id).prop('files')[0];
    if(project_computing
       || !project_check_doable(action)
       || !file_content) {
        return;
    }
    const project_code = $('#project_code').val();
    const form_data = new FormData();
    const url = Constants.path_project_oper_upload;
    const success = function(response) {
        base_report(response.msgs, response.success);
        project_init();
    }
    project_start_computation();
    form_data.append('action', action);
    form_data.append('file_content', file_content);
    form_data.append('project_code', project_code);
    const query = {
        url: url,
        type: 'POST',
        data: form_data,
        processData: false,
        contentType: false,
	error: xhr_error,
	success: success,
        complete: project_end_computation
    };
    $.ajax(query);
}


const project_action = function (action, params = null) {
    if(project_computing || !project_check_doable(action)) {
        return;
    }
    const go  = function () {
        const url = Constants.path_project_oper_action;
        const data = {
            'action': action,
            'project_code': $('#project_code').val(),
            'action_params': {}
        };        
        const success = function(response) {
            base_report(response.msgs, response.success);
            if(action == 'delete') {
                const url = Constants.path_project_page_main;
                base_relocate(url);
            }
            if(action != 'associate_manual') {
                project_init();
            }
        };
        if(params != null) {
            for(const [key, val] of Object.entries(params)) {
                data['action_params'][key] = val;
            }
        }
        project_start_computation();
        xhr_post(url, success, data, 'json', project_end_computation);
    };
    const txt = 'qst_confirmation_project_' + action;
    if(txt in Lang && project_status.warning[action]) {
        base_ask_confirmation(Lang[txt], go);
    } else {
        go();
    }
}


const project_manual_association_open = function () {
    if(!project_check_doable('associate_manual_prepare')) {
        return;
    }
    const project_code = $('#project_code').val();
    const div_manual_association = $('#div-manual-association');
    if(project_code != '' && project_code != null) {
        const url = Constants.path_project_page_manual_association;
        const success = function(response) {
            base_report(response.msgs, response.success);
            if(response.success) {
	        div_manual_association.html(response.result);
                div_manual_association.toggle();
            }
        };
        const data = {
            'project_code': project_code,
            'action_params': base_input_values('#table-action-params')
        };
	xhr_post(url, success, data);
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
        'id': $('#assoc-' + student + '-' + copy).val()
    };
    project_action('associate_manual', params);
}


const project_submit_data = function () {
    const data = base_input_values('#table-action-data');
    const url = Constants.path_project_oper_set_data;
    const handle_response = function (response) {
        base_report(response.msgs, response.success);
        if(response.success) {
            project_init();
        } else {
            project_highlight_errors(response.result);
        }
    }
    delete data[project_groups.select_id()];
    data['code'] = $('#project_code').val();
    data['groups'] = project_groups.value;
    xhr_post(url, handle_response, data);
}
