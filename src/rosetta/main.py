import customtkinter
from dotenv import load_dotenv

from .azure import Foundry
from .mainmenu import Ui as MainmenuUi


class Ui(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("rosetta")
        self.geometry(self._geometry(0.5, 0.5))

        parent_frame = customtkinter.CTkFrame(self)
        parent_frame.pack(fill="both", expand=True)
        parent_frame.grid_rowconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(0, weight=1)

        self.foundry = Foundry()

        self.mainmenu = MainmenuUi(
            self, parent_frame=parent_frame, foundry=self.foundry
        )
        self.mainmenu.grid(row=0, column=0, sticky="nsew")

        self.show_mainmenu()

    def show_mainmenu(self):
        self.mainmenu.tkraise()

    def _geometry(self, width_ratio, height_ratio):
        app_width = int(self.winfo_screenwidth() * width_ratio)
        app_height = int(self.winfo_screenheight() * height_ratio)
        return "{}x{}".format(app_width, app_height)


def main():
    load_dotenv()

    app = Ui()
    app.mainloop()

    """
    voice_ids = [
        "zh-HK-WanLungNeural",
        "zh-HK-HiuGaaiNeural",
    ]
    foundry = Foundry(voice_ids)
    for i in range(4):
        print("Enter some text >")
        text = input()
        foundry.speak(text)
    """
