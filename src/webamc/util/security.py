import random
import hashlib
import string

from webamc import config


password_hash_method = hashlib.md5
password_hash_loops = 2**16


def hash_password(password: str) -> str:
    result = password
    for _ in range(password_hash_loops):
        h = password_hash_method()
        h.update(result.encode())
        result = h.hexdigest()
    return result


def gen_ticket() -> str:
    return "".join(
        random.choice(string.ascii_letters + string.digits)
        for _ in range(config.CONFIG["ticket_length"])
    )
