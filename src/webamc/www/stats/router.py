import random
from webamc.www.all import *
from webamc.db import queries, tables
from .model.args_mcq_overview_t import args_mcq_overview_t
from .model.args_graph_t import args_graph_t
from .model.args_evo_t import args_evo_t

router = fa.APIRouter()

@router.get("/stats/page/dashboard")
def route_stats_page_dashboard(
        req: fa.Request,
        exam_id: int | None = None
) -> fa.Response:
    from .page import stats_dashboard
    with context.Context(req) as ctx:
        return stats_dashboard.page(ctx, exam_id)

@router.post("/stats/oper/graph-data")
def route_stats_open_graph_data(
    req: fa.Request,
    args: args_graph_t
) -> fa.Response:
    """
    AJAX route to send REAL graph data for a given question.
    format: JSON
    """
    with context.Context(req) as ctx:
        qst_id = args.qst_id
        exam_id = args.exam_id

        # getting all possible choices for this question
        choices = queries.get_question_choices(ctx.dbs, qst_id)

        DEV_MODE = False

        # simulation of fake random data to test stats graphs
        if DEV_MODE:
            total_students = random.randint(40, 100)

            labels = []
            data = []
            choices_info = []
            total_answered = 0

            for i, cho in enumerate(choices):
                label = chr(65 + i) if i < 26 else str(i + 1)
                labels.append(f"Réponse {label}")

                count = random.randint(0, int(total_students / len(choices)))
                total_answered += count
                data.append(count)

                choices_info.append({
                    "letter": label,
                    "id": cho.cho_id,
                    "is_correct": cho.cho_correct
                })

            no_response = max(0, total_students - total_answered)
            labels.append("Sans réponse")
            data.append(no_response)
            choices_info.append({
                "letter": "∅",
                "id": None,
                "is_correct": False,
                "is_no_response": True
            })

            if not labels:
                labels = ["No data"]
                data = [0]

            return fa.responses.JSONResponse({
                "labels": labels,
                "data": data,
                "choices_info": choices_info,
                "total_students": total_students
            })

        registrations = queries.get_exam_registrations(ctx.dbs, exam_id)
        total_students = len(registrations)

        labels = []
        data = []
        choices_info = []

        # looping through each choice to calculate stats
        for i, cho in enumerate(choices):
            label = chr(65 + i) if i < 26 else str(i + 1)
            labels.append(f"Réponse {label}")

            count = ctx.dbs.query(tables.Answer).join(
                tables.ItemInstance,
                tables.Answer.ans_instance == tables.ItemInstance.iti_id
            ).join(
                tables.ExamSubmission,
                tables.Answer.ans_submission == tables.ExamSubmission.exs_id
            ).join(
                tables.Registration,
                tables.ExamSubmission.exs_registration == tables.Registration.reg_id
            ).filter(
                tables.ItemInstance.iti_item == cho.cho_id,
                tables.Registration.reg_exam == exam_id
            ).count()

            data.append(count)

            choices_info.append({
                "letter": label,
                "id": cho.cho_id,
                "is_correct": cho.cho_correct,
                "is_no_response" : False
            })


        choice_ids = [cho.cho_id for cho in choices]
        students_who_answered = ctx.dbs.query(tables.Registration.reg_id).join(
            tables.ExamSubmission, tables.Registration.reg_id == tables.ExamSubmission.exs_registration
        ).join(
            tables.Answer, tables.ExamSubmission.exs_id == tables.Answer.ans_submission
        ).join(
            tables.ItemInstance, tables.Answer.ans_instance == tables.ItemInstance.iti_id
        ).filter(
            tables.ItemInstance.iti_item.in_(choice_ids),
            tables.Registration.reg_exam == exam_id
        ).distinct().count()

        no_response = total_students - students_who_answered
        if no_response < 0:
            no_response = 0

        labels.append("Sans réponse")
        data.append(no_response)
        choices_info.append({
            "letter": "∅",
            "id": None,
            "is_correct": False,
            "is_no_response": True
        })

        if not labels:
            labels = ["No data"]
            data = [0]

        return fa.responses.JSONResponse({
            "labels": labels,
            "data": data,
            "choices_info": choices_info,
            "total_students": total_students
        })


