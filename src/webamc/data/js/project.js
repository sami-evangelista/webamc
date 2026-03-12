var project_computing = false;
var project_wait_modal = null;


const project_start_computation = function () {
    project_computing = true;
    project_wait_modal = alertify
        .alert(Lang.info_please_wait)
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


const project_delete = function () {
    const go = function () {
        const data = {
            'action': 'delete',
            'action_params': {},
            'project_code': $('#project_code').val()
        };
        const success = function(_) {
            const url = Constants.path_project_page_main;
            base_relocate(url);
        };
        xhr_post_oper(Constants.path_project_oper_action, data, success);
    };
    base_ask_confirmation(Lang['qst_delete_project_confirmation'], go);
}


const project_init = function () {
    project_init_params();
    project_init_files();
    project_init_status();
}


const project_init_status = function () {
    const project_code = $('#project_code').val();
    if(project_code != '' && project_code != null) {
        const url = Constants.path_project_oper_get_status;
        const success = function(response) {
            const actions = response["result"]["status"]["actions"];
            const files = response["result"]["files"];
            for(const [a, s] of Object.entries(actions)) {
                const src = base_img_src(
                    s ? 'checkbox-checked' : 'checkbox-unchecked'
                );
                $('#img-status-' + a).attr('src', src);
            }
            for(const f of [
                'answer_sheets',
                'project_archive',
                'student_list'
            ]) {
                const src = base_img_src(
                    files.includes(f)
                        ? 'checkbox-checked' : 'checkbox-unchecked'
                );
                $('#img-status-' + f).attr('src', src);
            }
        };
        const data = {
            'project_code': project_code
        };
	xhr_post(url, success, data);
    }
}


const project_init_files = function () {
    const project_code = $('#project_code').val();
    const div_files = $('#div-files');
    if(project_code != '' && project_code != null) {
        const url = Constants.path_project_page_files;
        const success = function(html) {
	    div_files.html(html);
        };
        const data = {
            'project_code': project_code
        };
	xhr_post(url, success, data, 'html');
    }
}


const project_init_params = function () {
    const project_code = $('#project_code').val();
    if(project_code != '' && project_code != null) {
        const url = Constants.path_project_oper_get_data;
        const data = {
            'project_code': project_code
        };
        const success = function(response) {
	    for(const [key, val] of Object.entries(response.result)) {
                $('#' + key).val(val);
            }
        };
	xhr_post(url, success, data);
    }
}


const project_load_project = function () {
    const project_code = $('#project_code').val();
    const div_project = $('#div-project');
    if(project_code == '' || project_code == null) {
        div_project.html('');
    } else {
        const url = Constants.path_project_page_project;
        const success = function(html) {
	    div_project.html(html);
        };
        const data = {
            'project_code': project_code
        };
	xhr_post(url, success, data, 'html');
    }
}


const project_upload_action = function (file_id) {
    if(project_computing) {
        return;
    }
    const file_content = $('#' + file_id).prop('files')[0];
    const project_code = $('#project_code').val();
    if(file_content) {
        const form_data = new FormData();
        const url = Constants.path_project_oper_upload;
        const success = function(response) {
            base_report(response.msgs, response.success);
            project_init();
            project_end_computation();
        }
        project_start_computation();
        form_data.append('file_id', file_id);
        form_data.append('file_content', file_content);
        form_data.append('project_code', project_code);
        $.ajax({
            url: url,
            type: 'POST',
            data: form_data,
            processData: false,
            contentType: false,
	    error: xhr_error,
	    success: success
        });
    }
}


const project_handle_action_response = function (response) {
    base_report(response.msgs, response.success);
    if(!response.success) {
        for(const id of response.result) {
            $('#' + id).addClass('error');
        }
        setTimeout(function() {
            for(const id of response.result) {
                $('#' + id).removeClass('error');
            }
        }, base_tooltip_time * 1000);
    }
}

const project_basic_action = function (action, params = null) {
    if(project_computing) {
        return;
    }
    const url = Constants.path_project_oper_action;
    const data = {
        'action': action,
        'project_code': $('#project_code').val(),
        'action_params': {}
    };
    if(params != null) {
        for(const [key, val] of Object.entries(params)) {
            data['action_params'][key] = val;
        }
    }
    const success = function(response) {
        project_handle_action_response(response);
        if(action != 'associate-manual') {
            project_init();
        }
        project_end_computation();
        if(response.success && response.result.next_action != null) {
            console.log("continue with " + response.result.next_action);
            project_basic_action(action);
        }
    };
    project_start_computation();
    xhr_post(url, success, data);
}


const project_manual_association_open = function () {
    const project_code = $('#project_code').val();
    const div_manual_association = $('#div-manual-association');
    if(project_code != '' && project_code != null) {
        const url = Constants.path_project_page_manual_association;
        const success = function(response) {
            project_handle_action_response(response);
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


const project_clean_files = function () {
    const go = function () {
        project_basic_action('clean-files');
    };
    base_ask_confirmation(Lang['qst_clean_project_files_confirmation'], go);
}


const project_associate_manual = function (student, copy) {
    const params = {
        'student': student,
        'copy': copy,
        'id': $('#assoc-' + student + '-' + copy).val()
    };
    project_basic_action('associate-manual', params);
}


const project_submit_data = function () {
    const data = base_input_values('#table-action-params');
    data['code'] = $('#project_code').val();
    xhr_post(
        Constants.path_project_oper_set_data,
        project_handle_action_response,
        data
    );
}
