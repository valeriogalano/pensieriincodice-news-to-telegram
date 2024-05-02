import logging
import pickle
from datetime import datetime

from readwise import Readwise
from telegram_helper import TelegramHelper


logging.basicConfig(level=logging.DEBUG)
logging.getLogger("main").setLevel(logging.DEBUG)


def open_pickle():
    try:
        with open('readwise.pkl', 'rb') as f:
            published_documents = pickle.load(f)
    except FileNotFoundError:
        logging.debug("File 'readwise.pkl' non trovato.")
        published_documents = []

    return published_documents


def save_pickle(published_documents):
    with open('readwise.pkl', 'wb') as f:
        pickle.dump(published_documents, f)


def main():
    midnight_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    rw = Readwise()
    response = rw.get_published_documents(midnight_date.isoformat())

    if len(response) == 0:
        logging.debug("Nessun documento con tag 'published' trovato.")
        return

    published_documents = open_pickle()

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
        message = f"Nuovo documento pubblicato: {document['url']}"
        tg.send(message)
        published_documents.append(document['id'])

    save_pickle(published_documents)

    logging.debug("Bye!")


if __name__ == "__main__":
    main()
