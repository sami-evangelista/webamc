/* current exercise */
var mcq_exe_current = 0;

/* list[qst_id] */
var mcq_qst_list = [];

/* dict[qst_id, cho_id list] */
var mcq_qst_content = {};

/* dict[qst_id, exe_id] */
var mcq_qst_exe = {};

/* current question (if mcq_mode == mcq_mode_one_by_one) */
var mcq_qst_current = 0;

/* 0 = one question displayed (default), 1 = all questions displayed */
const mcq_mode_one_by_one = 0;
const mcq_mode_all = 1;
var mcq_mode = mcq_mode_one_by_one;

/* specifies if changes have been made since the last save */
var mcq_changes_done = false;

var mcq_clock_timeout = null;

var mcq_content;


const mcq_set_status = function (html_id, status = null) {
    const elem = $('#' + html_id)
          .removeClass('mcq-status-wrong')
          .removeClass('mcq-status-partially-correct')
          .removeClass('mcq-status-correct')
          .removeClass('mcq-status-unfilled')
          .removeClass('mcq-status-filled')
    ;
    if(status != null) {
        elem.addClass('mcq-status-' + status);
    }
}


const mcq_set_qst_status = function (qst_id, status) {
    const html_id = 'qst_' + qst_id + '_status';
    mcq_set_status(html_id, status);
    mcq_set_status(html_id + '_rule', status);
}


const mcq_set_cho_status = function (cho_id, status) {
    const html_id = 'cho_' + cho_id + '_status';
    mcq_set_status(html_id, status);
}


const mcq_collect_answers = function () {
    const result = {
        'itm_id': parseInt($('#itm_id').val()),
	'choices': {},
	'questions': {},
        'sub_content': mcq_content
    };
    for(let qst_id in mcq_qst_content) {
	result['questions'][qst_id] = {};
        for(const cho_id of mcq_qst_content[qst_id]) {
            const checked = $('#cho_' + cho_id).is(':checked');
            result['choices'][cho_id] = checked;
	    result['questions'][qst_id][cho_id] = checked;
	}
    }
    return result;
}


const mcq_save_review = function () {
    const go = function () {
        const success = function (result) {
            const args = {
                'mode': 'view',
                'sub_id': result['result']['sub_id']
            };
            base_relocate(base_encode_url(Constants.path_mcq_page_form, args));
        };
        const url = Constants.path_mcq_oper_save;
        const data = mcq_collect_answers();
        xhr_post_oper(url, data, success);
    };
    base_ask_confirmation(Lang['mcq_qst_confirmation_send'], go);
}


const mcq_reset_mode = function (mode) {
    mcq_qst_current = mcq_qst_list[0];
    mcq_exe_current = mcq_qst_exe[mcq_qst_current];
    mcq_set_mode(mode);
}


const mcq_reset_all = function () {
    const go = function () {
	$('.choice-input')
            .prop('disabled', false)
            .prop('checked', false);
	$('.mcq-status-box-choice').each(function (i) {
            mcq_set_status($(this).attr('id'));
	});
	$('.mcq-status-box-question').each(function (i) {
            mcq_set_status($(this).attr('id'), 'unfilled');
	});
	$('#btn-validate_mcq').show();
	mcq_reset_mode(mcq_mode);
    };
    base_ask_confirmation(Lang['mcq_qst_confirmation_restart'], go);
}


const mcq_reset_question = function (qst_id) {
    if($('#qst_' + qst_id + '_status').hasClass('mcq-status-filled')) {
        mcq_set_qst_status(qst_id, correct ? 'correct' : 'unfilled');
        for(cho_id of mcq_qst_content[qst_id]) {
            $('#cho_' + cho_id).prop('checked', false);
        }
    }
}


