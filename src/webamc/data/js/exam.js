const exam_submit = function () {
    const values = base_input_values('#div_creation');
    const success = function (_) {
        base_relocate(Constants.path_exam_page_main);
    };
    xhr_db_insert('exam', values, success);
}


const exam_toggle_details = function (db_exm_id) {
    const div_details = $('#div-exam-details-' + db_exm_id);
    const img_zoom = $('#img-exam-zoom-' + db_exm_id);
    let src;
    div_details.toggle();
    if(div_details.is(':visible')) {
        src = 'zoom-out';
    } else {
        src = 'zoom-in';
    }
    img_zoom.attr('src', base_img_src(src));
}


const exam_delete = function (db_exm_id, db_exm_mcq) {
    const go = function () {
	const success = function () {
            location.reload();
	};
	const where = [
            {'op': '=', 'col': 'exm_id', 'val': db_exm_id},
            {'op': '=', 'col': 'exm_mcq', 'val': db_exm_mcq}
	];
	xhr_db_delete('exam', where, success);
    }
    const question = Lang['qst_exam_deletion_confirmation'];
    base_ask_confirmation(question, go);
}


const exam_dashboard_select = function () {
    const exm_id = $('#exm_id').val();
    const dashboard = $('#exam_dashboard');
    if(exm_id == '' || exm_id == null) {
	dashboard.html('');
    } else {
	const success = function(html) {
	    dashboard.html(html);
	};
	const data = {
	    'exm_id': exm_id
	};
	const url = Constants.path_exam_page_dashboard_exam;
	xhr_post(url, success, data, 'html');
    }
}


const exam_register_group = function () {
    const exm_id = $('#exm_id').val();
    const grp_id = $('#grp_id').val();
    if(exm_id != '' && grp_id != '') {
	const success = function (result) {
            base_report_infos(result.msgs);
	    exam_dashboard_select();
	};
	const data = {
	    'exm_id': exm_id,
	    'grp_id': grp_id
	};
	const url = Constants.path_exam_oper_register_group;
	xhr_post_oper(url, data, success);
    }
}


const exam_select_all_registrations = function () {
    $('.checkbox_registration')
	.prop('checked', $('#checkbox_all').prop('checked'));
}


const exam_delete_registrations = function () {
    let queries = [];
    const handle_checkbox = function(_, checkbox) {
	if($(checkbox).prop('checked')) {
	    const reg_id = $(checkbox).data('reg_id');
	    let query = {
	        'type': 'delete',
		'table': 'registration',
		'where': [{
		    'op': '=',
		    'col': 'reg_id',
		    'val': reg_id
		}]
	    };
	    queries.push(query);
	}
    };
    $('.checkbox_registration').each(handle_checkbox);
    if(queries.length > 0) {
		const question = Lang['qst_item_deletion_confirmation'];
		const go = function(){
			const success = function (_) {
				 exam_dashboard_select();
			};
			xhr_db(queries, success);
    };
	base_ask_confirmation(question, go);
	}
}
