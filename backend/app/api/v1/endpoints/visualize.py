"""
Visualize API Endpoints
Chart generation and visualization tools (Admin-gated during beta).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.security import get_current_admin_user
from app.models.user import User
from app.services.plotting import PlottingService

router = APIRouter()

plotting_service = PlottingService()


class ChartRequest(BaseModel):
    code: str = Field(..., description="Python code using matplotlib/seaborn to generate a chart")


class ChartResponse(BaseModel):
    status: str
    image_base64: str | None = None
    error: str | None = None


@router.post("/chart", response_model=ChartResponse)
async def generate_chart(
    request: ChartRequest,
    user: User = Depends(get_current_admin_user),  # Admin-only during beta
):
    """Generate a chart from Python plotting code. Admin-only during beta."""
    result = await plotting_service.generate_chart(request.code)

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return ChartResponse(
        status=result["status"],
        image_base64=result["image_base64"],
        error=result.get("error"),
    )
