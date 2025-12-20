import heapq
import sqlite3
import zipfile
from datetime import datetime, timedelta, timezone

import fsrs

EPSILON_TIMEDELTA = timedelta(microseconds=1)


class Card:
    def __init__(self, *, id, modification_time, logical_update_num, tags, front, back):
        self.id = id
        self.modification_time = modification_time
        self.logical_update_num = logical_update_num
        self.tags = tags
        self.front = front
        self.back = back
        self._fsrs_card = fsrs.Card(id)
        self._review_log = []

    def get_question(self):
        return self.front

    def get_answer(self):
        return self.back

    def _due(self):
        return self._fsrs_card.due

    def _review(self, scheduler, *, rating):
        card, review_log = scheduler.review_card(card=self._fsrs_card, rating=rating)
        self._fsrs_card = card
        self._review_log.append(review_log)
        return review_log

    def __lt__(self, other):
        return self.id < other.id


class Deck:
    DB_FILENAME = "collection.anki21"
    CARD_SPLIT = "\x1f"

    def __init__(self, apkg_filename, *, name, voice_ids=None):
        self.name = name
        self.voice_ids = voice_ids if voice_ids is not None else set()
        self._scheduler = fsrs.Scheduler()
        self._time_ahead = timedelta()

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

        cards_list = [_card_of_sql_row(sql_row) for sql_row in sql_result]
        self._cards = {card.id: card for card in cards_list}

        review_order_list = [self._calc_review_order_pair(card) for card in cards_list]
        heapq.heapify(review_order_list)
        self._review_heap = review_order_list

    def peak_next_review_card(self):
        due, card = self._review_heap[0]
        now = datetime.now(timezone.utc).astimezone()
        if now + self._time_ahead >= due:
            return card

    def review(self, card, *, rating):
        _due, card_ = heapq.heappop(self._review_heap)
        if card != card_:
            raise RuntimeError("Tried to review a different card than next card")

        review_log = card._review(self._scheduler, rating=rating)
        heapq.heappush(self._review_heap, self._calc_review_order_pair(card))
        return review_log

    def review_ahead(self):
        due, _card = self._review_heap[0]
        now = datetime.now(timezone.utc).astimezone()
        if now + self._time_ahead < due:
            exact_timedelta = due - now
            rounded_up_num_days = (
                exact_timedelta + timedelta(days=1) - EPSILON_TIMEDELTA
            ).days
            self._time_ahead = timedelta(days=rounded_up_num_days)

    def _calc_review_order_pair(self, card):
        return card._due(), card

    def voice_ids_str(self):
        return ", ".join(self.voice_ids)