@router.post("/stats/oper/evolution-data")
def route_stats_evolution_data(
    req: fa.Request,
    args: args_evo_t
) -> fa.Response:

    with context.Context(req) as ctx:

        DEV_MODE = False

        # simulation of fake random data to test evolution graphs
        if DEV_MODE:
            import datetime

            # we need max_points first to generate realistic scores
            questions = queries.get_exam_questions(ctx.dbs, args.mcq_id)
            max_points = len(questions) if questions else 10

            labels = []
            data = []

            # random number of exam attempts for this fake student (e.g., between 4 and 8)
            num_attempts = random.randint(4, 8)

            # starting date (e.g., 100 days ago)
            current_date = datetime.datetime.now() - datetime.timedelta(days=100)

            for _ in range(num_attempts):
                # adding random days to make chronological sense
                current_date += datetime.timedelta(days=random.randint(7, 20))
                labels.append(current_date.strftime("%d/%m/%Y"))

                # fake score between 0 and max_points
                fake_score = round(random.uniform(0.0, float(max_points)), 1)
                data.append(fake_score)

            return fa.responses.JSONResponse({
                "labels": labels,
                "data": data,
                "max_score": max_points
            })

        # --- Real Data Logic ---
        submissions = ctx.dbs.query(
            tables.ExamSubmission, tables.Exam
        ).join(
            tables.Registration, tables.ExamSubmission.exs_registration == tables.Registration.reg_id
        ).join(
            tables.Exam, tables.Registration.reg_exam == tables.Exam.exm_id
        ).filter(
            tables.Registration.reg_usr == args.student_id,
            tables.Exam.exm_mcq == args.mcq_id
        ).order_by(
            tables.Exam.exm_start.asc()
        ).all()

        labels = []
        data = []

        for sub, exm in submissions:
            date_str = exm.exm_start.strftime("%d/%m/%Y")
            labels.append(date_str)

            detailed_scores = queries.get_student_detailed_scores(ctx.dbs, exm.exm_mcq, sub.exs_id)

            total_score = sum(detailed_scores.values()) if detailed_scores else 0.0

            data.append(float(total_score))

        if not labels:
            labels = ["No data"]
            data = [0]

        questions = queries.get_exam_questions(ctx.dbs, args.mcq_id)
        max_points = len(questions) if questions else 10

        return fa.responses.JSONResponse({
            "labels": labels,
            "data": data,
            "max_score": max_points
        })




@router.post("/stats/oper/mcq-overview-data")
def route_stats_mcq_overview_data(
    req: fa.Request,
    args: args_mcq_overview_t
) -> fa.Response:
    """
    AJAX route to send MCQ overview success rates.
    format: JSON
    """
    with context.Context(req) as ctx:
        exam_id = args.exam_id

        # getting exam object to find mcq_id
        exam = ctx.dbs.query(tables.Exam).filter(tables.Exam.exm_id == exam_id).first()
        if exam is None:
            return fa.responses.JSONResponse({"labels": [], "data": [], "qst_ids": []})

        # getting questions for this mcq
        questions = queries.get_exam_questions(ctx.dbs, exam.exm_mcq)

        DEV_MODE = True

        # simulation of fake random data to test stats graphs
        if DEV_MODE:
            labels = []
            data = []
            qst_ids = []
            exo_names = []

            for i, qst in enumerate(questions):
                # getting item to get the itm_code
                itm = queries.get_item(ctx.dbs, qst.qst_id)
                label = str(itm.itm_code) if itm.itm_code else f"Qst {i+1}"

                labels.append(label)

                exo_name = "Autre"

                if itm.itm_parent:
                    parent_itm = queries.get_item(ctx.dbs, itm.itm_parent)
                    if parent_itm:
                        exo_name = parent_itm.itm_title or parent_itm.itm_code or "Exercice sans nom"

                exo_names.append(exo_name)

                # generating a fake success percentage between 10% and 100%
                fake_percentage = round(random.uniform(10.0, 100.0), 1)
                data.append(fake_percentage)

                qst_ids.append(qst.qst_id)

            if not labels:
                labels = ["No data"]
                data = [0]

            return fa.responses.JSONResponse({
                "labels": labels,
                "data": data,
                "qst_ids": qst_ids,
                "exo_names": exo_names
            })

        # getting all submissions tied to this specific exam
        submissions = ctx.dbs.query(tables.ExamSubmission).join(
            tables.Registration, tables.ExamSubmission.exs_registration == tables.Registration.reg_id
        ).filter(
            tables.Registration.reg_exam == exam_id
        ).all()

        submission_count = len(submissions)
        question_totals = {qst.qst_id: 0.0 for qst in questions}

        # getting all registrations (total students expected)
        registrations = queries.get_exam_registrations(ctx.dbs, exam_id)
        total_students = len(registrations)

        # calculating total scores per question across all submissions
        for sub in submissions:
            detailed_scores = queries.get_student_detailed_scores(ctx.dbs, exam.exm_mcq, sub.exs_id)
            for qst_id, score in detailed_scores.items():
                if qst_id in question_totals:
                    question_totals[qst_id] += score

        labels = []
        data = []
        qst_ids = []
        exo_names = []

        # building labels and calculating success percentage
        for i, qst in enumerate(questions):
            itm = queries.get_item(ctx.dbs, qst.qst_id)

            label = str(itm.itm_code) if itm.itm_code else f"Qst {i+1}"
            labels.append(label)

            exo_name = "Autre"
            if itm.itm_parent:
                parent_itm = queries.get_item(ctx.dbs, itm.itm_parent)
                if parent_itm:
                    exo_name = parent_itm.itm_title or parent_itm.itm_code or "Exercice sans nom"

            exo_names.append(exo_name)

            avg_score = question_totals[qst.qst_id] / total_students if total_students > 0 else 0.0
            percentage = round(avg_score * 100, 1)

            data.append(percentage)
            qst_ids.append(qst.qst_id)

        return fa.responses.JSONResponse({
            "labels": labels,
            "data": data,
            "qst_ids": qst_ids,
            "exo_names": exo_names
        })

