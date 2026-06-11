import os


ALL = {
    ".css": "text/css",
    ".js": "text/javascript",
    ".json": "application/json",
    ".log": "plain/text",
    ".ods": "application/vnd.oasis.opendocument.spreadsheet",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".tex": "application/x-latex",
    ".zip": "application/zip"
}


def get_media_type(file_name: str) -> str:
    name, ext = os.path.splitext(file_name)
    if ext == "" and name.startswith("."):
        ext = name
    if ext in ALL:
        return ALL[ext]
    return "application/octet-stream"
