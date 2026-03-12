const profile_send_eaddr_change = function () {
    const data = {
	'usr_eaddr': $('#usr_eaddr').val()
    };
    const url = Constants.path_ticket_oper_send;
    data["tkt_type"] = Constants.ticket_eaddr_change;
    xhr_post_oper(url, data);
}
