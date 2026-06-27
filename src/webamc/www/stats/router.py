from webamc.www.all import *
from webamc.db import queries, tables
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

        # getting all possible choices for this question
        # using the existing function from queries.py
        choices = queries.get_question_choices(ctx.dbs, qst_id)
        
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
            ).filter(
                tables.ItemInstance.iti_item == cho.cho_id
            ).count()
            
            data.append(count)
            
            choices_info.append({
                "letter": label,
                "id": cho.cho_id
            })
            
        if not labels:
            labels = ["Aucune donnée"]
            data = [0]
            
        return fa.responses.JSONResponse({
            "labels": labels,
            "data": data,
            "choices_info": choices_info 
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
            tables.Exam, tables.ExamSubmission.exs_id== tables.Exam.exm_id
        ).filter(
            tables.ExamSubmission.exs_registration == args.student_id,
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
            
            print(f"DEBUG: Score pour {sub.exs_id} : {detailed_scores}")
            
            total_score = sum(detailed_scores.values()) if detailed_scores else 0.0
            
            data.append(float(total_score))

        if not labels:
            labels = ["Aucun test passé"]
            data = [0]

        return fa.responses.JSONResponse({
            "labels": labels,
            "data": data
        })

