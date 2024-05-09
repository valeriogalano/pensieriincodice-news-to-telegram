import json
import logging
import os
from datetime import datetime, timedelta

from readwise import Readwise
from telegram_helper import TelegramHelper

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("main").setLevel(logging.DEBUG)


def load_file():
    try:
        with open('readwise.json', 'rb') as f:
            json_string = f.read()
            published_documents = json.loads(json_string)
    except FileNotFoundError:
        logging.debug("File 'readwise.json' non trovato.")
        published_documents = []

    return published_documents


def dump_file(published_documents):
    with open('readwise.json', 'wb') as f:
        json_string = json.dumps(
            published_documents,
            indent=4
        )
        f.write(json_string.encode())


def main():
    midnight_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = midnight_date - timedelta(days=7)

    rw = Readwise()
    response = rw.get_published_documents(seven_days_ago.isoformat())

    if len(response) == 0:
        logging.debug("Nessun documento con tag 'published' trovato.")
        return

    published_documents = load_file()

    to_publish = []
    for document in response:
        document_id = document['id']
        if document_id not in published_documents:
            to_publish.append(document)

    if len(to_publish) == 0:
        logging.debug("Tutti i documenti trovati sono stati già pubblicati.")
        return

    tg = TelegramHelper()
    for document in to_publish:
        template_message = os.environ["TELEGRAM_MESSAGE_TEMPLATE"]
        message = template_message.format(
                      title=document['title'],
                      link=document['source_url'],
                      notes=document['notes']
                  )
        tg.send(message)
        published_documents.append(document['id'])

    dump_file(published_documents)

    logging.debug("Bye!")


if __name__ == "__main__":
    main()
