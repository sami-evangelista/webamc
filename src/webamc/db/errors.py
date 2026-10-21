import json

from webamc.all import *


class DBException(Exception):
    def msg(self) -> str:
        return lang.txt("err_db_invalid_request")


class DBInvalidValue(DBException):
    def __init__(self, tbl: str, col: str, val: types.db_base_val_t):
        super().__init__(tbl)
        self.col = col
        self.val = val
        self.tbl = tbl
    def __str__(self) -> str:
        return (
            f"invalid value for column {self.tbl}.{self.col}: "
            f"{json.dumps(self.val)}"
        )
    def msg(self) -> str:
        return lang.txt(
            "param_err_invalid_value",
            lang.txt(tp.cast(types.txt_t, f"col_desc_{self.col}"))
        )


class DBDuplicateValue(DBException):
    def __init__(
            self,
            tbl: str,
            col: str | list[str],
            val: types.db_base_val_t | list[types.db_base_val_t]
    ):
        super().__init__(tbl)
        self.col = col
        self.val = val
        self.tbl = tbl
    def __str__(self) -> str:
        return (
            f"duplicate for column {self.tbl}.{self.col}: "
            f"{json.dumps(self.val)}"
        )
    def msg(self) -> str:
        if isinstance(self.col, str):
            return lang.txt(
                "param_err_invalid_duplicate_value",
                lang.txt(tp.cast(types.txt_t, f"col_desc_{self.col}"))
            )
        c = tuple(
            lang.txt(tp.cast(types.txt_t, f"col_desc_{c}")) for c in self.col
        )
        return lang.txt("param_err_invalid_duplicate_value", str(c))


class DBInvalidNullValue(DBException):
    def __init__(self, tbl: str, col: str):
        super().__init__(tbl)
        self.col = col
        self.tbl = tbl
    def __str__(self) -> str:
        return f"invalid null value for column {self.tbl}.{self.col}"
    def msg(self) -> str:
        return lang.txt(
            "param_err_invalid_null_value",
            lang.txt(tp.cast(types.txt_t, f"col_desc_{self.col}"))
        )


class DBItemRelationInvalid(DBException):
    def __init__(self, itm_code_ancestor: str):
        super().__init__()
        self.itm_code_ancestor = itm_code_ancestor
    def msg(self) -> str:
        return lang.txt(
            "param_err_invalid_item_relation",
            self.itm_code_ancestor
        )


class DBDeletionOfItemReferencedInExamSubmission(DBException):
    def __init__(self, itm_code: str):
        super().__init__()
        self.itm_code = itm_code
    def msg(self) -> str:
        return lang.txt(
            "param_err_item_referenced_in_exam_submission",
            self.itm_code
        )
