from app.backend.api.deps import get_rag_engine
from app.backend.main import app
from contracts.rag.models import TutorResponse, TutorSource

from .factories import insert_chat


class StubRagEngine:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def ask(
        self,
        course: str,
        query: str,
        summary: str = "",
        history: list[dict] | None = None,
        memory: str = "",
    ) -> TutorResponse:
        self.calls.append(
            {
                "course": course,
                "query": query,
                "summary": summary,
                "history": history,
                "memory": memory,
            }
        )
        return TutorResponse(
            answer="Resposta de teste.",
            sources=[TutorSource(filename="ed.pdf", pages=[3])],
            is_fallback=False,
        )

    def preload_models(self) -> None:
        return None


async def test_send_message_student_receives_answer_and_persists_messages(
    api_client,
    db,
    auth_header,
):
    rag = StubRagEngine()
    app.dependency_overrides[get_rag_engine] = lambda: rag
    chat_id = await insert_chat(db, course="ed", user_id="stud-1")

    resp = await api_client.post(
        f"/api/v1/chat/{chat_id}/messages",
        json={"question": "O que e uma lista ligada?"},
        headers=auth_header(role="student", id="stud-1"),
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] == "Resposta de teste."
    assert body["sources"] == [{"filename": "ed.pdf", "pages": [3]}]
    assert body["is_fallback"] is False
    assert body["guardrail_triggered"] is False
    assert body["user_message_id"]
    assert body["assistant_message_id"]

    assert rag.calls == [
        {
            "course": "ed",
            "query": "O que e uma lista ligada?",
            "summary": None,
            "history": [],
            "memory": "",
        }
    ]

    messages = await db["messages"].find({"conversation_id": chat_id}).sort("_id", 1).to_list(length=None)
    assert [(m["role"], m["content"]) for m in messages] == [
        ("user", "O que e uma lista ligada?"),
        ("assistant", "Resposta de teste."),
    ]
    assert messages[1]["sources"] == [{"filename": "ed.pdf", "pages": [3]}]


async def test_send_message_cannot_access_another_students_chat(
    api_client,
    db,
    auth_header,
):
    app.dependency_overrides[get_rag_engine] = lambda: StubRagEngine()
    chat_id = await insert_chat(db, course="ed", user_id="owner")

    resp = await api_client.post(
        f"/api/v1/chat/{chat_id}/messages",
        json={"question": "O que e uma lista ligada?"},
        headers=auth_header(role="student", id="other-student"),
    )

    assert resp.status_code == 403
    assert await db["messages"].count_documents({"conversation_id": chat_id}) == 0
