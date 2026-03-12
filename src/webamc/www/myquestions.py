#!/usr/bin/env python3
# pylint: disable-all

"""
from sqlalchemy.orm import aliased

from webamc import *
from webamc.actions import compile
from webamc.db import op, tables
from . import html_elements as he, base, db, auth, filter


def gen_questions_page(questions: dict) -> types.http_response_t:
    h1 = he.H1("Mes questions", class_="text-2xl font-bold mb-4")
    tags = filters.get_all_tags()
    tags_html = he.Select(
        *[he.Option(tag["tag_name"], value=tag["tag_name"]) for tag in tags],
        id_="filter-tag",
        class_= "w-full p-2 border rounded"
    )

    questionsElementList = he.ElementList()
    filter_button = he.Button(
        "Filtrer",
        onclick="toggleFilterOptions()",
        class_= "px-4 py-2 bg-blue-600 text-white rounded shadow-md mb-4"
    )
    select_button = he.Button(
        "Selectionner",
        onclick="toggleSelectMode()",
        id_="select-btn",
        class_= "px-4 py-2 bg-purple-600 text-white rounded shadow-md mb-4"
    )
    filter_div = he.Div(
        he.Label("Filtrer par :", class_= "block font-semibold mb-2"),
        he.Div(
            he.Label(
                he.Input(
                    type="radio", name="filter-type", value="tag", checked=True,
                    onclick="toggleFilterType('tag')"
                ),
                "Tag",
                class_= "mr-4 cursor-pointer"
            ),
            he.Label(
                he.Input(
                    type="radio", name="filter-type", value="code",
                    onclick="toggleFilterType('code')"
                ),
                "Code",
                class_= "cursor-pointer"
            ),
            class_= "flex items-center mb-4"
        ),
        he.Div(
            he.Label("Choisissez un tag :", class_= "block font-semibold mb-1"),
            tags_html,
            id_="filter-tag-container"
        ),
        he.Div(
            he.Label("Entrez un code :", class_= "block font-semibold mb-1"),
            he.Input(
                type="text",
                id_="filter-code",
                class_= "w-full p-2 border rounded"
            ),
            id_="filter-code-container",
            style="display: none;"
        ),
        he.Button(
            "Appliquer le filtre",
            onclick="applyFilter()",
            class_= "mt-4 px-4 py-2 bg-green-500 text-white rounded"
        ),
        he.Button(
            "Retirer le filtre",
            onclick="removeFilter()",
            id_="remove-filter-btn",
            class_= "mt-4 px-4 py-2 bg-red-500 text-white rounded disabled:bg-gray-500"
        ),
        id_="filter-options",
        class_= "bg-gray-100 p-4 mb-5 rounded-lg shadow hidden"
    )

    select_options_div = he.Div(
        he.Button(
            "Tout séléctionner",
            title="Séléctionner toute les réponses",
            onclick="toggleSelectAll()",
            id_="select-all-btn",
            class_= "bg-gray-500 text-white px-3 py-1 rounded-full text-sm mr-3 ml-3"
        ),
        he.Button(
            "Modifier le barème",
            title="Modifier le barème pour toute les questions séléctionnées",
            onclick="editPoints()",
            class_= "bg-gray-500 text-white px-3 py-1 rounded-full text-sm mr-3 ml-3"
        ),
        he.Hr(class_= "mt-3 border-blue-400"),
        id_="select-options-div",
        class_= "flex justify-end p-3  rounded-lg shadow-md w-40 hidden mb-5 w-full"
    )

    qst_number = 1
    for qst_id, values in questions.items():
        answers = values["answers"]
        qst = values["qst"]
        tags = values["tags"]
        answersElementList = he.ElementList()
        for ans in answers:
            answer = he.Div(
                he.Input(
                    type="checkbox",
                    class_="hidden select-item-input select-answer-input accent-green-500",
                    onclick="toggleSelect(this)"
                ),
                he.Div(
                    he.Div(
                        he.Img(src=base.img_src(ans["ans_id"])),
                        class_=f"p-2 rounded {'bg-green-200' if ans['ans_correct'] else 'bg-red-200'}"
                    ),
                    he.Div(
                        he.Div(
                            he.Label("Points +", class_= "text-sm"),
                            he.Input(
                                type="number",
                                value=f"{ans['ans_pos_point']}",
                                id_=f"input-ans-pos-{ans['ans_id']}",
                                class_= "w-12 p-1 border rounded text-center input-ans-point"
                            )
                        ),
                        he.Div(
                            he.Label("Points -", class_= "text-sm"),
                            he.Input(
                                type="number",
                                value=f"{ans['ans_neg_point']}",
                                id_=f"input-ans-neg-{ans['ans_id']}",
                                class_= "w-12 p-1 border rounded text-center input-ans-point"
                            )
                        ),
                        class_= "flex items-center space-x-4"
                    ),
                    class_="flex justify-between items-center p-2 bg-gray-100 mt-1 rounded-md w-full colored-bg-div" 
                ),
                class_="flex flex-row items-center w-full space-x-2 answer-div", **{"data-val":str(ans["ans_correct"]).lower()}
            )
            answersElementList.append(answer)
        ans_div = he.Div(    
            answersElementList,
            id_=f"reponses-{qst_id}",
            class_="hidden mt-2"
        )
        question = he.Div(
            he.Div(
                he.Input(
                    type_="checkbox",
                    class_="hidden select-checkbox select-item-input select-question-input accent-green-500",
                    onclick_="toggleQuestionSelection(this)"
                ),
                he.Button(
                    f"Question {qst_number} : {qst['qst_code']}",
                    he.Img(src=base.img_src(qst_id)),
                    onclick=f"toggleReponses({qst_id})",
                    class_="w-full text-left font-semibold text-lg bg-gray-200 p-2 rounded-md colored-bg-div"
                ),
                class_= "flex items-center gap-2"
            ),
            ans_div,
            class_="border-b border-gray-300 pb-4 mb-4 questions-list-div",
            **{
                "data-qst-code": f"{qst['qst_code']}",
                "data-tags": f"{format_tags_for_div(tags)}"
            }
        )
        questionsElementList.append(question)
        qst_number += 1

    button_save = he.Button(
        "Sauvegarder",
        id_="save_button",
        title="Sauvegarder vos modifications",
        onclick="save_answers_points()",
        class_="px-4 py-2 bg-red-500 text-white rounded disabled:border-[#999999] mb-4 ml-auto"
    )
    main_div = he.Div(
        h1,
        he.Div(
            select_button,
            filter_button,
            button_save,
            class_= "flex justify-end items-center space-x-4"
        ),
        filter_div,
        select_options_div,
        he.Div(
            questionsElementList,
            id_="questions-list-container"
        ),
        class_= "bg-white p-6 rounded-lg shadow-md"
    )

    script = he.Script(src="https://cdn.tailwindcss.com")
    script2 = he.Script(src="https://cdn.jsdelivr.net/npm/sweetalert2@11")
    script3 = he.Script("initData()");
    elements = he.ElementList(
        main_div,
        script,
        script2,
        script3,
    )
    return base.html("", elements, attr={"class":"p-6"})


def get_all_user_questions(usr_id: int) -> list[tp.Dict[str, tp.Any]]:
    ItemQuestion = aliased(tables.Item)
    ItemAnswer = aliased(tables.Item)
    stmt = op.select(
        ItemQuestion.itm_id.label("qst_id"),
        ItemQuestion.itm_code.label("qst_code"),
        ItemAnswer.itm_id.label("ans_id"),
        tables.Answer.ans_correct.label("ans_correct"),
        tables.Answer.ans_pos_point.label("ans_pos_point"),
        tables.Answer.ans_neg_point.label("ans_neg_point"),
        tables.Tag.tag_id,
        tables.Tag.tag_name,
    ).join(
        tables.Question, tables.Question.qst_id == ItemQuestion.itm_id
    ).join(
        ItemAnswer, ItemQuestion.itm_id == ItemAnswer.itm_parent
    ).join(
        tables.Answer, ItemAnswer.itm_id == tables.Answer.ans_id
    ).join(
        tables.Usr, tables.Usr.usr_id == ItemQuestion.itm_usr
    ).join(
        tables.ItemTag, tables.ItemTag.itg_item == ItemQuestion.itm_id,
    ).join(
        tables.Tag, tables.Tag.tag_id == tables.ItemTag.itg_tag
    ).where(
        tables.Usr.usr_id == usr_id
    )
    return [
        {
            "qst_id": row[0],
            "qst_code":row[1],
            "ans_id": row[2],
            "ans_correct": row[3],
            "ans_pos_point": row[4],
            "ans_neg_point": row[5],
            "tag_id":row[6],
            "tag_name":row[7],
        }
        for row in op.execute(stmt).all()
    ]


def get_structured_questions(query: dict) -> dict:
    structured_dict = {}
    for result in query:
        question_id = result["qst_id"]
        tag_id = result["tag_id"]
        qst_code = result["qst_code"];
        response = {
            "ans_id": result["ans_id"],
            "ans_correct": result["ans_correct"],
            "ans_pos_point": result["ans_pos_point"],
            "ans_neg_point": result["ans_neg_point"],
        }
        if question_id not in structured_dict:
            structured_dict[question_id] = {"qst":{}, "tags":{}, "answers":[]}
        if tag_id not in structured_dict[question_id]["tags"]:
            structured_dict[question_id]["tags"][tag_id] = {
                "tag_name": result["tag_name"]
            }
        if qst_code not in structured_dict[question_id]["qst"]:
            structured_dict[question_id]["qst"] = {"qst_code":qst_code}
        structured_dict[question_id]["answers"].append(response) 
    return structured_dict


def format_tags_for_div(tag_dict: dict) -> str:
    str = ""
    for tag_id, tag in tag_dict.items():
        str += tag["tag_name"]+","
    str = str[:len(str)-1]
    return str


def save_answers(ans_point: dict[int, dict[str, int]]) -> bool:
    if ans_point == dict():
        return False  
    case_pos = sa.case(
        {int(id): int(ans["pos_point"]) for id, ans in ans_point.items()},
        value=tables.Answer.ans_id
    )
    case_neg = sa.case(
        {int(id): int(ans["neg_point"]) for id, ans in ans_point.items()},
        value=tables.Answer.ans_id
    )
    stmt = op.update(tables.Answer).where(
        tables.Answer.ans_id.in_([int(id) for id in ans_point.keys()])
    ).values(
        ans_pos_point=case_pos,
        ans_neg_point=case_neg
    )
    op.execute(stmt)
    op.commit()
    return True
"""
