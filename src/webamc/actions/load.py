import zipfile
import tempfile
import json
import typing as tp
from pathlib import Path
from sqlalchemy.orm import Session as ORMSession
import typeguard

from webamc.all import *
from webamc.db import tables, op
from . import output, compile as comp


def _load_dir(dir_path: Path, usr_id: int) -> None:
    def load_item(dbs: ORMSession, item: comp.item_t) -> None | int:
        def sub_dict(prefix: str) -> dict[str, tp.Any]:
            return {
                key: val
                for (key, val) in item.items()
                if key.startswith(prefix)
            }

        if "parent" in item:
            if item["parent"] not in num_map:
                return None
            item["parent"] = num_map[item["parent"]]

        tex_file = item.get("tex_file")

        result = None

        # check a CODE is provided if it is not a choice
        itm_code = item.get("itm_code")
        if (
                itm_code is None
                and item["itm_type"] != types.ITEM_TYPE_CHOICE
        ):
            output.warning(f"{tex_file}: no CODE provided in item")
            return None

        item["itm_usr"] = usr_id

        # duplicate detection
        if itm_code is not None:
            query = dbs.query(
                tables.Item
            ).where(
                (tables.Item.itm_code == itm_code)
                & (tables.Item.itm_usr == usr_id)
            )
            if query.first() is not None:
                output.warning(f"{tex_file}: duplicate item {itm_code}")
                return None

        # new item
        db_item = tables.Item(**sub_dict("itm_"))
        dbs.add(db_item)
        dbs.flush()
        dbs.refresh(db_item)
        result = int(db_item.itm_id)

        # insertion in item_relation
        if "parent" in item:
            db_item_relation = tables.ItemRelation(
                itr_child=result,
                itr_parent=item["parent"],
                itr_order=item["order"]
            )
            dbs.add(db_item_relation)

        # if it is an mcq we insert an mcq and records
        is_mcq = item.get("is_mcq", False)
        if is_mcq:
            mcq = tables.Mcq(mcq_id=result)
            dbs.add(mcq)

        # if it is not a choice we insert item_tag records
        if item["itm_type"] != types.ITEM_TYPE_CHOICE:
            for tag in item.get("tags", list()):
                row = dbs.query(
                    tables.Tag.tag_id
                ).where(
                    tables.Tag.tag_name == tag
                ).first()
                if row is None:
                    output.warning(f"{tex_file}: undefined tag {tag}")
                    continue
                info = f"{tex_file}: new item_tag ({itm_code}, {tag})"
                item_tag = tables.ItemTag(itg_tag=row.tag_id, itg_item=result)
                dbs.add(item_tag)
                output.info(info)

        # insert in the appropriate item sub-table
        val: dict[str, tp.Any] = dict()
        desc, tbl, prefix = {
            types.ITEM_TYPE_CHOICE: ("choice", tables.Choice, "cho_"),
            types.ITEM_TYPE_EXERCISE: ("exercise", tables.Exercise, "exe_"),
            types.ITEM_TYPE_QUESTION: ("question", tables.Question, "qst_"),
            types.ITEM_TYPE_PACK: ("pack", tables.Pack, "pak_")
        }[item["itm_type"]]
        val = {
            prefix + "id": result,
            **sub_dict(prefix)
        }
        if is_mcq:
            desc = "mcq"
        if itm_code is not None:
            desc += " " + itm_code
        info = f"{tex_file}: new {desc}"
        dbs.add(tbl(**val))
        output.info(info)

        # inserting instance from JSON in database
        for inst in item.get("instances", list()):
            img_path = dir_path / inst["png"]

            # png image checking
            if not img_path.is_file():
                output.warning(f"{tex_file} no image found")
                img_bin = None
            else:
                img_bin = Path(img_path).read_bytes()

            # ItemInstance object creation and added to db
            db_instance = tables.ItemInstance(
                iti_item=result,             # parent id
                iti_num=inst["iti_num"],     # instance num
                iti_seed=inst["iti_seed"],   # seed used
                iti_img=img_bin              # png
            )
            dbs.add(db_instance)
            output.info(
                f"{tex_file}: new instance {inst['iti_num']} "
                f"of {desc}"
            )

        return result

    num_map: dict[int, int] = dict()
    json_file = dir_path / comp.JSON_SPEC
    if json_file.is_file():
        items: list[comp.item_t] = typeguard.check_type(
            json.loads(json_file.read_text()), list[comp.item_t]
        )
        with op.Session() as dbs, dbs.begin():
            for item in items:
                itm_id = load_item(dbs, item)
                if itm_id is not None:
                    num_map[item["num"]] = itm_id


def action(archive: str, usr_id: int) -> None:
    if not Path(archive).is_file():
        output.error(f"invalid argument: {archive}")
    else:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir)
            try:
                with zipfile.ZipFile(archive) as zf:
                    zf.extractall(path=path)
                if not path.is_dir():
                    output.error("invalid archive file !")
                else:
                    _load_dir(path, usr_id)
            except zipfile.BadZipFile:
                output.error("not a zip file !")
