#!/usr/bin/env python3

from webamc.www.all import *
from webamc.db import tables
from webamc.www.mcq import router


def data(
        ctx: context.Context,
        mcq_result: router.args_mcq_result_t
) -> fa.Response:
    session.check_can_view_mcq(ctx, mcq_result["mcq_id"])

    mcq_id = mcq_result["mcq_id"]
    corr: dict[tp.Literal["cho", "qst"], dict[int, bool]] = {
        "cho": dict(),
        "qst": dict()
    }
    for cho_id, cho_checked in mcq_result["mcq_choices"].items():
        row = ctx.dbs.query(
            tables.Choice,
            tables.Item
        ).where(
            (tables.Choice.cho_id == int(cho_id))
            & (tables.Choice.cho_id == tables.Item.itm_id)
        ).first()
        assert row is not None
        choice, item = row.tuple()
        cho_correct = bool(choice.cho_correct)
        assert item.itm_parent is not None
        qst_id = int(item.itm_parent)
        correct = cho_checked == cho_correct
        corr["qst"].setdefault(qst_id, True)
        corr["cho"][cho_id] = correct
        corr["qst"][qst_id] = corr["qst"][qst_id] and correct
    response = {
        "success": True,
        "msgs": list(),
        "result": corr
    }
    return fa.responses.JSONResponse(response)
