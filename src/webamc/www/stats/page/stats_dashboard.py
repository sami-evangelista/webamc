from webamc.www.all import *
from webamc.db import tables, queries
from webamc.util import fmt
from webamc.www.stats import router


def page(ctx: context.Context, exam_id: int) -> he.Element:
    """
    Generate statis for a given exam
    """
    content = he.Div(he.Str(f"Statistiques de l'examen {exam_id}"))
    
    return base.page(ctx, "Statistiques", content)