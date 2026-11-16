from webamc.db import tables, queries
from webamc.www.all import *
from webamc.www.mcq import util


EXAM_NO_REGISTRATIONS = (10, 30)
EXAM_PROB_ABSENT = 0.05
EXAM_PROB_ANSWER = 0.95
EXAM_DURATION = 60


def data(ctx: context.Context, args: types.args_oper_t) -> fa.Response:

    no_rnd_exams = args["no_rnd_exams"]
    no_rnd_submissions = args["no_rnd_submissions"]

    exm_start = datetime.datetime(2020, 1, 1)
    for _ in range(no_rnd_exams):

        # pick a random mcq
        item = ctx.dbs.query(
            tables.Item
        ).where(
            tables.Item.itm_is_mcq
        ).order_by(
            sa.func.random()
        ).first()
        if item is None:
            break

        # create an exam for it
        seed = random.randint(1, 2 ** 64)
        exam = tables.Exam(
            exm_title=f"A random exam with number {seed}",
            exm_mcq=item.itm_id,
            exm_start=exm_start,
            exm_duration=EXAM_DURATION
        )
        ctx.dbs.add(exam)
        ctx.dbs.flush()

        # generate a random number of registrations and submissions
        no_registrations = random.randint(*EXAM_NO_REGISTRATIONS)
        usr_ids: set[int] = set()
        for _ in range(no_registrations):

            # get a random user and generate a registration with it
            usr = ctx.dbs.query(
                tables.Usr
            ).where(
                tables.Usr.usr_id.not_in(usr_ids)
            ).order_by(
                sa.func.random()
            ).first()
            if usr is None:
                break
            usr_ids.add(usr.usr_id)
            reg = tables.Registration(
                reg_usr=usr.usr_id,
                reg_exam=exam.exm_id
            )
            ctx.dbs.add(reg)
            ctx.dbs.flush()

            # the user can be absent with probability EXAM_PROB_ABSENT
            if random.random() <= EXAM_PROB_ABSENT:
                continue

            # else we generate a submission for her
            content = util.gen_mcq_content(ctx, item)
            sub_date_update = exm_start + datetime.timedelta(
                minutes=random.randint(1, EXAM_DURATION - 1)
            )
            sub = tables.Submission(
                sub_type=types.SUBMISSION_TYPE_EXAM,
                sub_date=exm_start + datetime.timedelta(minutes=1),
                sub_date_update=sub_date_update,
                sub_visible=False,
                sub_content=json.dumps(content),
                sub_exm_registration=reg.reg_id
            )
            ctx.dbs.add(sub)
            ctx.dbs.flush()
            for node, _ in types.mcq_enum_items(content):
                assert node["itm_type"] != types.ITEM_TYPE_CHOICE
                ans = tables.Answer(
                    ans_submission=sub.sub_id,
                    ans_instance=node["iti_id"]
                )
                ctx.dbs.add(ans)

                # for each question the user answer with probability
                # EXAM_PROB_ANSWER
                if node["itm_type"] == types.ITEM_TYPE_QUESTION:
                    if random.random() >= EXAM_PROB_ANSWER:
                        continue
                    choices = [
                        itm.itm_id
                        for itm in
                        queries.get_children(ctx.dbs, node["itm_id"])
                    ]
                    inst = ctx.dbs.query(
                        tables.ItemInstance
                    ).where(
                        tables.ItemInstance.iti_item.in_(choices)
                    ).where(
                        tables.ItemInstance.iti_num==node["iti_num"]
                    ).order_by(
                        sa.func.random()
                    ).first()
                    if inst is None:
                        break
                    ans = tables.Answer(
                        ans_submission=sub.sub_id,
                        ans_instance=inst.iti_id
                    )
                    ctx.dbs.add(ans)

        exm_start = exm_start + datetime.timedelta(minutes=EXAM_DURATION)

    return base.wrap_code("succ")
