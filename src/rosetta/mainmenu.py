import tkinter
from tkinter import filedialog

import customtkinter
from ttkwidgets.autocomplete import AutocompleteCombobox

from .anki import Deck


class Ui(customtkinter.CTkFrame):
    def __init__(self, controller, *, parent_frame, foundry):
        super().__init__(parent_frame)
        self.controller = controller

        self.foundry = foundry

        self._setup_state()
        self._setup_ui()

    def _setup_state(self):
        self.decks = {}
        self.voice_ids = set()

    def _setup_ui(self):
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
            deck = self.decks[deckname]
            row_frame = customtkinter.CTkFrame(self.deck_scroll_frame)
            row_frame.pack(fill="both", expand=True, padx=10, pady=5)

            button = customtkinter.CTkButton(
                row_frame,
                text=deckname,
                command=lambda deck=deck: self.controller.show_review(deck),
            )
            voice_ids = customtkinter.CTkLabel(
                row_frame,
                text=", ".join(deck.voice_ids)
                if len(deck.voice_ids) > 0
                else "<please add at least 1 voice id>",
            )
            edit_button = customtkinter.CTkButton(
                row_frame,
                text="edit",
                command=lambda deck=deck: self._deck_edit_popup(
                    deck, already_exists=True
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
            row_frame = customtkinter.CTkFrame(self.voice_id_scroll_frame)
            row_frame.pack(fill="both", expand=True, padx=10, pady=5)

            label = customtkinter.CTkLabel(
                row_frame,
                text=voice_id,
            )

            def _on_delete(voice_id):
                self.voice_ids.discard(voice_id)
                self._setup_voice_ids_scroll()

            delete_button = customtkinter.CTkButton(
                row_frame,
                text="-",
                command=lambda voice_id=voice_id: _on_delete(voice_id),
                fg_color="red",
            )

            label.pack(side="left", padx=10)
            delete_button.pack(side="right", padx=10)

    def _load_anki_deck(self):
        filepath = filedialog.askopenfilename(
            title="Select anki deck",
            filetypes=(("Anki decks", "*.apkg"), ("All files", "*.*")),
        )
        if filepath is not None:
            proposed_deckname = (
                filepath.removesuffix(".apkg").split("/")[-1].split("\\")[-1]
            )
            deck = Deck(filepath, name=proposed_deckname)
            self._deck_edit_popup(deck, already_exists=False)

    def _add_voice_id(self):
        popup = customtkinter.CTkToplevel(self)
        popup.title("Add voice ID")
        popup.transient(self.controller)
        popup.grab_set()

        popup_example_voice_id = customtkinter.CTkLabel(
            popup,
            text="i.e. en-US-Ava:DragonHDLatestNeural",
        )
        popup_example_voice_id.pack(padx=20, pady=10)

        popup_voice_id_var = tkinter.StringVar(value="")
        popup_voice_id = AutocompleteCombobox(
            popup,
            completevalues=self.foundry.get_voice_id_list(),
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

    def _deck_edit_popup(self, deck, *, already_exists):
        popup = customtkinter.CTkToplevel(self)
        popup.title("Add/edit deck")
        popup.transient(self.controller)
        popup.grab_set()

        popup_warning_label = customtkinter.CTkLabel(
            popup,
            text="(this action is destructive & will replace an existing deck with the same name)",
        )
        popup_warning_label.pack(padx=10, pady=10)

        popup_header_parent_frame = customtkinter.CTkFrame(popup)
        popup_header_parent_frame.pack(fill="both")

        popup_deckname_var = tkinter.StringVar(value=deck.name)
        popup_deckname = customtkinter.CTkEntry(
            popup_header_parent_frame, textvariable=popup_deckname_var
        )
        popup_deckname.pack(side="left", padx=10, pady=(0, 10), anchor="w")

        def _on_ok(deck):
            popup.destroy()
            if already_exists:
                self.decks.pop(deck.name)
            deckname = popup_deckname_var.get()
            if len(deckname) > 0:
                deck.name = deckname
                self.decks[deckname] = deck
                self._setup_decks_scroll()

        popup_ok = customtkinter.CTkButton(
            popup_header_parent_frame,
            text="OK",
            command=lambda deck=deck: _on_ok(deck),
        )
        popup_ok.pack(side="right", padx=10, pady=10, anchor="w")

        popup_voice_id_parent_frame = customtkinter.CTkFrame(popup)
        popup_voice_id_parent_frame.pack(fill="both")

        def _setup_voice_id_frame(deck):
            for widget in popup_voice_id_parent_frame.winfo_children():
                widget.destroy()

            def _setup_voice_id_scroll_and_return_pack(
                get_voice_ids,
                *,
                deck,
                title,
                move_voice_id_text,
                move_voice_id_color,
                move_voice_id_lambda,
                side,
                padx,
            ):
                def _on_move_voice_id(voice_id):
                    move_voice_id_lambda(voice_id)
                    _setup_voice_id_frame(deck)

                popup_voice_id_scroll_frame = customtkinter.CTkScrollableFrame(
                    popup_voice_id_parent_frame, label_text=title
                )

                for idx, voice_id in enumerate(get_voice_ids(deck)):
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
                        fg_color=move_voice_id_color,
                    )
                    move_button.pack(side="right", padx=10, pady=5)

                return lambda: popup_voice_id_scroll_frame.pack(
                    fill="both", side=side, expand=True, padx=padx, pady=10
                )

            pack_voice_id_scrolls = [
                _setup_voice_id_scroll_and_return_pack(
                    lambda deck: deck.voice_ids,
                    deck=deck,
                    title="Voice IDs",
                    move_voice_id_text="-",
                    move_voice_id_color="red",
                    move_voice_id_lambda=lambda voice_id: deck.voice_ids.discard(
                        voice_id
                    ),
                    side="left",
                    padx=(10, 5),
                ),
                _setup_voice_id_scroll_and_return_pack(
                    lambda deck: self.voice_ids - deck.voice_ids,
                    deck=deck,
                    title="All voice IDs",
                    move_voice_id_text="+",
                    move_voice_id_color="green",
                    move_voice_id_lambda=lambda voice_id: deck.voice_ids.add(voice_id),
                    side="right",
                    padx=(5, 10),
                ),
            ]

            [pack() for pack in pack_voice_id_scrolls]

        _setup_voice_id_frame(deck)

    def show(self):
        self.tkraise()
