import random

from webamc.all import *


DEPTH = 3
WIDTH = 4
NO_ROOTS = 3
NO_STUDENTS_PER_GROUP = 20
NO_TEACHERS_PER_GROUP = 20
NO_TAGS = 1_000
EADDR_DOMAIN = "example.com"
PASSWORD = "00000000"


def action(out_dir: str) -> None:

    all_names: set[tuple[str, str]] = set()

    def usr_code(prefix: str, grps: list[int], id_: int) -> str:
        return f"{prefix}-" + "-".join(str(g) for g in grps) + f"-{id_}"

    def teacher_code(grps: list[int], tea: int) -> str:
        return usr_code("T", grps, tea)

    def student_code(grps: list[int], stu: int) -> str:
        return usr_code("S", grps, stu)

    def grp_name(grps: list[int]) -> str:
        return "G-" + "-".join(str(g) for g in grps)

    def pick_name() -> str:
        def rep(n: int) -> str:
            return "".join(random.choice(choices) for _ in range(n))
        choices = [
            "ta", "ca", "de", "ti", "mi", "di", "de", "bi",
            "blu", "blu", "ba", "gu", "ro", "ma", "ku", "mon"
        ]
        if random.choice([0, 1]) == 0:
            return rep(4)
        return rep(2) + " " + rep(2)

    def pick_fst_name() -> str:
        choices = [
            "mark", "lisa", "sam", "mahmoud", "anna", "myriam", "paul",
            "boris", "michka", "andrea", "john", "adama", "fatou"
        ]
        return "-".join(random.choice(choices) for _ in range(2))

    def path(f: str) -> str:
        return os.path.join(out_dir, f)

    with (
            open(path("00-usr.csv"), "w", encoding="utf-8") as fd_usr,
            open(path("01-cas_auth.csv"), "w", encoding="utf-8") as fd_cas,
            open(path("02-local_auth.csv"), "w", encoding="utf-8") as fd_loc,
            open(path("03-tag.csv"), "w", encoding="utf-8") as fd_tag,
            open(path("04-grp.csv"), "w", encoding="utf-8") as fd_grp,
            open(path("05-usr_grp.csv"), "w", encoding="utf-8") as fd_ugp,
            open(path("06-tbl.csv"), "w", encoding="utf-8") as fd_tbl,
            open(path("07-admin.csv"), "w", encoding="utf-8") as fd_adm,
            open(path("08-attr.csv"), "w", encoding="utf-8") as fd_att,
            open(path("09-usr_attr.csv"), "w", encoding="utf-8") as fd_uat
    ):
        uid = 0

        def new_usr(usr_code: str, tbls: None | list[str] = None) -> None:
            nonlocal uid
            uid = uid + 1
            while True:
                usr_fst_name = pick_fst_name()
                usr_name = pick_name()
                key = (usr_fst_name, usr_name)
                if key not in all_names:
                    all_names.add(key)
                    break
            usr_eaddr = f"{usr_fst_name}.{usr_name}@{EADDR_DOMAIN}".replace(
                " ", "_"
            )
            fd_usr.write(f"{usr_code};{usr_eaddr};{usr_fst_name};{usr_name}\n")
            password = PASSWORD
            fd_loc.write(f"1;{usr_code};{usr_code};{password}\n")
            fd_cas.write(f"1;{usr_code};{usr_code}\n")
            fd_uat.write(f"UID;{usr_code};{str(uid).zfill(8)}\n")
            fd_uat.write(f"RID;{usr_code};{str(uid).zfill(8)[::-1]}\n")
            if tbls is not None:
                for tbl in tbls:
                    fd_adm.write(f"{usr_code};{tbl}\n")

        def new_right(usr_code: str, grp: str, right: int) -> None:
            fd_ugp.write(f"{usr_code};{grp};{right}\n")

        fd_usr.write("usr_code;usr_eaddr;usr_fst_name;usr_name\n")
        fd_cas.write("cas_enabled;cas_usr;cas_login\n")
        fd_loc.write("loc_enabled;loc_usr;loc_login;loc_password\n")
        fd_tag.write("tag_name;tag_desc;tag_color\n")
        fd_grp.write("grp_name;grp_parent\n")
        fd_ugp.write("ugp_usr;ugp_grp;ugp_right\n")
        fd_tbl.write("tbl_name\n")
        fd_adm.write("adm_usr;adm_tbl\n")
        fd_att.write("atr_code;atr_desc\n")
        fd_att.write("UID;User ID\n")
        fd_att.write("RID;Reversed user ID\n")
        fd_uat.write("uat_attr;uat_usr;uat_value\n")

        all_tables = [
            "admin",
            "local_auth",
            "cas_auth",
            "grp",
            "tag",
            "usr",
            "usr_grp",
            "tbl",
            "attr",
            "usr_attr"
        ]
        for tbl in all_tables:
            fd_tbl.write(tbl + "\n")

        new_usr("root", all_tables)

        def traverse(stack: list[int]) -> None:
            def new_right_on_next_grp(
                    usr_code: str, mod: int, right: int
            ) -> None:
                old_val = stack[-1]
                stack[-1] = (old_val + 1) % mod
                new_right(usr_code, grp_name(stack), right)
                stack[-1] = old_val
            if len(stack) == 1:
                grp_parent = ""
            else:
                grp_parent = grp_name(stack[:-1])
            grp = grp_name(stack)
            fd_grp.write(f"{grp};{grp_parent}\n")

            # root group => create teachers
            if len(stack) == 1:
                new_right("root", grp, 2)
                for i in range(NO_TEACHERS_PER_GROUP):
                    usr_code = teacher_code(stack, i)
                    new_usr(usr_code, ["tag"])
                    new_right(usr_code, grp, 2)
                    new_right_on_next_grp(usr_code, NO_ROOTS, 2)

            # leaf group => create students
            if len(stack) == DEPTH:
                for i in range(NO_STUDENTS_PER_GROUP):
                    usr_code = student_code(stack, i)
                    new_usr(usr_code)
                    new_right(usr_code, grp, 1)
                    new_right_on_next_grp(usr_code, WIDTH, 1)

            # non leaf group => create sub-groups
            else:
                for i in range(WIDTH):
                    stack.append(i)
                    traverse(stack)
                    stack.pop()

        def new_tag() -> None:
            tag_name_len = random.randint(5, 20)
            tag_name = "TAG-" + "".join(
                random.choice("abcdef") for _ in range(tag_name_len)
            )
            tag_color = "#" + "".join(
                random.choice("6789ABCDEF") for _ in range(6)
            )
            fd_tag.write(f"{tag_name};{tag_name};{tag_color}\n")

        for r in range(NO_ROOTS):
            traverse([r])
        for _ in range(NO_TAGS):
            new_tag()
