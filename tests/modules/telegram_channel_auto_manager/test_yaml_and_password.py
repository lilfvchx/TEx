"""Tests for YAML loader and password extraction."""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from TEx.modules.telegram_channel_auto_manager import YamlChannelLoader, ArchiveHandler

class ChannelAutoManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.yaml_path = 'channels.yaml'
        with open(self.yaml_path, 'w', encoding='utf-8') as fh:
            fh.write('channels:\n  - "@chan1"\n  - "https://t.me/chan2"\nregex:\n  - "scam"')

    def tearDown(self) -> None:
        if os.path.exists(self.yaml_path):
            os.remove(self.yaml_path)

    def test_yaml_loader(self) -> None:
        loader = YamlChannelLoader(self.yaml_path)
        self.assertIn('@chan1', loader.explicit)
        self.assertEqual(1, len(loader.regex))

    def test_password_regex(self) -> None:
        text = 'Archivo adjunto. Password: secreto123'
        password = ArchiveHandler.extract_password(text)
        self.assertEqual('secreto123', password)
