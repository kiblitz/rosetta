from .anki import Deck as AnkiDeck


class Deck:
    deck: AnkiDeck
    voice_ids: set[str]

    def __init__(self, filepath, *, name, voice_ids=None):
        voice_ids = voice_ids if voice_ids is not None else set()
        self.deck = AnkiDeck(filepath, name=name)
        self.voice_ids = voice_ids

    def voice_ids_str(self):
        return ", ".join(self.voice_ids)
