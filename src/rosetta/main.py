from .azure import Foundry


def main():
    print("hello world")
    voice_ids = [
        "zh-HK-WanLungNeural",
        "zh-HK-HiuGaaiNeural",
    ]
    foundry = Foundry(voice_ids)
    for i in range(4):
        foundry.run()
