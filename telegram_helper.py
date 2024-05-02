import json
import logging
import os

import requests
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger("telegram")


class TelegramHelper:
    token = None
    chat_id = None

    def __init__(self):
        self.token = os.environ["TELEGRAM_BOT_API_KEY"]
        self.chat_id = os.environ["TELEGRAM_CHAT_ID"]

        logger.debug("Telegram helper inizializzato!")

    def __send_telegram_message(
            self,
            message: str,
            chat_id: str,
    ):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic base64'
        }
        url = f'https://api.telegram.org/bot{self.token}/sendMessage'
        data_dict = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_notification': True
        }
        data = json.dumps(data_dict)
        response = requests.post(
            url,
            data=data,
            headers=headers,
            verify=False
        )
        return response

    def send(self, message):
        self.__send_telegram_message(message, self.chat_id)
