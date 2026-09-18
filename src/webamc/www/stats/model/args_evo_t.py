import pydantic

class args_evo_t(pydantic.BaseModel):
    student_id: int
    mcq_id: int
