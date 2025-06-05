"""Automatic channel management with archive extraction."""
from __future__ import annotations

import asyncio
import logging
import os
import re
import yaml
from typing import Dict, Iterable, List, Optional

from telethon import TelegramClient, events
from telethon.tl.types import Channel

from TEx.core.base_module import BaseModule
from TEx.core.media_handler import UniversalTelegramMediaHandler

logger = logging.getLogger('TelegramExplorer')


class YamlChannelLoader:
    """Load explicit channels and regex patterns from YAML."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.explicit: List[str] = []
        self.regex: List[re.Pattern] = []
        self.load()

    def load(self) -> None:
        if not os.path.exists(self.file_path):
            logger.warning('channels.yaml not found: %s', self.file_path)
            return

        with open(self.file_path, 'r', encoding='utf-8') as fh:
            data = yaml.safe_load(fh) or {}

        for handle in data.get('channels', []):
            if isinstance(handle, str):
                self.explicit.append(handle.strip())

        for regex in data.get('regex', []):
            try:
                self.regex.append(re.compile(str(regex), flags=re.IGNORECASE))
            except re.error as exc:
                logger.error('Invalid regex %s: %s', regex, exc)


class ArchiveHandler:
    """Download and extract compressed files."""

    ARCHIVE_EXT = ('.zip', '.rar', '.7z')
    PASS_RE = re.compile(r"(?i)(?:password|contrase\u00f1a)[:\s]*([^\s]+)")

    def __init__(self, client: TelegramClient, media_handler: UniversalTelegramMediaHandler) -> None:
        self.client = client
        self.media_handler = media_handler

    async def process_message(self, message) -> None:
        if not getattr(message, 'file', None):
            return

        file_name = getattr(message.file, 'name', '') or ''
        if not file_name.lower().endswith(self.ARCHIVE_EXT):
            return

        media = await self.media_handler.handle_medias(message, message.chat_id, '.')
        if not media:
            return

        password = self.extract_password(message.message or '')
        await self.extract_archive(media.disk_file_path, password)

    @staticmethod
    def extract_password(text: str) -> Optional[str]:
        match = ArchiveHandler.PASS_RE.search(text or '')
        return match.group(1) if match else None

    async def extract_archive(self, file_path: str, password: Optional[str]) -> None:
        try:
            if file_path.lower().endswith('.zip'):
                import zipfile

                with zipfile.ZipFile(file_path) as zf:
                    zf.extractall(path=os.path.dirname(file_path), pwd=password.encode() if password else None)
            elif file_path.lower().endswith('.rar'):
                import rarfile

                with rarfile.RarFile(file_path) as rf:
                    rf.extractall(path=os.path.dirname(file_path), pwd=password)
            elif file_path.lower().endswith('.7z'):
                import py7zr

                with py7zr.SevenZipFile(file_path, mode='r', password=password) as sz:
                    sz.extractall(path=os.path.dirname(file_path))
            else:
                logger.info('Unsupported archive type: %s', file_path)
        except Exception as exc:
            logger.error('Failed to extract %s: %s', file_path, exc)


class TelegramChannelAutoManager(BaseModule):
    """Join channels defined in YAML and monitor for archives."""

    def __init__(self, yaml_path: str) -> None:
        self.yaml_path = yaml_path
        self.media_handler = UniversalTelegramMediaHandler()
        self.loader = YamlChannelLoader(yaml_path)

    async def can_activate(self, config: Dict, args: Dict, data: Dict) -> bool:
        return True

    async def run(self, config: Dict, args: Dict, data: Dict) -> None:
        client: TelegramClient = data['telegram_client']
        self.media_handler.configure(config)
        await self.join_explicit(client)
        await self.search_and_join(client)

        handler = ArchiveHandler(client, self.media_handler)
        client.add_event_handler(handler.process_message, events.NewMessage)
        await asyncio.sleep(0)

    async def join_explicit(self, client: TelegramClient) -> None:
        for handle in self.loader.explicit:
            try:
                await client.join_channel(handle)
                logger.info('Joined channel %s', handle)
            except Exception as exc:
                logger.error('Unable to join %s: %s', handle, exc)

    async def search_and_join(self, client: TelegramClient) -> None:
        if not self.loader.regex:
            return

        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            if isinstance(entity, Channel) and entity.broadcast:
                text = (entity.username or '') + ' ' + (entity.title or '')
                if self._match_any(text):
                    try:
                        await client.join_channel(entity)
                        logger.info('Joined channel %s', text)
                    except Exception as exc:
                        logger.error('Unable to join %s: %s', text, exc)

    def _match_any(self, text: str) -> bool:
        return any(regex.search(text) for regex in self.loader.regex)