@router.post("/stats/oper/tags-data")
def route_stats_tags_data(req: fa.Request) -> fa.Response:
    """
    AJAX route to send Tags success rates based on real database scores
    or simulated data in DEV_MODE.
    format: JSON
    """
    with context.Context(req) as ctx:

        DEV_MODE = False

        # --- DEV MODE TO TEST THE FRONTEND ---
        if DEV_MODE:
            noms_tags = [
                "Bases de données",
                "Algorithmique",
                "Réseau",
                "Programmation C",
                "Web",
                "Sécurité",
                "Mathématiques"
            ]
            labels = []
            data = []
            tag_ids = []

            for i, nom in enumerate(noms_tags):
                labels.append(nom)
                fake_percentage = round(random.uniform(25.0, 90.0), 1)
                data.append(fake_percentage)
                tag_ids.append(i + 1)

            return fa.responses.JSONResponse({
                "labels": labels,
                "data": data,
                "tag_ids": tag_ids
            })

        current_usr_id = session.usr_id(ctx)

        # getting all exams created by the teacher
        teacher_exams = ctx.dbs.query(tables.Exam).join(
            tables.Item, tables.Exam.exm_mcq == tables.Item.itm_id
        ).filter(
            tables.Item.itm_usr == current_usr_id
        ).all()

        if not teacher_exams:
            return fa.responses.JSONResponse({"labels": [], "data": [], "tag_ids": []})

        tag_stats: dict[int, list[float]] = {}
        tag_names: dict[int, str] = {}

        all_item_tags = ctx.dbs.query(tables.ItemTag).all()

        for exam in teacher_exams:
            submissions = ctx.dbs.query(tables.ExamSubmission).join(
                tables.Registration, tables.ExamSubmission.exs_registration == tables.Registration.reg_id
            ).filter(
                tables.Registration.reg_exam == exam.exm_id
            ).all()

            for sub in submissions:
                detailed_scores = queries.get_student_detailed_scores(ctx.dbs, exam.exm_mcq, sub.exs_id)

                for qst_id, score in detailed_scores.items():
                    # getting the item
                    item_obj = queries.get_item(ctx.dbs, qst_id)

                    # collecting all possible ids to test
                    ids_to_check = [qst_id]
                    if item_obj and item_obj.itm_parent:
                        ids_to_check.append(item_obj.itm_parent)

                    # searching tags from these ids
                    tags = []
                    for check_id in ids_to_check:
                        found_tags = queries.get_item_tags(ctx.dbs, check_id)
                        if found_tags:
                            tags.extend(found_tags)


                    for tag in tags:
                        if tag.tag_id not in tag_stats:
                            tag_stats[tag.tag_id] = [0.0, 0.0]
                            tag_names[tag.tag_id] = str(tag.tag_name)

                        tag_stats[tag.tag_id][0] += float(score)
                        tag_stats[tag.tag_id][1] += 1.0



        labels = []
        data = []
        tag_ids = []
        counts = []

        for tag_id, (total_score, count) in tag_stats.items():
            labels.append(tag_names[tag_id])
            avg_percent = round((total_score / count) * 100, 1) if count > 0 else 0.0
            data.append(avg_percent)
            tag_ids.append(tag_id)
            counts.append(int(count))

        return fa.responses.JSONResponse({
            "labels": labels,
            "data": data,
            "tag_ids": tag_ids,
            "counts": counts
        })