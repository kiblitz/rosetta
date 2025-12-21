import heapq
import sqlite3
import zipfile
from datetime import datetime, timedelta, timezone
from enum import IntEnum

import fsrs

EPSILON_TIMEDELTA = timedelta(microseconds=1)


class Kind(IntEnum):
    SHOW_FRONT = 0
    SHOW_BACK = 1
    SPEAK_FRONT = 2


class ReviewCard:
    def __init__(self, *, parent_id, kind, front, back):
        self.id = ReviewCard._construct_id(parent_id=parent_id, kind=kind)
        self.parent_id = parent_id
        self.kind = kind
        self._review_logs = []
        self._fsrs_card = fsrs.Card(self.id)

        match self.kind:
            case Kind.SHOW_FRONT:
                self._question = lambda _: front
                self._answer = back
            case Kind.SHOW_BACK:
                self._question = lambda _: back
                self._answer = front
            case Kind.SPEAK_FRONT:
                self._question = (
                    lambda speak_function, speak_text=front: speak_function(speak_text)
                )
                self._answer = "{}\n{}".format(front, back)

    @staticmethod
    def _construct_id(*, parent_id, kind):
        return parent_id * len(Kind) + kind.value

    def get_question(self, foundry, *, use_last_voice_id=False):
        def _remove_brackets(string):
            parse_error = RuntimeError("Uneven brackets in string: {}".format(string))
            bracket_stack = []

            def _loop(substring):
                if len(substring) == 0:
                    return ""
                c = substring[0]

                def _match_bracket_stack(c=c):
                    match c:
                        case "]":
                            expected = "["
                        case ")":
                            expected = "("
                        case "}":
                            expected = "{"
                        case _:
                            raise RuntimeError("Unexpected bracket: {}".format(c))

                    if len(bracket_stack) == 0 or bracket_stack[-1] != expected:
                        raise parse_error

                    bracket_stack.pop()

                match c:
                    case "[" | "(" | "{":
                        bracket_stack.append(c)
                        return _loop(substring[1:])
                    case "]" | ")" | "}":
                        _match_bracket_stack()
                        return _loop(substring[1:])
                    case _:
                        if len(bracket_stack) == 0:
                            return c + _loop(substring[1:])
                        return _loop(substring[1:])

            result = _loop(string)
            if len(bracket_stack) != 0:
                raise parse_error
            return result

        def _speak(speak_text, foundry=foundry, use_last_voice_id=use_last_voice_id):
            foundry.speak(
                _remove_brackets(speak_text), use_last_voice_id=use_last_voice_id
            )

        return self._question(_speak)

    def get_answer(self):
        return self._answer

    def _calc_review_order_pair(self):
        return self._fsrs_card.due, (self.parent_id, self.kind)

    def _review(self, scheduler, *, rating):
        old_card = self._fsrs_card
        new_card, review_log = scheduler.review_card(card=old_card, rating=rating)
        self._fsrs_card = new_card
        self._review_logs.append(review_log)
        return review_log


class Card:
    def __init__(self, *, id, modification_time, logical_update_num, tags, front, back):
        self.id = id
        self.modification_time = modification_time
        self.logical_update_num = logical_update_num
        self.tags = tags
        self.front = front
        self.back = back
        self.review_cards = {
            kind: ReviewCard(
                parent_id=self.id, kind=kind, front=self.front, back=self.back
            )
            for kind in list(Kind)
        }

    def _get_review_card(self, kind):
        return self.review_cards[kind]


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

        review_order_list = [
            card._get_review_card(kind)._calc_review_order_pair()
            for card in cards_list
            for kind in Kind
        ]
        heapq.heapify(review_order_list)
        self._review_heap = review_order_list

    def peak_next_review_card(self):
        due, (card_id, kind) = self._review_heap[0]
        now = datetime.now(timezone.utc).astimezone()
        if now + self._time_ahead >= due:
            return self._cards[card_id]._get_review_card(kind)

    def review(self, review_card, *, rating):
        _due, (card_id, kind) = heapq.heappop(self._review_heap)
        expected_review_card_id = ReviewCard._construct_id(parent_id=card_id, kind=kind)
        if review_card.id != expected_review_card_id:
            raise RuntimeError(
                "Tried to review a different card than next card: (given {}) (expected {})".format(
                    review_card.id, expected_review_card_id
                )
            )

        review_log = review_card._review(self._scheduler, rating=rating)
        heapq.heappush(self._review_heap, review_card._calc_review_order_pair())
        return review_log

    def review_ahead(self):
        due, (_card_id, _kind) = self._review_heap[0]
        now = datetime.now(timezone.utc).astimezone()
        if now + self._time_ahead < due:
            exact_timedelta = due - now
            rounded_up_num_days = (
                exact_timedelta + timedelta(days=1) - EPSILON_TIMEDELTA
            ).days
            self._time_ahead = timedelta(days=rounded_up_num_days)
