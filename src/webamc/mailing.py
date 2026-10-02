import smtplib
import ssl
from pathlib import Path
from email.parser import Parser
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


def send_mail(
        to: list[str],
        msg_file: Path,
        fields: dict[str, str],
        cc: None | list[str] = None,
        bcc: None | list[str] = None
) -> bool:
    efrom = config.CONFIG["smtp_eaddr_from"]
    msg_body = msg_file.read_text()
    if "service" in fields:
        msg_fields = fields
    else:
        msg_fields = {**fields, "service": config.CONFIG["service_name"]}
    msg_body = msg_body.format(**msg_fields)

    msg = Parser().parsestr(msg_body)
    msg["From"] = efrom
    msg["To"] = ",".join(to)
    recipients = list(to)
    if cc is not None:
        msg["Cc"] = ",".join(cc)
        recipients += cc
    if bcc is not None:
        recipients += bcc

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
        conn.sendmail(efrom, recipients, msg.as_string().encode("utf-8"))
        conn.quit()
        return True
    except:
        pass
    if conn is not None:
        conn.quit()
    return False
