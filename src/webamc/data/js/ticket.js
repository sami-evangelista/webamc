const ticket_password_change = function (ticket) {
    const data = base_input_values('#table-password-change');
    data['ticket'] = ticket;
    xhr_post_oper(Constants.path_ticket_oper_password_change, data);
}


const ticket_account_creation = function (ticket) {
    const data = base_input_values('#table-account-creation');
    data['ticket'] = ticket;
    xhr_post_oper(Constants.path_ticket_oper_account_creation, data);
}
