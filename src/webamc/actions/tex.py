import TexSoup  # type: ignore

from webamc.all import *


tex_err_code_t = tp.Literal[
    "success",
    "error_parse",
    "info_no_question"
]
tex_qst_t = tp.TypedDict(
    "tex_qst_t",
    {
        "result": tex_err_code_t,
        "qst_type": types.question_type_t,
        "itm_code": str,
        "question": TexSoup.TexNode,
        "choices": list[TexSoup.TexNode]
    },
    total=False
)
tex_result_t = tuple[tex_err_code_t, list[tex_qst_t]]
tex_error_msg: dict[tex_err_code_t, str] = {
    "success": "",
    "error_parse": "could not parse tex file",
    "info_no_question": "no question found"
}


def extract_qst(file_content: str) -> tex_result_t:
    cfg = config.CONFIG

    # parse the content
    soup: None | TexSoup.TexSoup
    try:
        soup = TexSoup.TexSoup(file_content)
    except:
        return "error_parse", list()

    # get questions
    qsts = list()
    
    # force question and questionmult environments
    env_questions = cfg.get("tex_envs_question", ["question"])
    if isinstance(env_questions, str):
        env_questions = [env_questions]
        
    if "questionmult" not in env_questions:
        env_questions.append("questionmult")

    all_tex_qsts = []
    for env in env_questions:
        all_tex_qsts.extend(soup.find_all(env))

    for tex_qst in all_tex_qsts:
        qst: tex_qst_t = dict()
        qst["itm_code"] = tex_qst.args[0].string
        
        # get question type
        env_mults = cfg.get("tex_envs_question_mult", ["questionmult"])
        if isinstance(env_mults, str):
            env_mults = [env_mults]
            
        qst["qst_type"] = (
            types.QUESTION_TYPE_MULTI
            if tex_qst.name in env_mults or tex_qst.name == "questionmult" else
            types.QUESTION_TYPE_SINGLE
        )

        # get choices inside the question
        tex_choices = tex_qst.find(cfg["tex_envs_choices"])
        
        # fallback on the whole document if not found directly
        if tex_choices is None:
            tex_choices = soup.find(cfg["tex_envs_choices"])

        if tex_choices is None:
            qst["choices"] = list()
        else:
            qst["choices"] = tex_choices.children
            tex_choices.delete()
            
        qst["question"] = tex_qst
        qsts.append(qst)

    return "success", qsts


def iter_on_choices(qst: tex_qst_t) -> tp.Iterator[tuple[bool, bool, str]]:
    """Generate all choices of the question.

    Yields (b, l, tex) for each choice in the question where b == True
    if and only if it is a correct choice and tex is the choice
    content and l == True if and only if the choice belongs to last
    choices.

    """
    cfg = config.CONFIG
    nodes = [
        n for n in qst["choices"] if (
            isinstance(n, TexSoup.data.TexNode)
            and n.name in (
                cfg["tex_macros_lastchoices"] + cfg["tex_macros_choice"]
            )
        )
    ]
    last = False
    for n in nodes:
        if n.name in cfg["tex_macros_lastchoices"]:
            last = True
        else:
            correct = n.name in cfg["tex_macros_choice_correct"]
            yield correct, last, "".join(str(x) for x in n.contents)


def qst_tex_header(qst: tex_qst_t) -> str:
    """Get the latex code of the question text (i.e., without the choices)."""
    return "".join(str(x) for x in qst["question"].contents[1:])
