import re
import logging
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

logging.basicConfig(format='[%(asctime)s] MESSAGE:\n%(message)s\n',
                    level=logging.WARNING)


class GetContactRequester:
    client: TelegramClient

    def __init__(self, api_id: int, api_hash: str, session_strings, chats: list):
        """
        :param chats: a list of chats that will be listened by this client
        :param session_strings: ConfigParser object representing the section of session strings
        """
        self.session_strings = session_strings

        self.client = TelegramClient(StringSession(session_strings[0][1]),
                                     api_id, api_hash)
        self.client.add_event_handler(self._handle_message, events.NewMessage(chats=chats, incoming=True, outgoing=False))

        self.chats = chats
        self.response = None

    async def request(self, phone_number: str):
        await self._start_client()

        for chat in self.chats:
            await self.client.send_message(chat, phone_number)

        # response is None only if the message wasn't processed
        while True:
            if self.response is not None:
                break
            await asyncio.sleep(0.1)

        await self.client.disconnect()
        return self.response

    async def _start_client(self):
        self.response = None

        if not self.client.is_connected():
            await self.client.start()

    async def _handle_message(self, event):
        logging.warning(event.text)

        if re.search(r'(некорректный номер|запросов не осталось|настоящий getcontact|ничего не найдено)',
                     event.text, re.IGNORECASE):
            self.response = []
        elif event.is_reply and re.search('результаты', event.text, re.IGNORECASE):
            text = re.sub(r"Результаты по \+?[\d]{11}:", '', event.text)
            self.response = [name.strip() for name in text.split('\n') if name]