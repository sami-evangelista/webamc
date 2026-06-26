from webamc.www.all import *
from webamc.db import queries, tables
from .model.args_graph_t import args_graph_t

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