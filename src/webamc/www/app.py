from a2wsgi import ASGIMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.errors import ServerErrorMiddleware
from pydantic_settings import BaseSettings

from webamc.www.all import *
from webamc.db import op, queries
from webamc.www.auth import router as router_auth
from webamc.www.admin import router as router_admin
from webamc.www.db import router as router_db
from webamc.www.exam import router as router_exam
from webamc.www.project import router as router_project
from webamc.www.item import router as router_item
from webamc.www.mcq import router as router_mcq
from webamc.www.profile import router as router_profile
from webamc.www.ticket import router as router_ticket
from webamc.www.stats import router as router_stats
from . import index


class Settings(BaseSettings):
    config_file: None | str = None


settings = Settings()
config.load(settings.config_file)

# This function don't handle correctly status_code error 500.
async def exception_handler(
        req: fa.Request,
        exc: fa.HTTPException
) -> fa.Response:
    ctx = context.Context(req)
    return base.page_error(ctx, exc.status_code)


exceptions = {
    403: exception_handler,
    404: exception_handler,
    422: exception_handler,
    500: exception_handler
}

app = fa.FastAPI(
    exception_handlers=exceptions  # type: ignore
)
app.add_middleware(  # middleware to handle sessions
    SessionMiddleware,
    secret_key=config.CONFIG["secret_key"],
    max_age=None
)
app.add_middleware(  # middleware to handle server errors
    ServerErrorMiddleware,
    debug=config.CONFIG["debug"]
)
application = ASGIMiddleware(app)  # type: ignore

# include routers
for router in [
        router_admin,
        router_auth,
        router_db,
        router_exam,
        router_project,
        router_item,
        router_mcq,
        router_profile,
        router_ticket,
        router_stats
]:
    app.include_router(router.router)

# connect to the DB
op.connect()


@app.get("/hello")
async def hello() -> fa.Response:
    return fa.responses.PlainTextResponse("It works mate !")


@app.get("/static")
async def route_static(file_name: str) -> fa.Response:
    return base.static_file(file_name)


@app.get("/help")
async def route_help(help_id: types.help_t) -> fa.Response:
    return base.help_page(help_id)


@app.get("/img")
async def route_img(
    req: fa.Request,
    itm_id: int,
    iti_num: int = 1
) -> fa.Response:
    with context.Context(req) as ctx:
        img = queries.get_img(ctx.dbs, itm_id, iti_num)
        if img is None:
            return fa.responses.HTMLResponse(
                f"img-{itm_id}-inst-{iti_num}"
            )
        return fa.Response(
            content=img, media_type="image/png"
        )


@app.get("/")
async def route_index(req: fa.Request) -> fa.Response:
    with context.Context(req) as ctx:
        if not session.is_logged_in(ctx):
            url = base.mkuri("/auth/page/main")
            return fa.responses.RedirectResponse(url)

        # active exam => redirect to the mcq page
        registration = session.active_registration(ctx)
        if registration is not None:
            _, _, mcq = registration
            url = base.mkuri("/mcq/page/form", mcq_id=mcq.mcq_id)
            return fa.responses.RedirectResponse(url)
        return index.page(ctx)
