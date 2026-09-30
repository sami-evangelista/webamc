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
