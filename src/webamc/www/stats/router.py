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
            
            for i, cho in enumerate(choices):
                label = chr(65 + i) if i < 26 else str(i + 1)
                labels.append(f"Réponse {label}")
                
                count = random.randint(0, int(total_students / len(choices)))
                data.append(count)
                
                choices_info.append({
                    "letter": label,
                    "id": cho.cho_id,
                    "is_correct": cho.cho_correct 
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
                "is_correct": cho.cho_correct
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

        # building labels and calculating success percentage (0.0 to 1.0 -> 0% to 100%)
        # building labels and calculating success percentage
        for i, qst in enumerate(questions):
            # Récupération de l'Item pour avoir le itm_code
            itm = queries.get_item(ctx.dbs, qst.qst_id)
            
            # Si la question a un code, on l'utilise, sinon on met "Qst X" par sécurité
            label = str(itm.itm_code) if itm.itm_code else f"Qst {i+1}"
            labels.append(label)
            
            avg_score = question_totals[qst.qst_id] / total_students if total_students > 0 else 0.0
            percentage = round(avg_score * 100, 1)
            
            data.append(percentage)
            qst_ids.append(qst.qst_id)
            
        return fa.responses.JSONResponse({
            "labels": labels,
            "data": data,
            "qst_ids": qst_ids
        })