#!/usr/bin/env python3

import zipfile
import tempfile
import os
import json
import typing as tp
from sqlalchemy.orm import Session as ORMSession

from webamc.all import *
from webamc.db import tables, op
from webamc.util import io
from . import output, compile as comp


def _load_dir(dir_path: str, usr_id: int) -> None:
    def load_item(dbs: ORMSession, item: comp.item_t) -> None | int:
        def sub_dict(prefix: str) -> dict[str, tp.Any]:
            return {
                key: val
                for (key, val) in item.items()
                if key.startswith(prefix)
            }
        
        if "itm_parent" in item:
            if item["itm_parent"] not in num_map:
                return None
            item["itm_parent"] = num_map[item["itm_parent"]]
        
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

        item["itm_standalone"] = (
            item.get("itm_standalone", False) or "itm_parent" not in item
        )
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

        # new item (Le Moule)
        info = f"{tex_file}: new item {itm_code}"
        db_item = tables.Item(**sub_dict("itm_"))
        dbs.add(db_item)
        dbs.flush()
        dbs.refresh(db_item)
        output.info(info)
        result = int(db_item.itm_id)

        # if it is an mcq we insert an mcq and records
        if item.get("is_mcq", False):
            info = f"{tex_file}: new mcq {itm_code}"
            mcq = tables.Mcq(mcq_id=result)
            dbs.add(mcq)
            output.info(info)

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
        if itm_code is not None:
            desc += " " + itm_code
        info = f"{tex_file}: new {desc}"
        dbs.add(tbl(**val))
        output.info(info)
        
        # inserting instance from JSON in database
        instances = item.get("instances", [])
        for inst in instances:
            img_path = os.path.join(dir_path, inst["png"])
            
            # png image checking
            if not os.path.isfile(img_path):
                output.warning(f"{tex_file} (Instance {inst['iti_num']}): " + \
                "no image file found at {img_path}")
                img_bin = None
            else:
                img_bin = io.read_bin_file_content(img_path)
            
            # ItemInstance object creation and added to db
            db_instance = tables.ItemInstance(
                iti_item=result,             # parent id
                iti_num=inst["iti_num"],     # instance num
                iti_seed=inst["iti_seed"],   # seed used
                iti_img=img_bin              # png
            )
            dbs.add(db_instance)
            output.info(f"{tex_file}: added instance {inst['iti_num']} for item {result}")

        return result

    num_map: dict[int, int] = dict()
    json_file = os.path.join(dir_path, comp.JSON_SPEC)
    if os.path.isfile(json_file):
        with (
            open(json_file, encoding="utf-8") as fd,
            op.Session() as dbs,
            dbs.begin()
        ):
            items: list[comp.item_t] = tp.cast(
                list[comp.item_t], json.loads(fd.read())
            )
            for item in items:
                itm_id = load_item(dbs, item)
                if itm_id is not None:
                    num_map[item["num"]] = itm_id

def action(archive: str, usr_id: int) -> None:
    if not os.path.isfile(archive):
        output.error(f"invalid argument: {archive}")
    else:
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                with zipfile.ZipFile(archive) as zf:
                    zf.extractall(path=tmp_dir)
                if not os.path.isdir(tmp_dir):
                    output.error("invalid archive file !")
                else:
                    _load_dir(tmp_dir, usr_id)
            except zipfile.BadZipFile:
                output.error("not a zip file !")