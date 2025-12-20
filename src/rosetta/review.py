import customtkinter
import fsrs


class Ui(customtkinter.CTkFrame):
    def __init__(self, controller, *, parent_frame, foundry):
        super().__init__(parent_frame)
        self.controller = controller

        self.foundry = foundry
        self.deck = None

        self._setup_ui()

    def _setup_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        self._setup_action_bar()

        self.reviewer_frame = customtkinter.CTkFrame(self)
        self.reviewer_frame.pack(fill="both", expand=True)
        self._setup_reviewer()

    def _setup_action_bar(self):
        parent_frame = customtkinter.CTkFrame(self)
        parent_frame.pack(fill="both")

        mainmenu_button = customtkinter.CTkButton(
            parent_frame,
            text="Main menu",
            command=self.controller.show_mainmenu,
            fg_color="grey",
        )
        mainmenu_button.pack(side="left", padx=10, pady=10, anchor="w")

        if self.deck is None:
            return

        deckname_label = customtkinter.CTkLabel(
            parent_frame,
            text=self.deck.name,
        )
        deckname_label.pack(side="left", padx=10, pady=10, anchor="w")

    def _setup_reviewer(self):
        for widget in self.reviewer_frame.winfo_children():
            widget.destroy()

        if self.deck is None:
            return

        review_card = self.deck.peak_next_review_card()
        if review_card is not None:
            self._setup_card_review(deck=self.deck, review_card=review_card)
        else:
            self._setup_review_ahead(deck=self.deck)

    def _setup_card_review(self, *, deck, review_card):
        inner_frame = customtkinter.CTkFrame(self.reviewer_frame)
        inner_frame.place(relx=0.5, rely=0.5, anchor="center")

        question_frame = customtkinter.CTkFrame(inner_frame)
        question_label = customtkinter.CTkLabel(
            question_frame, text=review_card.get_question()
        )
        question_label.pack(side="left")
        question_frame.pack(padx=5, pady=5)

        answer_frame = customtkinter.CTkFrame(inner_frame)

        def _setup_answer_frame(show):
            for widget in answer_frame.winfo_children():
                widget.destroy()

            show_answer_button = customtkinter.CTkButton(
                answer_frame,
                text="{} answer".format("show" if not show else "hide"),
                command=lambda show=not show: _setup_answer_frame(show),
            )

            if show:
                answer_label = customtkinter.CTkLabel(
                    answer_frame, text=review_card.get_answer()
                )
                answer_label.pack(side="right", padx=5, pady=5)

            show_answer_button.pack(side="left", padx=5, pady=5)
            answer_frame.pack(padx=5, pady=5)

        _setup_answer_frame(False)

        def _review(deck, card, rating):
            deck.review(card, rating=rating)
            self._setup_reviewer()

        rating_frame = customtkinter.CTkFrame(inner_frame)
        again_button = customtkinter.CTkButton(
            rating_frame,
            text="again",
            command=lambda deck=deck, card=review_card: _review(
                deck, card, fsrs.Rating.Again
            ),
        )
        hard_button = customtkinter.CTkButton(
            rating_frame,
            text="hard",
            command=lambda deck=deck, card=review_card: _review(
                deck, card, fsrs.Rating.Hard
            ),
        )
        good_button = customtkinter.CTkButton(
            rating_frame,
            text="good",
            command=lambda deck=deck, card=review_card: _review(
                deck, card, fsrs.Rating.Good
            ),
        )
        easy_button = customtkinter.CTkButton(
            rating_frame,
            text="easy",
            command=lambda deck=deck, card=review_card: _review(
                deck, card, fsrs.Rating.Easy
            ),
        )
        again_button.pack(side="left", padx=5, pady=5)
        hard_button.pack(side="left", padx=5, pady=5)
        good_button.pack(side="left", padx=5, pady=5)
        easy_button.pack(side="left", padx=5, pady=5)
        rating_frame.pack(padx=10, pady=10)

    def _setup_review_ahead(self, *, deck):
        inner_frame = customtkinter.CTkFrame(self.reviewer_frame)
        inner_frame.place(relx=0.5, rely=0.5, anchor="center")

        done_label = customtkinter.CTkLabel(inner_frame, text="No more cards to review")
        done_label.pack(padx=5, pady=5)

        def _review_ahead(deck):
            deck.review_ahead()
            self._setup_reviewer()

        review_ahead_button = customtkinter.CTkButton(
            inner_frame,
            text="Review ahead",
            command=lambda deck=deck: _review_ahead(deck),
        )
        review_ahead_button.pack(padx=5, pady=5)

    def show(self, deck):
        self.deck = deck
        self.foundry.update_speech_synthesizer(self.deck.voice_ids)
        self._setup_ui()
        self.tkraise()
