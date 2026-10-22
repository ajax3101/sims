import enum
import uuid
from datetime import date
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from sims.core.db import get_session
from sims.modules.reports import service
from sims.modules.reports.document import Document
from sims.modules.reports.exporters import to_docx, to_pdf, to_xlsx

router = APIRouter(prefix="/api/reports", tags=["reports"])
Session = Depends(get_session)


class ReportFormat(enum.StrEnum):
    XLSX = "xlsx"
    DOCX = "docx"
    PDF = "pdf"


_RENDER = {
    ReportFormat.XLSX: (to_xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ReportFormat.DOCX: (to_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ReportFormat.PDF: (to_pdf, "application/pdf"),
}
FormatQuery = Query(ReportFormat.XLSX, alias="format")


def _file(doc: Document, fmt: ReportFormat, stem: str) -> Response:
    render, media_type = _RENDER[fmt]
    filename = f"{stem}.{fmt.value}"
    ascii_name = f"report.{fmt.value}"  # RFC 6266: ASCII fallback + UTF-8 name for Cyrillic
    return Response(render(doc), media_type=media_type, headers={
        "Content-Disposition": f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename)}"})


@router.get("/academic-debts", summary="Academic debt register by faculty/institute, department or group")
async def academic_debts(fmt: ReportFormat = FormatQuery, org_unit_id: uuid.UUID | None = None,
                         department_id: uuid.UUID | None = None, group_id: uuid.UUID | None = None,
                         session: AsyncSession = Session):
    doc = await service.academic_debts(session, org_unit_id=org_unit_id, department_id=department_id, group_id=group_id)
    return _file(doc, fmt, f"академборги-{date.today():%Y-%m-%d}")


@router.get("/financial-debts", summary="Tuition payment debts")
async def financial_debts(fmt: ReportFormat = FormatQuery, org_unit_id: uuid.UUID | None = None,
                          group_id: uuid.UUID | None = None, session: AsyncSession = Session):
    doc = await service.financial_debts(session, org_unit_id=org_unit_id, group_id=group_id)
    return _file(doc, fmt, f"фінборги-{date.today():%Y-%m-%d}")


@router.get("/students/{student_id}/card", summary="Individual student card with transcript")
async def student_card(student_id: uuid.UUID, fmt: ReportFormat = FormatQuery, session: AsyncSession = Session):
    name, doc = await service.student_card(session, student_id)
    return _file(doc, fmt, name)
