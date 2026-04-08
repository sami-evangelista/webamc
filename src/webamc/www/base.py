import urllib
import fastapi as fa
from importlib import resources

from webamc.all import *
from webamc.util import io, fmt
from webamc.actions import load, loadcsv, output
from webamc import project
from . import html_elements as he, session, context, mtype


sub_page_generator_t = tp.Callable[
    tp.Concatenate[context.Context, ...], he.Element
]
sub_page_spec_t = tuple[
    bool,
    types.static_img_t,
    sub_page_generator_t
]
page_layout_t = tp_ext.TypedDict(
    "page_layout_t",
    {
        "title": types.txt_t,
        "path": types.path_t,
        "default": str,
        "sub_pages": dict[str, sub_page_spec_t]
    }
)
menu_item_t = tuple[
    tp.Callable[[context.Context], bool],
    bool,
    types.static_img_t,
    types.txt_t,
    types.path_t
]

css_urls = [
    "https://cdn.jsdelivr.net/npm/alertifyjs@1.14.0"
    + "/build/css/alertify.min.css",
    "https://cdn.jsdelivr.net/npm/alertifyjs@1.14.0"
    + "/build/css/themes/default.min.css"
]
js_urls = [
    "https://code.jquery.com/jquery-3.7.1.min.js",
    "https://cdn.jsdelivr.net/npm/alertifyjs@1.14.0/build/alertify.min.js"
]
menu_items: list[menu_item_t] = [
    (session.ne_inbox,
     True,
     "inbox",
     "page_title_project_inbox",
     "/project/page/inbox"),
    (session.has_submission_right,
     True,
     "projects",
     "page_title_project",
     "/project/page/main"),
    (session.has_submission_right,
     False,
     "mcq",
     "page_title_item",
     "/item/page/main"),
    (session.has_submission_right,
     True,
     "exam",
     "page_title_exam",
     "/exam/page/main"),
    (session.is_admin,
     False,
     "settings",
     "page_title_administration",
     "/admin/page/main"),
    (lambda ctx: True,
     True,
     "person",
     "page_title_profile",
     "/profile/page/main"),
    (lambda ctx: True,
     False,
     "home",
     "page_title_index",
     "/"),
    (lambda ctx: True,
     False,
     "signout",
     "page_title_signout",
     "/auth/oper/logout")
]


def page(
        ctx: context.Context,
        title: str | types.txt_t,
        body: he.Element,
        side_buttons: None | list[he.Element] = None,
        wip: bool = False
) -> fa.Response:

    # menu (none if not connected)
    if not session.is_logged_in(ctx):
        div_menu: he.Element = he.Empty()
    else:
        imgs = [
            static_img(img, txt, mkuri(path))
            for (enabled, dev, img, txt, path) in menu_items
            if enabled(ctx) and not (dev and not config.CONFIG["dev"])
        ]
        div_name = he.Div(
            he.Str(str(session.usr_name(ctx))),
            class_="my-name"
        )
        div_menu = he.ElementList(
            he.Div(id_="menu-btn", class_="menu"),
            he.Div(div_name, *imgs, id_="menu-content", class_="menu")
        )

    # scripts and css files
    scripts: list[he.Element] = list()
    links: list[he.Element] = list()

    # third-party css files
    links += [
        he.Link(
            rel="stylesheet",
            type_="text/css",
            href=css_url
        )
        for css_url in css_urls
    ]

    # third-party javascripts
    scripts += [
        he.Script(src=src)
        for src in js_urls
    ]

    # webamc javascripts and css
    js_files = [
        "constants.js",
        "lang.js"
    ] + [
        x.name for x in (resources.files("webamc") / "data" / "js").iterdir()
    ]
    for fname in js_files:
        if io.get_file_extension(fname) != ".js":
            continue
        src = mkuri("/static", file_name=fname)
        script = he.Script(src=src)
        scripts.append(script)
    css_files = [
        "dyn.css"
    ] + [
        x.name for x in (resources.files("webamc") / "data" / "css").iterdir()
    ]
    links += [
        he.Link(
            rel="stylesheet",
            type_="text/css",
            href=mkuri("/static", file_name=fname)
        )
        for fname in css_files
        if io.get_file_extension(fname) == ".css"
    ]

    # head information
    if title in types.literal_type_values(types.txt_t):
        title = fmt.fmt_title(lang.txt(tp.cast(types.txt_t, title)))
    etitle = he.Title(he.Str(f"{config.CONFIG['service_name']} - {title}"))
    meta = he.Meta(**{
        "http-equiv": "Content-Type",
        "content": "text/html; charset=utf-8"
    })

    # if side buttons are given, divide the page with a sidebar and a mainpanel
    if side_buttons is None:
        body = he.Str(body) if isinstance(body, str) else body
    else:
        a_buttons = [he.Div(btn) for btn in side_buttons]
        div_sidebar = he.Div(
            *a_buttons,
            id_="sidebar"
        )
        div_mainpanel = he.Div(
            he.Str(body) if isinstance(body, str) else body,
            id_="mainpanel"
        )
        body = he.ElementList(div_sidebar, div_mainpanel)

    # work-in-progress warning
    if not wip:
        div_wip: he.Element = he.Empty()
    else:
        img_wip = he.Img(
            src=static_img_src("warning"),
            title=lang.txt("warning_page_wip"),
            class_="warning"
        )
        div_wip = he.Div(
            img_wip,
            id_="wip-warning"
        )

    # help div
    img_close_help = static_img(
        "dismiss",
        "verb_close",
        js="base_popup_help_close()",
        id_="img-tooltip-help-close-button"
    )
    div_tooltip_help = he.Div(
        img_close_help,
        he.Div(id_="div-tooltip-help-title"),
        he.Div(id_="div-tooltip-help-body"),
        id_="div-tooltip-help"
    )

    # head and body
    head = he.Head(
        etitle,
        meta,
        *links,
        *scripts
    )
    body = he.Body(
        he.H1(he.Str(title)),
        div_menu,
        div_wip,
        div_tooltip_help,
        body
    )
    h = he.Html(head, body, lang="en")
    return fa.responses.HTMLResponse(f"<!doctype html>\n{h}")