const mcq_on_choice_click = function (cho_id) {
    mcq_changes_done = true;
    for(let qst_id in mcq_qst_content) {
        const cho_ids = mcq_qst_content[qst_id];
        if(cho_ids.includes(cho_id)) {
            const status = cho_ids.every(function (x) {
                return !$('#cho_' + x).is(':checked');
            }) ? 'unfilled' : 'filled';
            mcq_set_qst_status(qst_id, status);
        }
    }
}


const mcq_show_item = function (item) {
    $('#' + item).show(base_anim_delay);
    $('#' + item + '_body').show(base_anim_delay);
}


const mcq_hide_item = function (item) {
    $('#' + item).hide(base_anim_delay);
    $('#' + item + '_body').hide(base_anim_delay);
}


const mcq_set_current_qst = function (qst_id) {
    if(0 == mcq_qst_list.length) {
	return;
    }
    qst_next = qst_id;
    exe_next = mcq_qst_exe[qst_next];
    if(exe_next != mcq_exe_current) {
        mcq_hide_item('exe_' + mcq_exe_current);
        mcq_show_item('exe_' + exe_next);
    }
    mcq_hide_item('qst_' + mcq_qst_current);
    mcq_show_item('qst_' + qst_next);
    $('.mcq-status-box-question').removeClass('mcq-status-current');
    $('#qst_' + qst_next + '_status_rule').addClass('mcq-status-current');
    mcq_qst_current = qst_next;
    mcq_exe_current = exe_next;
}


const mcq_move_qst = function (move) {
    if(0 == mcq_qst_list.length) {
	return;
    }
    var pos = - 1;
    for(var i = 0; pos < 0 && i < mcq_qst_list.length; i ++) {
        if(mcq_qst_list[i] == mcq_qst_current) {
            pos = i;
        }
    }
    pos += move;
    while(pos < 0) {
        pos += mcq_qst_list.length;
    }
    pos = pos % mcq_qst_list.length;
    mcq_set_current_qst(mcq_qst_list[pos]);
}


const mcq_key_pressed = function (evt) {
    let key = (evt.keyCode ? evt.keyCode : evt.which);
    let character = String.fromCharCode(key);
    if(Constants.key_qst_next == character) {
	mcq_move_qst_next();
    } else if(Constants.key_qst_prev == character) {
        mcq_move_qst_prev();
    } else if(Constants.key_switch_mode == character) {
	mcq_switch_mode();
    }
}


const mcq_move_qst_prev = function () {
    if(mcq_mode == mcq_mode_one_by_one) {
	mcq_move_qst(-1);
    }
}


const mcq_move_qst_next = function () {
    if(mcq_mode == mcq_mode_one_by_one) {
	mcq_move_qst(1);
    }
}


const mcq_switch_mode = function () {
    mcq_set_mode((mcq_mode + 1) % 2);
}


const mcq_set_mode = function (mode) {
    mcq_mode = mode;
    $('.mcq-status-box-question').removeClass('mcq-status-current');
    if(mcq_mode == mcq_mode_one_by_one) {
        $('.mcq-question, .mcq-exercise').hide();
        mcq_show_item('exe_' + mcq_exe_current);
        mcq_show_item('qst_' + mcq_qst_current);
        $('.mcq-status-box-question').removeClass('mcq-status-current');
        $('#qst_' + mcq_qst_current + '_status_rule')
            .addClass('mcq-status-current');
    } else if(mcq_mode == mcq_mode_all) {
        $('.mcq-question-body, .mcq-exercise-body').hide();
        $('.mcq-question, .mcq-exercise').show();
    } else {
        mcq_set_mode(mcq_mode_one_by_one);
    }
}


const mcq_init = function (mode, content) {
    $(document).keypress(function (evt) {
        mcq_key_pressed(evt);
    });
    mcq_content = content
    mcq_reset_mode(mode);
}


const mcq_focus_question = function (qst_id) {
    if(mcq_mode_one_by_one == mcq_mode) {
	mcq_set_current_qst(qst_id);
    } else {
	const exe_id = mcq_qst_exe[qst_id];
        mcq_show_item('qst_' + qst_id);
        mcq_show_item('exe_' + exe_id);
	$([document.documentElement, document.body]).animate({
            scrollTop: $('#qst_' + qst_id).offset().top
	}, base_anim_delay);
    }
}


