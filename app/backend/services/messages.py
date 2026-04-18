from app.backend.schemas.ask import AskRequest
from rag.src.retrieval import ask

def ask_message(body: AskRequest):

    #verificar se existe aquele conversation_id

    #conversation = get_conversation(body.conversation_id)

    response = ask(
        #conversation.project_id.course_code,
        "ed",
        body.question,
        iaedu_url=str(body.iaedu_endpoint),
        iaedu_channel_id=body.iaedu_channel_id,
        iaedu_api_key=body.iaedu_api_key,
    )

    return response

def get_messages(body: AskRequest):
    pass
