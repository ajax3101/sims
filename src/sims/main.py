from fastapi import FastAPI

from sims.core.config import get_settings
from sims.core.errors import register_error_handlers
from sims.modules.academic.router import router as academic_router
from sims.modules.finance.router import router as finance_router
from sims.modules.imports.router import router as imports_router
from sims.modules.performance.router import router as performance_router
from sims.modules.reports.router import router as reports_router
from sims.modules.staff.router import router as staff_router
from sims.modules.students.router import router as students_router


def create_app() -> FastAPI:
    app = FastAPI(title="SIMS", description="Student Information Management System")
    register_error_handlers(app)

    @app.get("/api/meta", tags=["meta"], summary="Deployment facts the UI must show (demo data)")
    async def meta() -> dict[str, bool]:
        return {"demo": get_settings().demo}

    for r in (academic_router, staff_router, students_router, performance_router, finance_router,
              reports_router, imports_router):
        app.include_router(r)
    return app


app = create_app()