const mcq_new_exe = function (exe_id) {
    const label_click = function () {
        $('#exe_' + exe_id + '_body').toggle(base_anim_delay);
    };
    $('#exe_' + exe_id + '_label').on('click', label_click);
}


const mcq_new_qst = function (qst_id, exe_id) {
    const label_click = function () {
        $('#qst_' + qst_id + '_body').toggle(base_anim_delay);
    };
    const status_rule_click = function () {
        mcq_focus_question(qst_id);
    };
    const status_click = function () {
        mcq_reset_question(qst_id);
    };
    mcq_qst_list.push(qst_id);
    mcq_qst_content[qst_id] = [];
    mcq_qst_exe[qst_id] = exe_id;
    $('#qst_' + qst_id + '_label').on('click', label_click);
    $('#qst_' + qst_id + '_status').on('click', status_click);
    $('#qst_' + qst_id + '_status_rule').on('click', status_rule_click);
}


const mcq_new_cho = function (cho_id, qst_id) {
    const cho_click = function () {
        mcq_on_choice_click(cho_id);
    };
    mcq_qst_content[qst_id].push(cho_id);
    $('#cho_' + cho_id).on('click', cho_click);
}


const mcq_init_timer = function (sec_duration, end_time) {
    const div_timer = $('#mcq-exam-timer');
    const span_timer_text = $('#mcq-exam-timer-text');
    const countdown = function() {
        const sec_left = parseInt((end_time - Date.now()) / 1000);

        /* exam finished => save answers for the last time and then
         *   finish the mcq and finally redirect to the index page */
        if(sec_left <= 0) {
            if(mcq_clock_timeout != null) {
                clearInterval(mcq_clock_timeout);
            }
            const finish = function () {
                const send_finish = function () {
		    const url = Constants.path_mcq_oper_finish;
		    const success = function (_) {
			base_relocate(Constants.path_);
		    };
                    xhr_post_oper(url, null, success);
                };
                base_report_infos(
                    [Lang['mcq_info_exam_finished']],
                    send_finish
                );
            };
            mcq_save_exam(finish);
            return false;
	}

        /* update the timer value and its background color */
        const hours = Math.floor(sec_left / 3600);
        const minutes = Math.floor((sec_left - hours * 3600) / 60);
        const seconds = sec_left % 60;
        const txt = hours.toString()
              + ':' + minutes.toString().padStart(2, '0')
              + ':' + seconds.toString().padStart(2, '0')
        ;
        const ratio = sec_left / sec_duration;
        const gval = Math.max(0, Math.min(2 * ratio, 1)) * 255;
        const rval = Math.max(0, Math.min(2 - 2 * ratio, 1)) * 255;
        const g = parseInt(gval).toString(16);
        const r = parseInt(rval).toString(16);
        const col = '#' + r.padStart(2, '0') + g.padStart(2, '0') + '00';
        span_timer_text.html(txt);
        div_timer.css('background-color', col);
        return true;
    };
    if(countdown()) {
        mcq_clock_timeout = setInterval(countdown, 1000);
    }
};


const mcq_save_exam = function(callback = null) {
    if(mcq_changes_done) {
        mcq_changes_done = false;
        const data = mcq_collect_answers();
        const url = Constants.path_mcq_oper_save;
        const pop_info = function (_) {
            base_report_infos([Lang['mcq_info_progress_saved']], callback);
        };
        xhr_post_oper(url, data, pop_info);
    } else {
        base_report_infos([Lang['mcq_info_progress_saved']]);
        if(callback != null) {
            callback();
        }
    }
}


const mcq_init_save_timer = function () {
    setInterval(mcq_save_exam, Constants.exam_autosave_period * 1000);    
}
