from pathlib import Path


ALL = {
    ".css": "text/css",
    ".ico": "image/x-icon",
    ".js": "text/javascript",
    ".json": "application/json",
    ".log": "plain/text",
    ".ods": "application/vnd.oasis.opendocument.spreadsheet",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".tex": "application/x-latex",
    ".zip": "application/zip",
    ".xlsx": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
}


def get_mtype(path: Path) -> str:
    return ALL.get(path.suffix, "application/octet-stream")
