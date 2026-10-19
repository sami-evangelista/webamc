const base_anim_delay = 400;
const base_tooltip_time = 5;
var base_computing = false;
var base_wait_modal = null;


const base_img_src = function (file_name) {
    const file = file_name + '-' + Constants.icon_size + '.png';
    return Constants.path_static + '?file_name=' + file;
}


const base_report_msgs = function (msgs, notif_type, callback = null) {
    const result = msgs.length > 0;
    if(result) {
        let fst = true;
	for(const msg of msgs) {
	    fun = fst ? callback : null;
	    alertify.notify(msg, notif_type, base_tooltip_time, fun);
	    fst = false;		
	}
    }
    return result;
}


const base_report_infos = function (infos, callback = null) {
    return base_report_msgs(infos, 'custom', callback);
}


const base_report_errors = function (errors, callback = null) {
    return base_report_msgs(errors, 'error', callback);
}


const base_report = function (msgs, are_infos, callback = null) {
    const fun = are_infos ? base_report_infos : base_report_errors;
    fun(msgs, callback);
}


const base_ask_confirmation = function (question, js) {
    alertify.webamc_confirm(question, js);
}


const base_relocate = function (url) {
    if(url == null) {
        console.error("No url specified !");
    }
    window.location.href = url;
}


const base_escape_html = function (unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;")
    ;
}


const base_input_values = function (selector) {
    const result = {};
    const add_arg = function () {
        const str_to_number = function (val, parser) {
            let result = parser(val);
            if(isNaN(result)) {
                result = null;
                $(this).val('');
            }
            return result;
        }
	const name = $(this).attr('id');
	if(name == null) {
	    return;
	}
	let val;

        // get the element value
        if($(this).is('[type="checkbox"]')) {
            val = $(this).prop('checked');
	} else {
	    val = $(this).val();
	}

        // first try to convert it according to its data-type attribute
        if($(this).data('type') == 'integer') {
            val = str_to_number(val, parseInt);
        } else if($(this).data('type') == 'float') {
            val = str_to_number(val, parseFloat);
        } else if($(this).data('type') == 'boolean') {
            val = Boolean(val);
        } else if($(this).data('type') == 'string') {
            val = String(val);
        } else {

            // no data-type specified => convert according to the
            // element type
            if($(this).is('[type="number"]')) {
                val = str_to_number(val, parseInt);
	    } else {
	        if(val == ''
	           && ($(this).is('select')
		       || $(this).is('[type="date"]')
		       || $(this).is('[type="datetime-local"]'))) {
		    val = null;
	        }
            }
	}
	result[name] = val;
    };
    const types_inspected = 'input,select,textarea';
    $(selector).find(types_inspected).each(add_arg);
    if($(selector).is(types_inspected)) {
        $(selector).each(add_arg);
    }
    return result;
}


const base_input_value = function(id) {
    return base_input_values('#' + id)[id];
}


$(document).ready(function() {
    $('#menu-btn').hover(
	function () {
	    $('#menu-content').fadeIn(base_anim_delay);
	    $('#menu-btn').fadeOut(base_anim_delay);
	}
    );
    $('#menu-content').hover(
	function () {},
	function () {
	    $('#menu-content').fadeOut(base_anim_delay);
	    $('#menu-btn').fadeIn(base_anim_delay);
	}
    );
});


const base_submit_file = function (id_file, url, div_submit_result) {
    const content = $('#' + id_file).prop('files')[0];
    if(!content) {
        return;
    }
    const computation = async function() { 
        const success = function (result) {
            if(!result.success) {
                base_report_errors(result.msgs);
            } else {
                let html = '', inf = 0, warn = 0, err = 0;
                const msgs = result.result;
                for(const msg of msgs) {
                    let color = '';
                    if(msg.status == 0) {
                        color = 'aaaaff';
                        inf ++;
                    } else if(msg.status == 1) {
                        color = 'ff7f00';
                        warn ++;
                    } else if(msg.status == 2) {
                        color = 'ffaaaa';
                        err ++;
                    }
                    if(color != '') {
                        html += '<span style="color: #' + color
                            + '">' + msg.msg + '</span>\n';
                    }
                }
                html = '<pre class="terminal">'
                    + '\n<code>' + html + '</code>'
                    + '</pre>'
                    + '\n<ul>'
                    + '\n<li>' + inf + ' '
                    + Lang['seq_information_messages'] + '</li>'
                    + '\n<li>' + warn + ' '
                    + Lang['seq_warning_messages'] + '</li>'
                    + '\n<li>' + err + ' '
                    + Lang['seq_error_messages'] + '</li>'
                    + '\n</ul>';
                $('#' + div_submit_result).html(html);
            }
        }
        const form_data = new FormData();
        form_data.append(id_file, content);
        await $.ajax({
            url: url,
            type: 'POST',
            data: form_data,
            processData: false,
            contentType: false,
	    error: xhr_error,
	    success: success
        });
    };
    base_launch_computation(computation);
}


const base_help_open = function (help, section) {
    const url = Constants.path_help + '?help_id=' + help;
    const success = function (response) {
        $('#div-tooltip-help-body').html(response);
        $('#div-tooltip-help').hide().fadeIn(base_anim_delay);
        if(section != null) {
            if($('#' + section).length == 0) {
                console.log("help section " + section + " not found !");
            } else {
                location.hash = '#' + section;
            }
        }
    };
    xhr_get(url, success);
}


const base_popup_help_close = function () {
    $('#div-tooltip-help-body').html();
    $('#div-tooltip-help').fadeOut(base_anim_delay);
}


const base_launch_computation = async function (comp) {
    if(base_computing) {
        return;
    }
    let future = comp();
    base_computing = true;
    base_wait_modal = alertify
        .alert(Lang['info_please_wait'])
        .set('modal', true)
        .set('closable', false)
        .set('frameless', true);
    base_wait_modal.elements.dialog.classList.add('please_wait');
    await future;
    base_computing = false;
    if(base_wait_modal) {
        base_wait_modal.close();
        base_wait_modal = null;
    }
}
