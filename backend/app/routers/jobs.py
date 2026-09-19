"""Background job status polling endpoint.

Clients that received a ``202 Accepted`` from ``POST /documents/upload``
should poll ``GET /jobs/{job_id}`` until status is ``done`` or ``failed``.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobStatusResponse(BaseModel):
    """Current state of a background document processing job."""

    job_id: str
    doc_id: str
    status: str  # pending | processing | done | failed
    error: str | None = None
    result: dict | None = None


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Poll the status of a background document processing job.

    Args:
        job_id: The job UUID returned in the ``202 Accepted`` response.

    Returns:
        ``JobStatusResponse`` with the current job status and result when done.

    Raises:
        404: If the job_id is not found.
    """
    import json

    from app.db.base import get_session
    from app.db.models import AnalysisJob

    async with get_session() as session:
        job = await session.get(AnalysisJob, job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found",
        )

    result = None
    if job.result_json:
        try:
            result = json.loads(job.result_json)
        except Exception:
            result = None

    return JobStatusResponse(
        job_id=job.job_id,
        doc_id=job.doc_id,
        status=job.status.value,
        error=job.error,
        result=result,
    )
