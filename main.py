import json
import logging
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

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


def escape_string(text_to_escape):
    translate_table = str.maketrans({
        '_': r'\_',
        '*': r'\*',
        '[': r'\[',
        ']': r'\]',
        '(': r'\(',
        ')': r'\)',
        '~': r'\~',
        '`': r'\`',
        '>': r'\>',
        '#': r'\#',
        '+': r'\+',
        '-': r'\-',
        '=': r'\=',
        '|': r'\|',
        '{': r'\{',
        '}': r'\}',
        '.': r'\.',
        '!': r'\!'
    })

    return text_to_escape.translate(translate_table)


def __clean_url(url: str) -> str:
    """Remove ALL query parameters and fragments from the URL.

    Rationale: Telegram MarkdownV2 is very strict about special characters.
    Query strings often contain characters like parentheses and tildes which
    lead to parsing errors. The user prefers to drop tracking (and any other)
    parameters entirely, keeping only the canonical scheme://host/path.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        # If parsing fails, return the original URL unchanged
        return url

    # Strip query and fragment completely
    cleaned = parsed._replace(query='', fragment='')
    return urlunparse(cleaned)


def __escape_url_for_markdown_destination(url: str) -> str:
    """Escape only characters required inside MarkdownV2 link destination.

    In MarkdownV2, within the parentheses of a link destination, only
    ")" and "\\" must be escaped. The rest should remain untouched so
    the URL stays valid and clickable.
    """
    return url.replace('\\', r'\\').replace(')', r'\)')


def make_markdown_link(url: str, label: str | None = None) -> str:
    """Build a safe MarkdownV2 link string.

    - Cleans the URL from tracking params.
    - Escapes only necessary chars for the destination.
    - Uses the provided label or the URL itself as visible text, escaped
      via escape_string for MarkdownV2.
    """
    cleaned = __clean_url(url)
    dest = __escape_url_for_markdown_destination(cleaned)
    visible = cleaned if label is None else label
    return f"[{escape_string(visible)}]({dest})"


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
    document = to_publish[0]
    logging.debug("Pubblicazione articolo " + document['title'])
    logging.debug("Link: " + document['source_url'])
    logging.debug("Note: " + document['notes'])
    template_message = os.environ["TELEGRAM_MESSAGE_TEMPLATE"]
    link_value = make_markdown_link(document['source_url'], label="Consulta la fonte")
    message = template_message.format(
                  title=escape_string(document['title']),
                  link=link_value,
                  notes=escape_string(document['notes'])
              )
    try:
        tg.send(message)
        published_documents.append(document['id'])
        dump_file(published_documents)
    except Exception as e:
        # Re-raise to ensure a non-zero exit code so the GitHub Action fails
        logging.error("Errore durante l'invio del messaggio su Telegram: %s", e)
        raise

    logging.debug("Bye!")


if __name__ == "__main__":
    main()
