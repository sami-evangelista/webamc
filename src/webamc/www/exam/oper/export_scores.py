from pathlib import Path
import itertools
import io
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from webamc.www.all import *
from webamc.www.exam import util
from webamc.db import queries


ROW_PREFIX_COLS: list[types.txt_t] = [
    "col_desc_usr_name",
    "col_desc_usr_fst_name",
    "col_desc_usr_code",
    "base_score",
    "base_max"
]
USR_DATA_COLS = 3
COL_IDX_QUESTION_START = len(ROW_PREFIX_COLS)
ROTATED_CHAR_WIDTH = 4
CHAR_WIDTH_MULT = 1.6


def generate_excel_scores(ctx: context.Context, exm_id: int) -> fa.Response:

    # get exam data
    exam = util.get_exam(ctx, exm_id)[1]
    exam_result = list(queries.get_exam_result(ctx.dbs, exm_id))

    # init excel file
    wb = openpyxl.Workbook()
    ws = wb.active
    assert isinstance(ws, Worksheet)  # security check
    ws.title = lang.txt("base_scores")

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

    # list all questions that appeared in exam submissions
    questions = sorted(
        set(
            item
            for row in exam_result
            for item in (
                    list()
                    if row["sub_result"] is None
                    else row["sub_result"]["qst_answers"]
            )
        ),
        key=lambda item: str(item.itm_code)
    )
    fst_qst_col = get_column_letter(COL_IDX_QUESTION_START + 1)
    last_qst_col = get_column_letter(COL_IDX_QUESTION_START + len(questions))

    # title row
    ws.append([exam.exm_title])
    ws.merge_cells(
        start_row=1,
        start_column=1,
        end_row=1,
        end_column=len(ROW_PREFIX_COLS) + len(questions)
    )

    # header row
    headers = [lang.txt(t).title() for t in ROW_PREFIX_COLS]
    max_header_len = 0
    for item in questions:
        headers.append(str(item.itm_code))
        max_header_len = max(max_header_len, len(str(item.itm_code)))
    ws.append(headers)
    for row_idx in (1, 2):
        for col_idx, cell in enumerate(ws[row_idx], start=1):
            cell.font = header_font
            cell.fill = header_fill
            if col_idx > COL_IDX_QUESTION_START:
                cell.alignment = vertical_align
                letter = get_column_letter(col_idx)
                ws.column_dimensions[letter].width = ROTATED_CHAR_WIDTH
            else:
                cell.alignment = center_align

    for exm_row in exam_result:
        row_idx = ws.max_row + 1
        row: list[str | int] = [
            exm_row["usr"].usr_name.upper(),
            exm_row["usr"].usr_fst_name.title(),
            exm_row["usr"].usr_code.title()
        ]
        if exm_row["sub_result"] is not None:
            items = exm_row["sub_result"]["items"]
            max_score = exm_row["sub_result"]["max_score"]
            qst_answers = exm_row["sub_result"]["qst_answers"]
            score = exm_row["sub_result"]["score"]
            exm_score = max_score[
                next(i for i in max_score if i.itm_id == exam.exm_mcq)
            ]
            row.append(f"=SUM({fst_qst_col}{row_idx}:{last_qst_col}{row_idx})")
            row.append(exm_score)
        else:
            items = set()
            max_score = dict()
            score = dict()
            qst_answers = dict()
            row.append(lang.txt("exam_usr_status_absent"))
            row.append("")
        for qst in questions:
            if qst in score and len(qst_answers[qst]) > 0:
                row.append(score[qst])
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
            if qst in items and len(qst_answers[qst]) == 0:
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

    filename = lang.txt("base_scores") + "-" + exam.exm_title.replace(" ", "_")
    headers_response = {
        "Content-Disposition":
        f"attachment; filename=\"{filename}.xlsx\""
    }
    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    return fa.Response(
        content=stream.read(),
        media_type=mtype.get_mtype(Path(f"{filename}.xlsx")),
        headers=headers_response
    )
