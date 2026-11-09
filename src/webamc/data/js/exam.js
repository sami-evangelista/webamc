const exam_submit = function () {
    const values = base_input_values('#div_creation');
    const success = function (_) {
        base_relocate(Constants.path_exam_page_main);
    };
    xhr_db_insert('exam', values, success);
}


const exam_delete = function (db_exm_id) {
    const go = function () {
	const success = function () {
            location.reload();
	};
	const where = {
            'op': '=',
            'col': 'exm_id',
            'val': db_exm_id
        };
	xhr_db_delete('exam', [where], success);
    }
    const question = Lang['qst_confirmation_exam_deletion'];
    base_ask_confirmation(question, go);
}


const exam_dashboard_select = function () {
    const exm_id = $('#exm_id').val();
    const dashboard = $('#div-exam-dashboard');
    if(exm_id == '' || exm_id == null) {
	dashboard.html('');
    } else {
	const success = function(html) {
	    dashboard.html(html);
	};
	const data = {
	    'exm_id': exm_id
	};
	const url = Constants.path_exam_page_dashboard;
	xhr_post(url, success, data, 'html');
    }
}


const exam_register = function (what) {
    const data = {
        'exm_id': base_input_value('exm_id'),
        'usr_id': null,
        'grp_id': null
    };
    data[what] = base_input_value(what);
    if(data['exm_id'] != null
       && (data['grp_id'] != null || data['usr_id'] != null)) {
	const success = function (result) {
            base_report_infos(result.msgs);
	    exam_dashboard_select();
	};
	const url = Constants.path_exam_oper_register;
	xhr_post_oper(url, data, success);
    }
}


const exam_select_all_registrations = function () {
    $('.checkbox_registration')
	.prop('checked', $('#checkbox_all').prop('checked'));
}


const exam_unregister = function () {
    let queries = [];
    const handle_checkbox = function(_, checkbox) {
	if($(checkbox).prop('checked')) {
	    const reg_id = $(checkbox).data('reg_id');
            const where = {
		'op': '=',
		'col': 'reg_id',
		'val': reg_id
	    };
	    const query = {
	        'type': 'delete',
		'table': 'registration',
		'where': [where]
	    };
	    queries.push(query);
	}
    };
    $('.checkbox_registration').each(handle_checkbox);
    if(queries.length > 0) {
	const question = Lang['qst_confirmation_registrations_delete'];
	const go = function(){
	    const success = function (_) {
		exam_dashboard_select();
	    };
	    xhr_db(queries, success);
        };
	base_ask_confirmation(question, go);
    }
}


const exam_view_submission = function (sub_id) {
    if(sub_id != null) {
        const args = {
            'mode': 'view',
            'sub_id': sub_id
        };
        const url = base_encode_url(Constants.path_mcq_page_form, args);
        window.open(url, '_blank').focus();
    }
}


const exam_publish = function (exm_id) {
    const data = {
        'exm_id': base_input_value('exm_id')
    };
    const url = Constants.path_exam_oper_publish_scores;
    xhr_post_oper(url, data);
}
