import sqlite3
import zipfile
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Card:
    id: int
    modification_time: datetime
    logical_update_num: int
    tags: list[str]
    front: str
    back: str


class Deck:
    DB_FILENAME = "collection.anki21"
    CARD_SPLIT = "\x1f"

    def __init__(self, apkg_filename, *, name):
        self.name = name

        with zipfile.ZipFile(apkg_filename, "r") as zf:
            with zf.open(Deck.DB_FILENAME) as db_file:
                db_bytes = db_file.read()

        conn = sqlite3.connect(":memory:")
        conn.deserialize(db_bytes)
        cursor = conn.cursor()

        sql_result = cursor.execute("SELECT id,mod,usn,tags,flds FROM notes").fetchall()

        def _card_of_sql_row(sql_row):
            id, mod, usn, tags, flds = sql_row
            id = int(id)
            modification_time = datetime.fromtimestamp(int(mod))
            logical_update_num = int(usn)
            tags = tags.split()
            front, back = flds.split(Deck.CARD_SPLIT)
            return Card(
                id=id,
                modification_time=modification_time,
                logical_update_num=logical_update_num,
                tags=tags,
                front=front,
                back=back,
            )

        self.cards = [_card_of_sql_row(sql_row) for sql_row in sql_result]
