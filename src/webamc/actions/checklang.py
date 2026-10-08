import re
from importlib import resources

from webamc.all import *
from webamc.util import termout


def action() -> None:
    for lg in types.literal_type_values(types.lang_t):
        err = False
        config.CONFIG["lang"] = lg
        lang.reset()
        for txt in types.literal_type_values(types.txt_t):
            if not lang.exists(txt):
                termout.error(f"[{lg}] missing text {txt}")
                err = True
        for txt in lang.texts:
            if txt not in types.literal_type_values(types.txt_t):
                termout.error(f"[{lg}] unused text {txt}")
                err = True
        for mail in types.literal_type_values(types.mail_file_t):
            p = (
                resources.files("webamc")
                / "data" / "eml" / lg / (mail + ".eml")
            )
            if not p.exists():
                termout.error(f"[{lg}] missing mail file {mail}")
                err = True
        for h in types.literal_type_values(types.help_t):
            p = (
                resources.files("webamc")
                / "data" / "help" / lg / (h + ".html")
            )
            if not p.exists():
                termout.error(f"[{lg}] missing help file {h}")
                err = True
        if not err:
            termout.info(f"[{lg}] no error found")
    for js in (resources.files("webamc") / "data" / "js").iterdir():
        for line in js.read_text().split("\n"):
            for expr in re.finditer(r"Lang\['([^']+)'\]", line):
                for txt in expr.groups():
                    if txt not in types.literal_type_values(types.txt_t):
                        termout.error(f"undefined text {txt} in {js.name}")
