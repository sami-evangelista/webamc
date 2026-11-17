from webamc.db import tables, queries
from webamc.www.all import *
from webamc.www.mcq import util


EXAM_NO_REGISTRATIONS = (10, 30)
EXAM_PROB_ABSENT = 0.05
EXAM_PROB_ANSWER = 0.95
EXAM_DURATION = 60
USR_PROB = (40, 110)
QST_PROB = (40, 110)
USR_STEP = 2
QST_STEP = 1


def data(ctx: context.Context, args: types.args_oper_t) -> fa.Response:

    next_usr_prob = USR_PROB[1]
    next_qst_prob = QST_PROB[1]

    def prob(p: float) -> bool:
        return random.random() <= p

    def random_date() -> datetime.datetime:
        return datetime.datetime(
            random.randint(2020, 2026),
            random.randint(1, 12),
            random.randint(1, 28)
        )

    def new_usr(u: tables.Usr) -> None:
        nonlocal next_usr_prob
        if u not in usr_prob:
            usr_prob[u] = float(next_usr_prob) / 100.0
            next_usr_prob -= USR_STEP
            if next_usr_prob < USR_PROB[0]:
                next_usr_prob = USR_PROB[1]

    def new_qst(qst: tables.Item) -> None:
        nonlocal next_qst_prob
        if qst not in qst_prob:
            qst_prob[qst] = float(next_qst_prob) / 100.0
            next_qst_prob -= QST_STEP
            if next_qst_prob < QST_PROB[0]:
                next_qst_prob = QST_PROB[1]
            qst_choices[qst, True] = list()
            qst_choices[qst, False] = list()
            for cho in queries.get_children(ctx.dbs, qst.itm_id):
                qst_choices[qst, cho.itm_cho_correct] += list(
                    ctx.dbs.query(
                        tables.ItemInstance
                    ).where(
                        tables.ItemInstance.iti_item==cho.itm_id
                    )
                )

    def pick_choice(
            qst: tables.Item,
            usr: tables.Usr,
            num: int
    ) -> tp.Optional[tables.ItemInstance]:
        instances = [
            inst
            for inst in qst_choices[qst, prob(usr_prob[usr] * qst_prob[qst])]
            if inst.iti_num == num
        ]
        if len(instances) == 0:
            return None
        return random.choice(instances)

    def pick_usr() -> tp.Optional[tables.Usr]:
        result = ctx.dbs.query(
            tables.Usr
        ).where(
            tables.Usr.usr_id.not_in(usr_ids)
        ).order_by(
            sa.func.random()
        ).first()
        if result is not None:
            usr_ids.add(result.usr_id)
            new_usr(result)
        return result

    def pick_mcq() -> tp.Optional[tables.Item]:
        return ctx.dbs.query(
            tables.Item
        ).where(
            tables.Item.itm_is_mcq
        ).order_by(
            sa.func.random()
        ).first()

    def gen_submission(
            mcq: tables.Item,
            usr: tables.Usr,
            exam: tp.Optional[tables.Exam],
            reg: tp.Optional[tables.Registration]
    ) -> None:
        content = util.gen_mcq_content(ctx, mcq)
        if exam is None or reg is None:
            sub_type = types.SUBMISSION_TYPE_REVIEW
            sub_date = random_date()
            sub_rev_usr = usr.usr_id
            sub_rev_mcq = mcq.itm_id
            sub_exm_registration = None
        else:
            sub_type = types.SUBMISSION_TYPE_EXAM
            sub_date = exam.exm_start + datetime.timedelta(minutes=1)
            sub_rev_usr = None
            sub_rev_mcq = None
            sub_exm_registration = reg.reg_id
        sub = tables.Submission(
            sub_type=sub_type,
            sub_date=sub_date,
            sub_date_update=sub_date,
            sub_visible=False,
            sub_content=json.dumps(content),
            sub_exm_registration=sub_exm_registration,
            sub_rev_usr=sub_rev_usr,
            sub_rev_mcq=sub_rev_mcq
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
                qst = queries.get_item(ctx.dbs, node["itm_id"])
                new_qst(qst)
                if prob(EXAM_PROB_ANSWER):
                    inst = pick_choice(qst, usr, node["iti_num"])
                    if inst is not None:
                        ans = tables.Answer(
                            ans_submission=sub.sub_id,
                            ans_instance=inst.iti_id
                        )
                        ctx.dbs.add(ans)

    no_rnd_exams = args["no_rnd_exams"]
    no_rnd_submissions = args["no_rnd_submissions"]
    usr_prob: dict[tables.Usr, float] = dict()
    qst_prob: dict[tables.Item, float] = dict()
    qst_choices: dict[
        tuple[tables.Item, bool],
        list[tables.ItemInstance]
    ] = dict()
    usr_ids: set[int] = set()

    for _ in range(no_rnd_exams):

        # pick a random mcq
        mcq = pick_mcq()
        if mcq is not None:

            # create an exam for it
            seed = random.randint(1, 2 ** 16)
            exam = tables.Exam(
                exm_title=f"A random exam with number {seed}",
                exm_mcq=mcq.itm_id,
                exm_start=random_date(),
                exm_duration=EXAM_DURATION
            )
            ctx.dbs.add(exam)
            ctx.dbs.flush()

            # generate a random number of registrations and submissions
            no_registrations = random.randint(*EXAM_NO_REGISTRATIONS)
            usr_ids = set()
            for _ in range(no_registrations):

                # get a random user and generate a registration for her
                usr = pick_usr()
                if usr is not None:
                    reg = tables.Registration(
                        reg_usr=usr.usr_id,
                        reg_exam=exam.exm_id
                    )
                    ctx.dbs.add(reg)
                    ctx.dbs.flush()

                    # the user can be absent with probability
                    # EXAM_PROB_ABSENT else we generate a submission
                    # for her
                    if not prob(EXAM_PROB_ABSENT):
                        gen_submission(mcq, usr, exam, reg)

    for _ in range(no_rnd_submissions):
        usr_ids = set()
        mcq = pick_mcq()
        usr = pick_usr()
        if mcq is not None and usr is not None:
            gen_submission(mcq, usr, None, None)

    return base.wrap_code("succ")
