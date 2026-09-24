import smtplib
import ssl
from pathlib import Path
from importlib import resources

from webamc.all import *


def find_mail(mail_file: types.mail_file_t) -> None | Path:

    # first look in directory pointed by parameter mails_dir of the
    # configuration then in the default dir which is webamc/data/eml.
    eml = mail_file + ".eml"
    pkg_data = str(resources.files("webamc"))
    candidates = [
        Path(pkg_data) / "data" / "eml" / config.CONFIG["lang"] / eml
    ]
    if config.CONFIG["mails_dir"] is not None:
        candidates.insert(0, Path(config.CONFIG["mails_dir"]) / eml)
    return next((c for c in candidates if c.is_file()), None)


def send_mail(eaddr_from: str, eaddr_to: str, msg: str | bytes) -> bool:
    conn: None | smtplib.SMTP | smtplib.SMTP_SSL = None
    try:
        if config.CONFIG["smtp_ssl"]:
            ctx = ssl.create_default_context()
            conn = smtplib.SMTP_SSL(
                config.CONFIG["smtp_host"],
                config.CONFIG["smtp_port"],
                context=ctx
            )
        else:
            conn = smtplib.SMTP(
                config.CONFIG["smtp_host"],
                config.CONFIG["smtp_port"]
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
