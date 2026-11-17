from webamc.db import tables, queries
from webamc.www.all import *


def gen_mcq_content(
        ctx: context.Context,
        item: tables.Item
) -> types.mcq_content_t:
    def loop(item: tables.Item) -> types.mcq_content_t:

        assert item.itm_type != types.ITEM_TYPE_CHOICE
        result: types.mcq_content_t

        # get an instance of this item
        instances = list(queries.get_item_instances(ctx.dbs, item.itm_id))
        assert len(instances) > 0
        inst = random.choice(instances)

        # question type
        if item.itm_type == types.ITEM_TYPE_QUESTION:
            qsts.add(item.itm_id)
            result = {
                "itm_id": item.itm_id,
                "itm_type": types.ITEM_TYPE_QUESTION,
                "itm_qst_type": item.itm_qst_type,
                "iti_id": inst.iti_id,
                "iti_num": inst.iti_num,
                "children": None
            }

        # pack type
        elif item.itm_type == types.ITEM_TYPE_PACK:
            packs[item] = list()
            result = {
                "itm_id": item.itm_id,
                "itm_type": types.ITEM_TYPE_PACK,
                "itm_qst_type": item.itm_qst_type,
                "iti_id": inst.iti_id,
                "iti_num": inst.iti_num,
                "children": packs[item]
            }

        # mcq or exercise type
        else:
            children = [
                loop(child) for child in queries.get_children(
                    ctx.dbs, item.itm_id
                )
            ]
            if item.itm_rnd:
                random.shuffle(children)
            result = {
                "itm_id": item.itm_id,
                "itm_type": types.ITEM_TYPE_EXERCISE,
                "itm_qst_type": item.itm_qst_type,
                "iti_id": inst.iti_id,
                "iti_num": inst.iti_num,
                "children": children
            }

        return result

    packs: dict[tables.Item, list[types.mcq_content_t]] = dict()
    qsts: set[int] = set()
    result = loop(item)

    # packs
    for item_pack, pack_content in packs.items():
        for item_qst in queries.gen_pack_questions(
                ctx.dbs, item_pack, session.usr_id(ctx), qsts
        ):
            instances = list(
                queries.get_item_instances(ctx.dbs, item_qst.itm_id)
            )
            assert len(instances) > 0
            inst = random.choice(instances)

            pack_content.append({
                "itm_id": item_qst.itm_id,
                "itm_type": types.ITEM_TYPE_QUESTION,
                "itm_qst_type": item.itm_qst_type,
                "iti_num": inst.iti_num,
                "iti_id": inst.iti_id,
                "children": None
            })
            qsts.add(item_qst.itm_id)

    return result
