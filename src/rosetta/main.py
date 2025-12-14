from dotenv import load_dotenv

from .anki import Deck
from .azure import Foundry


def main():
    load_dotenv()

    deck = Deck("canto.apkg")
    for card in deck.cards:
        print(card)

    voice_ids = [
        "zh-HK-WanLungNeural",
        "zh-HK-HiuGaaiNeural",
    ]
    foundry = Foundry(voice_ids)
    for i in range(4):
        print("Enter some text >")
        text = input()
        foundry.speak(text)
