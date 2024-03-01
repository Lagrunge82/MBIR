import asyncio
import time
import traceback
import logging

from app.components.App import App
from app.config import MB_LOG_LEVEL
from app.utils.functions import configure_logger

mb_logger = configure_logger(name='pymodbus.logging', level=MB_LOG_LEVEL, file='modbus.log')


if __name__ == "__main__":
    app = App()

    logger = configure_logger(name='application.logger', level=app.LOG_LEVEL, file='app.log')

    logger.info('Application started')
    asyncio.run(app.async_exec())
    logger.info('Application finished')
