"""
/ask endpoint. Thin route layer — all actual logic lives in
app.services.query_service. Keeping this file free of business logic makes
it easy to add auth, rate limiting, or request logging here later without
touching the service itself.
"""
from fastapi import APIRouter

from app.schemas.ask import AskRequest, AskResponse
from app.services.query_service import ask_aquagen

router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    result = ask_aquagen(request.question)
    return AskResponse(**result)
