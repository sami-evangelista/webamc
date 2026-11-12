from webamc.www.all import *
from webamc.www.exam import util
from webamc.db import queries, tables


def data(ctx: context.Context, args: types.args_oper_t) -> fa.Response:

    exm_id = args["exm_id"]
    exam = util.get_exam(ctx, exm_id)[1]

    # check the exam is finished
    if datetime.datetime.now() <= exam.end_time():
        return base.wrap_code("err_exam_not_finished")

    # list all submissions of the exam, set their visible flag to true
    # and create a message linked to the submission
    for sub, reg in queries.get_exam_submissions(ctx.dbs, exm_id):
        sub.sub_visible = True
        ctx.dbs.query(
            tables.Message
        ).where(
            tables.Message.msg_sub == sub.sub_id
        ).delete()
        msg = tables.Message(
            msg_type=types.MESSAGE_TYPE_SUBMISSION,
            msg_title=exam.exm_title,
            msg_from=session.usr_id(ctx),
            msg_to=reg.reg_usr,
            msg_sub=sub.sub_id
        )
        ctx.dbs.add(msg)

    return base.wrap_code("succ")
