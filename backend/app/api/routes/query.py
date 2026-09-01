from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.db_models import User
from app.schemas.query import QueryRequest, QueryResponse
from app.services.query import process_query


# Router responsible for ClarifyAI's main query API.
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
) -> QueryResponse:
    """
    Process a question submitted by an authenticated user.

    API-layer responsibilities:
    - authenticate the request
    - validate the request schema
    - pass the question to the service layer
    - return the service result

    Business logic remains inside the query service.
    """

    # Authentication is intentionally handled by the dependency.
    #
    # The current_user object establishes that the caller has
    # a valid authenticated identity. Query history/persistence
    # is not part of Phase 1, so the user is not persisted here.
    _ = current_user

    # Pass only the actual business input to the service layer.
    #
    # The service should not need to know about FastAPI's
    # QueryRequest schema.
    return process_query(
        query.question
    )