def page_error_body(code: int) -> he.Element:
    return he.Txt(tp.cast(types.txt_t, f"err_http_{code}"))


def page_error(
        ctx: context.Context,
        code: int
) -> fa.Response:
    title = tp.cast(types.txt_t, f"err_http_{code}")
    result = page(ctx, title, page_error_body(code))
    result.status_code = code
    return result


def mkuri(path: types.path_t, **kwargs: tp.Any) -> str:
    result = config.CONFIG["root_path"] + path
    if kwargs != dict():
        result = (
            result
            + "?"
            + "&".join(
                (urllib.parse.quote(str(key))
                 + "=" + urllib.parse.quote(str(val)))
                for key, val in kwargs.items()
            )
        )
    return result


def img_src(ctx: context.Context, itm_id: int) -> str:
    session.img_push(ctx, itm_id)
    return mkuri("/img", itm_id=itm_id)


def redirect(url: str) -> fa.Response:
    return fa.responses.RedirectResponse(url)


def redirect_to_login_url() -> fa.Response:
    url = mkuri("/auth/page/main")
    return redirect(url)


def file_img(file_name: str) -> types.static_img_t:
    try:
        doc_types: dict[str, types.static_img_t] = {
            ".pdf": "doc-pdf",
            ".ods": "doc-table",
            ".zip": "doc-archive"
        }
        result = doc_types[io.get_file_extension(file_name)]
    except KeyError:
        result = "doc-text"
    return result


def static_img_src(
        img: types.static_img_t,
        size: None | int = None
) -> str:
    if size is None:
        size = config.CONFIG["icon_size"]
    return mkuri("/static", file_name=f"{img}-{size}.png")


def static_img(
        img: types.static_img_t,
        title: types.txt_t,
        href: str = "",
        js: str = "",
        size: None | int = None,
        title_args: None | tuple[str] = None,
        **kwargs: str
) -> he.Element:
    result: he.Element
    src = static_img_src(img, size)
    title_str = lang.txt(title, title_args)
    result = he.Img(src=src, title=title_str, alt=title_str, **kwargs)
    if href != "":
        result["class"] += " btn"
        result["onclick"] = f"base_relocate('{href}')"
    elif js != "":
        result["class"] += " btn"
        result["onclick"] = f"javascript:{js}"
    return result


def generic_load_file(
        file_path: str,
        file_type: tp.Literal["csv", "archive"],
        usr_id: None | int = None,
        csv_delimiter: str = ";"
) -> types.load_result_t:
    def error(err: str) -> None:
        result.append({"status": 2, "msg": err})
    def warning(warn: str) -> None:
        result.append({"status": 1, "msg": warn})
    def info(inf: str) -> None:
        result.append({"status": 0, "msg": inf})
    result: types.load_result_t = list()
    output.error = error
    output.warning = warning
    output.info = info
    if file_type == "csv":
        loadcsv.action(file_path, csv_delimiter)
    elif file_type == "archive":
        assert usr_id is not None
        load.action(file_path, usr_id)
    return result


