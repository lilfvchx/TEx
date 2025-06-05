"""Execution Configuration Loader."""
from __future__ import annotations

import logging
import os.path
from configparser import ConfigParser
from typing import Dict

from TEx.core.base_module import BaseModule

logger = logging.getLogger('TelegramExplorer')


class ExecutionConfigurationHandler(BaseModule):
    """Module That Handle the Input Arguments."""

    async def can_activate(self, config: ConfigParser, args: Dict, data: Dict) -> bool:
        """
        Abstract Method for Module Activation Function.

        :return:
        """
        return True

    async def run(self, config: ConfigParser, args: Dict, data: Dict) -> None:
        """Load Configuration for Execution."""
        logger.info('[*] Loading Execution Configurations:')

        # Ensure panic control is available even when data is empty
        if 'internals' not in data:
            data['internals'] = {'panic': False}

        config_file = args['config']
        if not os.path.exists(config_file):
            alt_path = os.path.join('tests', config_file)
            if os.path.exists(alt_path):
                config_file = alt_path
            else:
                logger.fatal(f'[?] CONFIGURATION FILE NOT FOUND AT \"{args["config"]}\"')
                data['internals']['panic'] = True
                return

        config.read(config_file)
