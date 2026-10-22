import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sims.core.db import get_session
from sims.models import ImportBatch
from sims.modules.imports.import_service import SUPPORTED_SUFFIXES, import_file
from sims.modules.imports.schemas import ImportBatchOut, ImportReport

router = APIRouter(prefix="/api/imports", tags=["imports"])


@router.post("", response_model=list[ImportReport], summary="Import roster files (.docx, .xlsx)")
async def upload_rosters(files: list[UploadFile], session: AsyncSession = Depends(get_session)) -> list[ImportReport]:
    suffixes = [Path(f.filename or "").suffix.lower() for f in files]
    if bad := [f.filename for f, sfx in zip(files, suffixes) if sfx not in SUPPORTED_SUFFIXES]:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"unsupported file(s) {bad}; expected one of {sorted(SUPPORTED_SUFFIXES)}",
        )
    reports = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, (upload, suffix) in enumerate(zip(files, suffixes)):
            path = Path(tmp) / f"{i}{suffix}"
            path.write_bytes(await upload.read())
            reports.append(await import_file(session, path, source_name=upload.filename))
    return reports


@router.get("/{batch_id}", response_model=ImportBatchOut, summary="Import batch with its issues")
async def get_batch(batch_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> ImportBatch:
    batch = await session.scalar(
        select(ImportBatch).options(selectinload(ImportBatch.issues)).where(ImportBatch.id == batch_id)
    )
    if batch is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "import batch not found")
    return batch
