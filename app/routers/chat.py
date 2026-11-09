
import os
import json

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Conversation, Message
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationSummary
)
from app.services.llm import (
    generate_response,
    generate_streaming_response
)

load_dotenv()

SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "You are a helpful AI assistant."
)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


# Normal chat API
@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):

    if request.conversation_id is None:
        conversation = Conversation(title=request.message[:50])
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    else:
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id
        ).first()

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )

    previous_messages = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.id.asc()).all()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    messages.extend([
        {
            "role": message.role,
            "content": message.content
        }
        for message in previous_messages
    ])

    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message
    )

    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    messages.append({
        "role": "user",
        "content": request.message
    })

    try:
        llm_result = generate_response(messages)

        ai_answer = llm_result["content"]
        prompt_tokens = llm_result["prompt_tokens"]
        completion_tokens = llm_result["completion_tokens"]
        total_tokens = llm_result["total_tokens"]

    except (RuntimeError, ValueError) as error:
        raise HTTPException(
            status_code=503,
            detail=str(error)
        )

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=ai_answer,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens
    )

    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return ChatResponse(
        conversation_id=conversation.id,
        user_message=user_message,
        assistant_message=assistant_message
    )


# Streaming chat API
@router.post("/stream/")
def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db)
):

    if request.conversation_id is None:
        conversation = Conversation(title=request.message[:50])
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    else:
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id
        ).first()

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )

    previous_messages = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.id.asc()).all()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    messages.extend([
        {
            "role": message.role,
            "content": message.content
        }
        for message in previous_messages
    ])

    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message
    )

    db.add(user_message)
    db.commit()

    messages.append({
        "role": "user",
        "content": request.message
    })

    def stream_answer():
        full_answer = ""
        usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }

        try:
            for chunk in generate_streaming_response(messages):

                # Handle generated text
                if "content" in chunk:
                    content = chunk["content"]
                    full_answer += content
                    yield content

                # Handle token usage
                elif "usage" in chunk:
                    usage.update(chunk["usage"])

            # Save assistant response and token usage
            if full_answer:
                assistant_message = Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=full_answer,
                    prompt_tokens=usage["prompt_tokens"],
                    completion_tokens=usage["completion_tokens"],
                    total_tokens=usage["total_tokens"]
                )

                db.add(assistant_message)
                db.commit()

        except (RuntimeError, ValueError) as error:
            db.rollback()
            yield f"\n[ERROR] {error}"

    return StreamingResponse(
        stream_answer(),
        media_type="text/plain"
    )


# Get all conversations
@router.get("/conversations")
def get_conversations(db: Session = Depends(get_db)):

    conversations = db.query(Conversation).order_by(
        Conversation.id.desc()
    ).all()

    return conversations


# Get messages from one conversation
@router.get("/conversations/{conversation_id}/messages")
def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db)
):

    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.id.asc()).all()

    return messages


# Summarize conversation
@router.post(
    "/conversations/{conversation_id}/summarize",
    response_model=ConversationSummary
)
def summarize_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    conversation_messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.id.asc()).all()

    if not conversation_messages:
        raise HTTPException(
            status_code=400,
            detail="No messages to summarize"
        )

    history = "\n".join(
        f"{message.role}: {message.content}"
        for message in conversation_messages
    )

    prompt = [
        {
            "role": "system",
            "content": (
                "Summarize the conversation. Return only valid JSON "
                "with exactly these fields: title (string), "
                "summary (string), action_items (array of strings). "
                "Do not use Markdown code fences."
            )
        },
        {
            "role": "user",
            "content": history
        }
    ]

    try:
        llm_result = generate_response(prompt)
        result = llm_result["content"].strip()

        # Remove Markdown code fences if Gemini adds them
        if result.startswith("```"):
            result = result.split("\n", 1)[-1]
            if result.endswith("```"):
                result = result[:-3].strip()

        # Parse JSON
        summary_data = json.loads(result)

        # Validate using Pydantic
        return ConversationSummary.model_validate(summary_data)

    except (RuntimeError, ValueError, KeyError, TypeError) as error:
        raise HTTPException(
            status_code=502,
            detail=f"Could not generate a valid summary: {error}"
        )
