import io
import typing as tp

import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.formatting.rule import FormulaRule
from fastapi.responses import Response

from webamc.www.all import context
from webamc.db import queries, tables


def generate_excel_scores(ctx: context.Context, exam_id: int) -> Response:

    # getting global data from exam
    monitoring_data = queries.get_exam_monitoring(ctx.dbs, exam_id)
    if not monitoring_data:
        return Response(content="Can't find exam", status_code=404)

    # get real mcq_id
    exam = ctx.dbs.query(tables.Exam).filter_by(exm_id=exam_id).first()
    if not exam:
        return Response(content="Can't find exam", status_code=404)
    mcq_id = exam.exm_mcq

    # init excel file
    wb = openpyxl.Workbook()
    ws = wb.active
    assert isinstance(ws, Worksheet) # security check
    ws.title = "Notes Examen"

    # styles
    grey_fill = PatternFill(
        start_color="D3D3D3", end_color="D3D3D3", fill_type="solid"
    )
    red_fill = PatternFill(
        start_color="FFCCCC", end_color="FFCCCC", fill_type="solid"
    )
    bold_font = Font(bold=True)
    vertical_align = Alignment(
        textRotation=90, horizontal="center", vertical="bottom"
    )
    center_align = Alignment(horizontal="center", vertical="center")

    students = monitoring_data["students"]

    # get all questions from db
    direct_items = ctx.dbs.query(
        tables.Item.itm_id
    ).filter(
        tables.Item.itm_parent == mcq_id
    ).all()
    parent_ids = [mcq_id] + [item.itm_id for item in direct_items]

    questions_data = ctx.dbs.query(
        tables.Question.qst_id,
        tables.Item.itm_code
    ).join(
        tables.Item, tables.Question.qst_id == tables.Item.itm_id
    ).filter(
        tables.Item.itm_parent.in_(parent_ids)
    ).all()

    # pre-calculate stats
    student_records: list[dict[str, tp.Any]] = []

    for student in students:
        is_absent = student["status"] == "not started"

        sub_id = None
        if not is_absent:
            exam_sub = ctx.dbs.query(
                tables.ExamSubmission
            ).filter_by(
                exs_registration=student["reg_id"]
            ).first()
            if exam_sub:
                sub_id = exam_sub.exs_id

        if sub_id is None:
            scores_dict = dict()
        else:
            scores_dict = queries.get_student_detailed_scores(
                ctx.dbs, mcq_id, sub_id
            )

        # save data for later
        student_records.append({
            "data": student,
            "is_absent": is_absent,
            "scores": scores_dict
        })

    # calculate statistics fields
    total_questions = len(questions_data)

    # sort students alphabetically
    student_records.sort(key=lambda x: (
        (x["data"]["usr_name"] or "").lower(),
        (x["data"]["usr_fst_name"] or "").lower()
    ))

    # write row 1: headers
    headers = ["Nom", "Prénom", "Login", "Note", "Max"]
    max_header_len = 0
    for _, itm_code in questions_data:
        code_str = str(itm_code)
        headers.append(code_str)
        max_header_len = max(max_header_len, len(code_str))
    ws.append(headers)

    # auto-fit row height for vertical text
    ws.row_dimensions[1].height = max(40, max_header_len * 6)

    # compute boundaries for excel formulas
    last_row = 3 + len(student_records)
    last_col_letter = get_column_letter(5 + len(questions_data))

    # write row 2: max points row (using excel formula)
    row2 = [
        "", "", "Note Max", f"=MAX(D4:D{last_row})", float(total_questions)
    ]
    for _ in questions_data:
        row2.append(1.0)
    ws.append(row2)

    # write row 3: average row (using excel formulas for percentages)
    row3 = ["", "", "Moyenne", f"=AVERAGE(D4:D{last_row})", ""]
    for i in range(len(questions_data)):
        col_letter = get_column_letter(6 + i)
        # Excel AVERAGE ignores empty/text cells automatically!
        row3.append(f"=AVERAGE({col_letter}4:{col_letter}{last_row})")
    ws.append(row3)

    # format rows 1, 2 and 3
    for row_idx in [1, 2, 3]:
        for col_idx, cell in enumerate(ws[row_idx], start=1):
            cell.font = bold_font
            if row_idx == 1 and col_idx > 5:
                cell.alignment = vertical_align
            elif row_idx in [2, 3] and col_idx >= 4:
                cell.alignment = center_align

                # apply percentage format to success rates in row 3
                if row_idx == 3 and col_idx > 5:
                    cell.number_format = '0%'
                elif isinstance(cell.value, (int, float)):
                    cell.number_format = '0.0'

    # fill student rows
    for record in student_records:
        student = record["data"]
        is_absent = record["is_absent"]
        scores_dict = record["scores"]

        current_row = ws.max_row + 1

        # set sum formula instead of fixed score
        if is_absent:
            note_formula = "ABS"
        else:
            note_formula = f"{current_row}:{last_col_letter}{current_row}"
            note_formula = f"SUM(F{note_formula})"

        row_data = [
            student["usr_name"],
            student["usr_fst_name"],
            student["usr_login"],
            note_formula,
            float(student["total_questions"])
        ]

        # add 1 or 0 for questions
        for qst_id, _ in questions_data:
            if is_absent:
                row_data.append("")
            else:
                val = 1 if scores_dict.get(qst_id, 0.0) > 0 else 0
                row_data.append(val)

        ws.append(row_data)
        current_row = ws.max_row

        # center and format student cells (cols >= 4)
        for col_idx in range(4, len(row_data) + 1):
            cell = ws.cell(row=current_row, column=col_idx)
            cell.alignment = center_align
            # force float formatting display (.0)
            if isinstance(cell.value, (int, float)):
                cell.number_format = '0.0'

        # apply grey style only for absent students
        if is_absent:
            for col_idx in range(5, len(row_data) + 1):
                ws.cell(row=current_row, column=col_idx).fill = grey_fill

    # apply conditional formatting for incorrect/empty answers
    score_range = f"F4:{last_col_letter}{last_row}"

    # rule: if student is NOT absent (col D <> "ABS") AND cell is
    # empty or 0 => fill red
    red_rule = FormulaRule(
        formula=['AND($D4<>"ABS", OR(ISBLANK(F4), F4=0))'],
        stopIfTrue=True,
        fill=red_fill
    ) # type: ignore[no-untyped-call]
    ws.conditional_formatting.add(score_range, red_rule)

    # auto-fit columns
    for col_idx, col in enumerate(ws.columns, start=1):
        max_length = 0
        column_letter = get_column_letter(col_idx)

        for cell in col:
            try:
                # mypy checking
                cell_value = getattr(cell, "value", None)
                row_num = getattr(cell, "row", None)

                if cell_value is not None and row_num is not None:
                    if row_num in [2, 3] or (row_num == 1 and col_idx > 5):
                        continue
                    max_length = max(max_length, len(str(cell_value)))
            except:
                pass

        adjusted_width = max_length + 4
        if col_idx <= 5 and adjusted_width < 12:
            adjusted_width = 12
        if col_idx > 5 and adjusted_width < 6:
            adjusted_width = 6

        ws.column_dimensions[column_letter].width = adjusted_width

    # save and return response
    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    headers_response = {
        'Content-Disposition':
        f'attachment; filename="notes_examen_{exam_id}.xlsx"'
    }
    mtype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return Response(
        content=stream.read(),
        media_type=mtype,
        headers=headers_response
    )
