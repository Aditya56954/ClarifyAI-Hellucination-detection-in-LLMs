from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.db_models import User
from app.schemas.query import QueryRequest, QueryResponse
from app.services.query import process_query


# Router responsible for ClarifyAI's main query-related APIs.
router = APIRouter(
    prefix="/query",
    tags=["Query"],
)


@router.post(
    "",
    response_model=QueryResponse,
)
def submit_query(
    query: QueryRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Process a question submitted by an authenticated user.

    Authentication is handled through get_current_user().
    This ensures that only users with a valid JWT can access
    the ClarifyAI query pipeline.
    """

    # Pass the validated question to the service layer.
    #
    # The service layer is responsible for the actual
    # ClarifyAI processing logic.
    response = process_query(query)

    return response