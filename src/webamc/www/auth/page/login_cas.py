#!/usr/bin/env python3

from webamc.www.all import *


def page(ctx: context.Context) -> he.Element:
    from webamc.www.auth.oper import login_cas
    href = login_cas.get_cas_client().get_login_url()
    return he.ElementList(
        he.Txt("seq_authentify_with_server"),
        he.A(he.Str(" " + config.CONFIG["cas_server_name"]), href=href)
    )
