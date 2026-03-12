const auth_send_password_change = function () {
    const data = base_input_values('#table-password-change');
    data["tkt_type"] = Constants.ticket_password_change;
    xhr_post_oper(Constants.path_ticket_oper_send, data);
};


const auth_send_login_local = function () {
    const data = base_input_values('#table-login-local');
    const success_func = function (_) {
	window.location.replace(Constants.path_);
    };
    xhr_post_oper(Constants.path_auth_oper_login_local, data, success_func);
};


const auth_send_creation = function () {
    const data = base_input_values('#table-creation');
    data["tkt_type"] = Constants.ticket_account_creation;
    xhr_post_oper(Constants.path_ticket_oper_send, data);
};
