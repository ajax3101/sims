from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class NotFound(Exception):
    def __init__(self, what: str):
        super().__init__(f"{what} not found")
        self.detail = f"{what} not found"


class Conflict(Exception):
    def __init__(self, detail: str, constraint: str | None = None):
        super().__init__(detail)
        self.detail = detail
        self.constraint = constraint


class InvalidInput(ValueError):
    """Business-rule validation failure (422) beyond what the request schema checks."""


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFound)
    async def _not_found(_: Request, exc: NotFound) -> JSONResponse:
        return JSONResponse({"detail": exc.detail}, status_code=404)

    @app.exception_handler(Conflict)
    async def _conflict(_: Request, exc: Conflict) -> JSONResponse:
        return JSONResponse({"detail": exc.detail, "constraint": exc.constraint}, status_code=409)

    @app.exception_handler(InvalidInput)
    async def _invalid(_: Request, exc: InvalidInput) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=422)