def gen_composite_page(
        ctx: context.Context,
        layout: page_layout_t,
        sub_page: str | None = None,
        wip: bool = False,
        sub_page_args: None | dict[str, tp.Any] = None
) -> fa.Response:
    def sub_page_title(sub_page: str) -> types.txt_t:
        return tp.cast(
            types.txt_t, layout["title"] + "_" + sub_page.replace("-", "_")
        )
    body: he.Element
    title = fmt.fmt_title(lang.txt(layout["title"]))
    if sub_page is None:
        sub_page = layout["default"]
    if sub_page not in layout["sub_pages"]:
        body = he.Empty()
    else:
        dev, img, fun = layout["sub_pages"][sub_page]
        if dev and not config.CONFIG["dev"]:
            body = he.Empty()
        else:
            sub_title = fmt.fmt_title(lang.txt(sub_page_title(sub_page)))
            title = f"{title} / {sub_title}"
            if sub_page_args is None:
                sub_page_args = dict()
            body = fun(ctx, **sub_page_args)
    side_buttons = [
        static_img(
            img,
            sub_page_title(sub_page),
            mkuri(layout["path"], sub_page=sub_page)
        )
        for sub_page, (dev, img, _) in layout["sub_pages"].items()
        if not (dev and not config.CONFIG["dev"])
    ]
    return page(
        ctx,
        title,
        body,
        side_buttons=side_buttons,
        wip=wip
    )


def gen_js_constants() -> str:
    constants = {
        "icon_size": config.CONFIG["icon_size"],
        "key_qst_next": config.CONFIG["key_qst_next"],
        "key_qst_prev": config.CONFIG["key_qst_prev"],
        "key_switch_mode": config.CONFIG["key_switch_mode"],
        "mcq_save_period": 10,
        "max_diff": types.ITEM_MAX_DIFFICULTY,
        "min_diff": types.ITEM_MIN_DIFFICULTY,
        "ticket_account_creation": types.TICKET_ACCOUNT_CREATION,
        "ticket_eaddr_change": types.TICKET_EADDR_CHANGE,
        "ticket_password_change": types.TICKET_PASSWORD_CHANGE,
        **{
            f"path{cst.replace('/', '_').replace('-', '_')}":
            mkuri(cst) for cst in tp.get_args(types.path_t)
        }
    }
    js = [
        f"   static {const} = {json.dumps(val)};"
        for const, val in constants.items()
    ]
    return "class Constants {\n" + "\n".join(js) + "\n}"


def gen_js_lang() -> str:
    lang.load_texts()
    js = [
        f"   static {key} = {json.dumps(fmt.fmt_title(val))};"
        for key, val in lang.texts.items()
    ]
    return "class Lang {\n" + "\n".join(js) + "\n}"


def gen_css_dyn() -> str:
    tag_img = static_img_src("tag", 24)
    grp_img = static_img_src("group", 24)
    usr_img = static_img_src("person", 24)
    timer_img = static_img_src("exam", 24)
    menu_img = static_img_src("menu")
    icon_size = config.CONFIG["icon_size"]
    return f""":root {{
    --icon-size: {icon_size}px;
    --url-timer-img: url("{timer_img}");
    --url-grp-img: url("{grp_img}");
    --url-tag-img: url("{tag_img}");
    --url-usr-img: url("{usr_img}");
    --url-menu-img: url("{menu_img}");
}}"""


def wrap_code(code: types.oper_code_t, result: tp.Any = None) -> fa.Response:
    response: types.json_response_t = {
        "success": not code.startswith("err"),
        "msgs": [lang.txt(types.oper_code_to_txt(code))],
        "result": result
    }
    return fa.responses.JSONResponse(response)


def static_file(file_name: str) -> fa.Response:
    result: fa.Response

    # some specific file that are dynamically generated
    if file_name == "constants.js":
        result = fa.responses.PlainTextResponse(gen_js_constants())
    elif file_name == "lang.js":
        result = fa.responses.PlainTextResponse(gen_js_lang())
    elif file_name == "dyn.css":
        result = fa.responses.PlainTextResponse(gen_css_dyn())
    else:

        ext = io.get_file_extension(file_name)
        with resources.as_file(
                resources.files("webamc") / "data" / ext[1:] / file_name
        ) as path:
            if not os.path.exists(path):
                raise fa.HTTPException(status_code=404)
            result = fa.responses.FileResponse(path)

    result.headers["Content-Type"] = mtype.get_media_type(file_name)
    return result


def help_page(help_id: types.help_t) -> fa.Response:
    path =  resources.files("webamc") / "data" / "help" / config.CONFIG["lang"]
    for p in [
            path / f"{help_id}.html",
            path / f"{help_id}.htm",
            path / help_id
    ]:
        try:
            with resources.as_file(p) as resource, open(resource) as fd:
                return fa.responses.HTMLResponse(fd.read())
        except FileNotFoundError:
            continue
    result = fa.responses.HTMLResponse(str(page_error_body(404)))
    return result


def mkhelp(e: he.Element, title: types.txt_t, help_id: types.help_t) -> None:
    e["class"] += " help-tooltip"
    e["onclick"] = f"javascript: base_help_open('{title}', '{help_id}')"
