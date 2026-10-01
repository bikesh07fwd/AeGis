from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from database.models import ConversationMessage

async def save_message(db: AsyncSession, conversation_id: str, message_id: str, role: str, content: str, model_name: str = None, tenant_id: int = 1) -> ConversationMessage:
    msg = ConversationMessage(
        tenant_id=tenant_id or 1,
        conversation_id=conversation_id,
        message_id=message_id,
        role=role,
        content=content,
        model_name=model_name
    )
    db.add(msg)
    await db.commit()
    return msg

async def get_recent_messages(db: AsyncSession, conversation_id: str, limit: int = 5) -> list[ConversationMessage]:
    stmt = (
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(desc(ConversationMessage.created_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    messages = list(result.scalars().all())
    messages.reverse() # return in chronological order
    return messages
