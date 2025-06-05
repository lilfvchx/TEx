import asyncio
from datetime import datetime
from typing import Optional

from telethon import TelegramClient, events
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class TelegramMessage(Base):
    __tablename__ = "telegram_message"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, index=True)
    text = Column(String)
    file_path = Column(String)
    date_time = Column(DateTime, default=datetime.utcnow)


def init_db(db_url: str):
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


async def process_new_messages(api_id: int, api_hash: str, db_url: str, session_name: str = "session") -> None:
    """Listen for new Telegram messages and store them in the database."""
    Session = init_db(db_url)

    async with TelegramClient(session_name, api_id, api_hash) as client:

        @client.on(events.NewMessage)
        async def handler(event: events.NewMessage.Event) -> None:
            session = Session()
            message = event.message
            file_path: Optional[str] = None

            if message.media:
                file_path = await message.download_media()

            entry = TelegramMessage(
                id=message.id,
                chat_id=event.chat_id or 0,
                text=message.message or "",
                file_path=file_path,
                date_time=message.date,
            )
            session.merge(entry)
            session.commit()
            session.close()
            print(f"Mensaje guardado con ID {message.id}")

        print("Escuchando mensajes...")
        await client.run_until_disconnected()
