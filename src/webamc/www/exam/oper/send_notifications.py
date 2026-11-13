from webamc import mailing
from webamc.db import queries, tables
from webamc.util import fmt
from webamc.www.all import *
from webamc.www.exam import util


def data(ctx: context.Context, args: types.args_oper_t) -> fa.Response:

    exm_id = args["exm_id"]
    exam = util.get_exam(ctx, exm_id)[1]

    # check the exam is finished
    if datetime.datetime.now() <= exam.end_time():
        return base.wrap_code("err_exam_not_finished")

    # get the mail file
    mail = mailing.find_mail("notification-email")
    if mail is None:
        return base.wrap_code("err_mail_file_not_found")

    usr = queries.get_usr(ctx.dbs, session.usr_id(ctx))
    if usr is None:
        raise fa.HTTPException(status_code=403)
    cc = [usr.usr_eaddr]

    query = ctx.dbs.query(
        tables.Usr
    ).select_from(
        tables.Registration
    ).where(
        tables.Registration.reg_exam == exm_id
    ).join(
        tables.Submission,
        tables.Submission.sub_exm_registration == tables.Registration.reg_id
    ).where(
        tables.Submission.sub_visible
    ).join(
        tables.Usr,
        tables.Usr.usr_id == tables.Registration.reg_usr
    )
    bcc = [usr.usr_eaddr for usr in query]
    if len(bcc) == 0:
        return base.wrap_code("err_mail_no_recipient")
    fields = {
        "sender": fmt.fmt_name(usr.usr_fst_name, usr.usr_name),
        "exam": exam.exm_title.title(),
        "url": config.CONFIG["base_url"] + base.mkuri("/")
    }
    if not mailing.send_mail(list(), mail, fields, bcc=bcc, cc=cc):
        return base.wrap_code("err_mail_server")
    return base.wrap_code(
        "succ",
        msgs=[lang.txt("exam_param_mail_sent", str(len(bcc)))]
    )
