#!/usr/bin/env python3

import smtplib
import ssl
from importlib import resources

from webamc.all import *


def find_mail(mail_file: types.mail_file_t) -> None | str:

    # first look in directory pointed by parameter mails_dir of the
    # configuration then in the default dir which is webamc/data/eml.
    eml = mail_file + ".eml"
    with resources.as_file(
            resources.files("webamc") / "eml" / config.CONFIG["lang"] / eml
    ) as path:
        candidates = [os.path.abspath(path)]
    if config.CONFIG["mails_dir"] is not None:
        candidates.insert(
            0, os.path.join(config.CONFIG["mails_dir"], eml)
        )
    return next(
        (c for c in candidates if os.path.exists(c) and os.path.isfile(c)),
        None
    )


def send_mail(eaddr_from: str, eaddr_to: str, msg: str | bytes) -> bool:
    conn = None
    try:
        ctx = ssl.create_default_context()
        conn = smtplib.SMTP_SSL(
            config.CONFIG["smtp_host"],
            config.CONFIG["smtp_port"],
            context=ctx
        )
        if config.CONFIG["smtp_auth"]:
            conn.login(
                config.CONFIG["smtp_user"],
                config.CONFIG["smtp_password"]
            )
        conn.sendmail(eaddr_from, [eaddr_to], msg)
        conn.quit()
        return True
    except:
        pass
    if conn is not None:
        conn.quit()
    return False
