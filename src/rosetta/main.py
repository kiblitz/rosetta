import tkinter

import customtkinter
from dotenv import load_dotenv

from .anki import Deck
from .azure import Foundry


class RosettaDeck:
    deck: Deck
    voice_ids: set[str]

    def __init__(self, deck, *, voice_ids=None):
        voice_ids = voice_ids if voice_ids is not None else set()
        self.deck = deck
        self.voice_ids = voice_ids

    def voice_ids_str(self):
        return ", ".join(self.voice_ids)


class Ui(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self._setup_state()
        self._setup_ui()

    def _setup_state(self):
        self.decks = {}
        self.voice_ids = set()

    def _setup_ui(self):
        self.title("rosetta")
        self.geometry(self._geometry(0.5, 0.5))

        self._setup_action_bar()
        self._setup_deck_and_voice_id_frames()

    def _setup_action_bar(self):
        parent_frame = customtkinter.CTkFrame(self)
        parent_frame.pack(fill="both")

        load_deck_button = customtkinter.CTkButton(
            parent_frame,
            text="Load deck",
            command=self._load_anki_deck,
            fg_color="grey",
        )
        load_deck_button.pack(side="left", padx=10, pady=10, anchor="w")

        add_voice_id_button = customtkinter.CTkButton(
            parent_frame,
            text="Add voice ID",
            command=self._add_voice_id,
            fg_color="grey",
        )
        add_voice_id_button.pack(side="left", padx=10, pady=10, anchor="w")

    def _setup_deck_and_voice_id_frames(self):
        parent_frame = customtkinter.CTkFrame(self)
        parent_frame.pack(fill="both", expand=True)

        self.deck_scroll_frame = customtkinter.CTkScrollableFrame(
            parent_frame, label_text="Decks"
        )
        self.deck_scroll_frame.pack(
            fill="both", side="left", expand=True, padx=(10, 5), pady=(10, 10)
        )
        self._setup_decks_scroll()

        self.voice_id_scroll_frame = customtkinter.CTkScrollableFrame(
            parent_frame, label_text="Voice IDs"
        )
        self.voice_id_scroll_frame.pack(
            fill="both", side="right", expand=True, padx=(5, 10), pady=(10, 10)
        )
        self._setup_voice_ids_scroll()

    def _setup_decks_scroll(self):
        for widget in self.deck_scroll_frame.winfo_children():
            widget.destroy()

        for idx, deckname in enumerate(self.decks):
            rosetta_deck = self.decks[deckname]
            row_frame = customtkinter.CTkFrame(self.deck_scroll_frame)
            row_frame.pack(fill="both", expand=True, padx=10, pady=5)

            button = customtkinter.CTkButton(
                row_frame,
                text=deckname,
                command=lambda text=deckname: print("TODO: open deck {}".format(text)),
            )
            voice_ids = customtkinter.CTkLabel(
                row_frame, text=rosetta_deck.voice_ids_str()
            )
            edit_button = customtkinter.CTkButton(
                row_frame,
                text="edit",
                command=lambda rosetta_deck=rosetta_deck: self._deck_edit_popup(
                    rosetta_deck, already_exists=True
                ),
                fg_color="red",
            )

            button.pack(side="left", padx=(0, 10))
            voice_ids.pack(side="left", padx=(0, 10))
            edit_button.pack(side="right", padx=(10, 0))

    def _setup_voice_ids_scroll(self):
        for widget in self.voice_id_scroll_frame.winfo_children():
            widget.destroy()

        for idx, voice_id in enumerate(self.voice_ids):
            label = customtkinter.CTkLabel(
                self.voice_id_scroll_frame,
                text=voice_id,
            )

            label.grid(row=idx, column=0, padx=10, pady=(0, 10), sticky="ew")

    def _load_anki_deck(self):
        filepath = tkinter.filedialog.askopenfilename(
            title="Select anki deck",
            filetypes=(("Anki decks", "*.apkg"), ("All files", "*.*")),
        )
        if filepath is not None:
            proposed_deckname = (
                filepath.removesuffix(".apkg").split("/")[-1].split("\\")[-1]
            )
            deck = Deck(filepath, name=proposed_deckname)
            rosetta_deck = RosettaDeck(deck)
            self._deck_edit_popup(rosetta_deck, already_exists=False)

    def _add_voice_id(self):
        popup = customtkinter.CTkToplevel(self)
        popup.title("Add voice ID")
        popup.transient(self)
        popup.grab_set()

        popup_example_voice_id = customtkinter.CTkLabel(
            popup,
            text="i.e. en-US-Ava:DragonHDLatestNeural",
        )
        popup_example_voice_id.pack(padx=20, pady=10)

        popup_voice_id_var = tkinter.StringVar(value="")
        popup_voice_id = customtkinter.CTkEntry(
            popup,
            textvariable=popup_voice_id_var,
        )
        popup_voice_id.pack(fill="x", padx=20, anchor="w")

        def _on_ok():
            popup.destroy()
            voice_id = popup_voice_id_var.get()
            if len(voice_id) > 0:
                self.voice_ids.add(voice_id)
                self._setup_voice_ids_scroll()

        popup_ok = customtkinter.CTkButton(popup, text="OK", command=_on_ok)
        popup_ok.pack(padx=20, pady=10, anchor="w")

    def _deck_edit_popup(self, rosetta_deck, *, already_exists):
        popup = customtkinter.CTkToplevel(self)
        popup.title("Add/edit deck")
        popup.transient(self)
        popup.grab_set()

        popup_warning_label = customtkinter.CTkLabel(
            popup,
            text="(this action is destructive & will replace an existing deck with the same name)",
        )
        popup_warning_label.pack(padx=10, pady=10)

        popup_header_parent_frame = customtkinter.CTkFrame(popup)
        popup_header_parent_frame.pack(fill="both")

        popup_deckname_var = tkinter.StringVar(value=rosetta_deck.deck.name)
        popup_deckname = customtkinter.CTkEntry(
            popup_header_parent_frame, textvariable=popup_deckname_var
        )
        popup_deckname.pack(side="left", padx=10, pady=(0, 10), anchor="w")

        def _on_ok(rosetta_deck):
            popup.destroy()
            if already_exists:
                self.decks.pop(rosetta_deck.deck.name)
            deckname = popup_deckname_var.get()
            if len(deckname) > 0:
                rosetta_deck.deck.name = deckname
                self.decks[deckname] = rosetta_deck
                self._setup_decks_scroll()

        popup_ok = customtkinter.CTkButton(
            popup_header_parent_frame,
            text="OK",
            command=lambda rosetta_deck=rosetta_deck: _on_ok(rosetta_deck),
        )
        popup_ok.pack(side="right", padx=10, pady=10, anchor="w")

        popup_voice_id_parent_frame = customtkinter.CTkFrame(popup)
        popup_voice_id_parent_frame.pack(fill="both")

        def _setup_voice_id_frame(rosetta_deck):
            for widget in popup_voice_id_parent_frame.winfo_children():
                widget.destroy()

            def _setup_voice_id_scroll_and_return_pack(
                get_voice_ids,
                *,
                rosetta_deck,
                title,
                move_voice_id_text,
                move_voice_id_lambda,
                side,
                padx,
            ):
                def _on_move_voice_id(voice_id):
                    move_voice_id_lambda(voice_id)
                    _setup_voice_id_frame(rosetta_deck)

                popup_voice_id_scroll_frame = customtkinter.CTkScrollableFrame(
                    popup_voice_id_parent_frame, label_text=title
                )

                for idx, voice_id in enumerate(get_voice_ids(rosetta_deck)):
                    popup_voice_id_row_frame = customtkinter.CTkFrame(
                        popup_voice_id_scroll_frame
                    )
                    popup_voice_id_row_frame.pack(
                        fill="both", expand=True, padx=10, pady=5
                    )

                    label = customtkinter.CTkLabel(
                        popup_voice_id_row_frame,
                        text=voice_id,
                    )
                    label.pack(side="left", padx=10, pady=5)

                    move_button = customtkinter.CTkButton(
                        popup_voice_id_row_frame,
                        text=move_voice_id_text,
                        command=lambda voice_id=voice_id: _on_move_voice_id(voice_id),
                        fg_color="red",
                    )
                    move_button.pack(side="right", padx=10, pady=5)

                return lambda: popup_voice_id_scroll_frame.pack(
                    fill="both", side=side, expand=True, padx=padx, pady=10
                )

            pack_voice_id_scrolls = [
                _setup_voice_id_scroll_and_return_pack(
                    lambda rosetta_deck: rosetta_deck.voice_ids,
                    rosetta_deck=rosetta_deck,
                    title="Voice IDs",
                    move_voice_id_text="-",
                    move_voice_id_lambda=lambda voice_id: rosetta_deck.voice_ids.discard(
                        voice_id
                    ),
                    side="left",
                    padx=(10, 5),
                ),
                _setup_voice_id_scroll_and_return_pack(
                    lambda rosetta_deck: self.voice_ids - rosetta_deck.voice_ids,
                    rosetta_deck=rosetta_deck,
                    title="All voice IDs",
                    move_voice_id_text="+",
                    move_voice_id_lambda=lambda voice_id: rosetta_deck.voice_ids.add(
                        voice_id
                    ),
                    side="right",
                    padx=(5, 10),
                ),
            ]

            [pack() for pack in pack_voice_id_scrolls]

        _setup_voice_id_frame(rosetta_deck)

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
