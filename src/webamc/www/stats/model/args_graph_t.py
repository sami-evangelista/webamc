from pydantic import BaseModel

class args_graph_t(BaseModel):
    qst_id: int
    exam_id: int
