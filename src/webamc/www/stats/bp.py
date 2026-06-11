#!/usr/bin/env python3
# pylint: disable-all

"""Provide a Blueprint with routes of the stat module.

This corresponds to all routes starting with /stat.

"""

"""
@route("/stats", GET)
def get_stats():
    "Route to show statistics of student's fa.responses for each tag"
    usr_id = session.usr_id()

    # Requête pour récupérer les statistiques
    stats = op.session.query(
        tables.Tag.tag_name,
        func.count().label("total"),
        func.sum(case([(tables.StudentResponse.res_ans == tables.Answer.ans_id, 1)], else_=0)).label("correct"),
        func.count(tables.StudentResponse.res_ans).label("incorrect")  # all answers
    ).join(tables.ItemTag, tables.Tag.tag_id == tables.ItemTag.itg_tag) \
     .join(tables.StudentResponse, tables.StudentResponse.res_qst == tables.ItemTag.itg_item) \
     .join(tables.Answer, tables.StudentResponse.res_ans == tables.Answer.ans_id) \
     .filter(tables.StudentResponse.res_usr == usr_id) \
     .group_by(tables.Tag.tag_name).all()

    result = [
        {
            "tag": tag,
            "correct": correct or 0,
            "incorrect": total - correct or 0  # wrong answers
        }
        for tag, total, correct in stats
    ]

    # Retourner la page des statistiques avec les données du camembert
    return generate_stats_page(result)
"""

