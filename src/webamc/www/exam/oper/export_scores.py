import itertools
import io
import typing as tp
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.formatting.rule import FormulaRule

from webamc.www.all import *
from webamc.db import queries, tables


ROW_PREFIX_COLS: list[types.txt_t] = [
    "col_desc_usr_name",
    "col_desc_usr_fst_name",
    "col_desc_usr_code",
    "word_score"
]
USR_DATA_COLS = 3
COL_IDX_QUESTION_START = len(ROW_PREFIX_COLS)
ROTATED_CHAR_WIDTH = 4
CHAR_WIDTH_MULT = 1.6


def generate_excel_scores(ctx: context.Context, exm_id: int) -> fa.Response:

    # init excel file
    wb = openpyxl.Workbook()
    ws = wb.active
    assert isinstance(ws, Worksheet)  # security check
    ws.title = "Notes Examen"

    # styles
    header_font = Font(
        bold=True
    )
    header_fill = PatternFill(  # light blue
        start_color="CCCCFF",
        end_color="CCCCFF",
        fill_type="solid"
    )
    absent_fill = PatternFill(  # grey
        start_color="DDDDDD",
        end_color="DDDDDD",
        fill_type="solid"
    )
    no_answer_fill = PatternFill(  # yellow
        start_color="FFFF88",
        end_color="FFFF88",
        fill_type="solid"
    )
    usr_data_fill = PatternFill(  # rose salmon
        start_color="FEDCD0",
        end_color="FEDCD0",
        fill_type="solid"
    )
    vertical_align = Alignment(
        textRotation=90,
        horizontal="center",
        vertical="bottom"
    )
    center_align = Alignment(
        horizontal="center",
        vertical="bottom"
    )
    thin_border = Border(
        left=Side(style="thin"), 
        right=Side(style="thin"), 
        top=Side(style="thin"), 
        bottom=Side(style="thin")
    )

    exam_result = list(queries.get_exam_result(ctx.dbs, exm_id))

    # list all questions
    questions = sorted(
        set(item for row in exam_result for item in row[3]),
        key=lambda item: str(item.itm_code)
    )
    fst_qst_col = get_column_letter(COL_IDX_QUESTION_START + 1)
    last_qst_col = get_column_letter(COL_IDX_QUESTION_START + len(questions))

    # header row
    headers = [lang.txt(t).title() for t in ROW_PREFIX_COLS]
    max_header_len = 0
    for item in questions:
        headers.append(str(item.itm_code))
        max_header_len = max(max_header_len, len(str(item.itm_code)))
    ws.append(headers)
    for col_idx, cell in enumerate(ws[1], start=1):
        cell.font = header_font
        cell.fill = header_fill
        if col_idx > COL_IDX_QUESTION_START:
            cell.alignment = vertical_align
            letter = get_column_letter(col_idx)
            ws.column_dimensions[letter].width = ROTATED_CHAR_WIDTH
        else:
            cell.alignment = center_align

    for usr, sub, items, qst_answers, qst_scores in exam_result:
        is_absent = sub is None
        row_idx = ws.max_row + 1
        row: list[str | int] = [
            usr.usr_name.upper(),
            usr.usr_fst_name.title(),
            usr.usr_code.title()
        ]
        score = sum(qst_scores.get(qst, 0) for qst in questions)
        if is_absent:
            row.append("")
        else:
            row.append(
                f"=SUM({fst_qst_col}{row_idx}:{last_qst_col}{row_idx})"
            )
        for qst in questions:
            if qst in qst_scores:
                row.append(max(qst_scores[qst], 0))
            else:
                row.append("")
        ws.append(row)

        # color cells containing user informations (name, ...)
        for col_idx in range(1, USR_DATA_COLS + 1):
            ws.cell(row=row_idx, column=col_idx).fill = usr_data_fill

        # color cells of questions that the user did not have (either
        # the user is absent or the question did not appear)
        for i, qst in enumerate(questions, start=1):
            col_idx = i + COL_IDX_QUESTION_START
            if qst not in items:
                ws.cell(row=row_idx, column=col_idx).fill = absent_fill

        # color cells of questions that the user did have but did not
        # answer
        for i, qst in enumerate(questions, start=1):
            col_idx = i + COL_IDX_QUESTION_START
            if qst in items and qst not in qst_scores:
                ws.cell(row=row_idx, column=col_idx).fill = no_answer_fill

    # adjust column widths containing names, first name, ...
    for col_idx in range(1, USR_DATA_COLS + 1):
        max_length = 0
        for row_idx in range(1, ws.max_row + 1):
            cell_value = ws.cell(row=row_idx, column=col_idx).value
            max_length = max(max_length, len(str(cell_value)))
        letter = get_column_letter(col_idx)
        ws.column_dimensions[letter].width = max_length * CHAR_WIDTH_MULT

    for col_idx, row_idx in itertools.product(
            range(1, ws.max_column + 1),
            range(1, ws.max_row + 1)
    ):
        ws.cell(row=row_idx, column=col_idx).border = thin_border

    """

    # calculate statistics fields
    total_questions = len(questions_data)

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

    # apply conditional formatting for incorrect/empty answers
    score_range = f"F4:{last_col_letter}{last_row}"
"""
    headers_response = {
        'Content-Disposition':
        f'attachment; filename="notes_examen_{exm_id}.xlsx"'
    }
    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    mtype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return fa.Response(
        content=stream.read(),
        media_type=mtype,
        headers=headers_response
    )
