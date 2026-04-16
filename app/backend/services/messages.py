from app.backend.schemas.ask import AskRequest
from rag.src.retrieval import ask

def ask_message(body: AskRequest):

    #verificar se existe aquele conversation_id

    #conversation = get_conversation(body.conversation_id)

    ask(
        conversation.project_id.course_code,
        body.question,
        collection_name=conversation.project_id.collection_name,
        iaedu_url=str(body.iaedu_endpoint),
        iaedu_channel_id=body.iaedu_channel_id,
        iaedu_api_key=body.iaedu_api_key,
    )

def get_messages(body: AskRequest):
    pass
