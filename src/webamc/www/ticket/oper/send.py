from email.parser import Parser

from webamc.www.all import *
from webamc import mailing
from webamc.db import tables, col_types as ct
from webamc.util import security
from webamc.www.ticket import router


def data(
        ctx: context.Context,
        args: router.args_oper_send_t
) -> fa.Response:

    # check eaddr is valid
    try:
        ct.Eaddr.val_chk(args["usr_eaddr"])
    except ValueError:
        return base.wrap_code("err_invalid_eaddr")

    query = ctx.dbs.query(tables.Usr)
    if session.is_logged_in(ctx):
        query = query.where(tables.Usr.usr_id == session.usr_id(ctx))
    else:
        query = query.where(tables.Usr.usr_eaddr == args["usr_eaddr"])
    usr = query.first()

    codes: dict[types.ticket_type_t, types.oper_code_t] = {
        types.TICKET_ACCOUNT_CREATION: "succ_ticket_account_creation_sent",
        types.TICKET_EADDR_CHANGE: "succ_ticket_eaddr_change_sent",
        types.TICKET_PASSWORD_CHANGE: "succ_ticket_password_change_sent"
    }
    code = codes[args["tkt_type"]]

    # perform some checks
    if args["tkt_type"] == types.TICKET_ACCOUNT_CREATION:
        if usr is not None:
            return base.wrap_code(code)
    elif usr is None:
        return base.wrap_code(code)

    # generate the ticket
    tkt_value = security.gen_ticket()
    validity = config.CONFIG["password_ticket_validity"]
    deadline = (
        datetime.datetime.now() + datetime.timedelta(seconds=validity)
    )
    usr_id = None if usr is None else usr.usr_id
    if args["tkt_type"] != types.TICKET_ACCOUNT_CREATION:
        assert usr_id is not None
        ctx.dbs.query(
            tables.Ticket
        ).where(
            (tables.Ticket.tkt_usr==usr_id)
            & (tables.Ticket.tkt_type==args["tkt_type"])
        ).delete()
    ticket = tables.Ticket(
        tkt_usr=usr_id,
        tkt_value=tkt_value,
        tkt_deadline=deadline,
        tkt_type=args["tkt_type"],
        tkt_eaddr=args["usr_eaddr"]
    )
    ctx.dbs.add(ticket)
    ctx.dbs.commit()

    url = config.CONFIG["base_url"] + base.mkuri(
        "/ticket/page/main",
        ticket=tkt_value
    )

    # read the appropriate mail file and set its content if no
    # mail file found
    mails: dict[types.ticket_type_t, types.mail_file_t] = {
        types.TICKET_ACCOUNT_CREATION: "account-creation",
        types.TICKET_EADDR_CHANGE: "eaddr-change",
        types.TICKET_PASSWORD_CHANGE: "password-change"
    }
    file_path = mailing.find_mail(mails[args["tkt_type"]])
    if file_path is None:
        subjects: dict[types.ticket_type_t, str] = {
            types.TICKET_ACCOUNT_CREATION: "Account Creation",
            types.TICKET_EADDR_CHANGE: "Email address change",
            types.TICKET_PASSWORD_CHANGE: "Password change"
        }
        msg_txt = f"Subject: {subjects[args['tkt_type']]}\n\n{url}"
    else:
        with open(file_path, encoding="utf-8") as fd:
            msg_txt = fd.read()

    # replace variables that may appear in the mail
    msg_txt = msg_txt.format(
        service=config.CONFIG["service_name"],
        url=url,
        usr_id=usr.usr_code if usr is not None else "",
        eaddr=args["usr_eaddr"]
    )

    # create the mail and send it
    msg = Parser().parsestr(msg_txt)
    eaddr_from = config.CONFIG["smtp_eaddr_from"]
    eaddr_to = args["usr_eaddr"]
    msg["From"] = eaddr_from
    msg["To"] = eaddr_to
    if not mailing.send_mail(
            eaddr_from, eaddr_to, msg.as_string().encode("utf8")
    ):
        return base.wrap_code("err_mail_server")

    return base.wrap_code(code)
