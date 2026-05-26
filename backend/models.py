from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from copy import deepcopy

CARD_VALUE = {
    "A": 1, "2": 2, "3": 3, "4": 4, "5": 5,
    "6": 6, "7": 7, "8": 8, "9": 9,
    "10": 10, "J": 10, "Q": 10, "K": 10,
}

INITIAL_DECK = {
    1: 4,   # Ace
    2: 4,   # 2
    3: 4,   # 3
    4: 4,   # 4
    5: 4,   # 5
    6: 4,   # 6
    7: 4,   # 7
    8: 4,   # 8
    9: 4,   # 9
    10: 16, # 10, J, Q, K
}

RANK_DISPLAY = {
    1: "A", 2: "2", 3: "3", 4: "4", 5: "5",
    6: "6", 7: "7", 8: "8", 9: "9", 10: "10",
    11: "J", 12: "Q", 13: "K",
}

SUIT_DISPLAY = {
    "hearts": "♥",
    "diamonds": "♦",
    "clubs": "♣",
    "spades": "♠",
}

SUIT_COLOR = {
    "hearts": "red",
    "diamonds": "red",
    "clubs": "black",
    "spades": "black",
}


def parse_card(s: str) -> int:
    s = s.strip().upper()
    if s in ("A", "ACE"):
        return 1
    if s in ("J", "JACK"):
        return 10
    if s in ("Q", "QUEEN"):
        return 10
    if s in ("K", "KING"):
        return 10
    try:
        v = int(s)
        if 1 <= v <= 10:
            return v if v != 1 else 1
        raise ValueError(f"Valor de carta invalido: {s}")
    except ValueError:
        raise ValueError(f"Carta invalida: {s}")


def card_rank_to_shoe_value(rank: int) -> int:
    if rank >= 10:
        return 10
    return rank


class Hand:
    def __init__(self, cards: List[str] = None):
        self.cards: List[str] = cards or []

    def add_card(self, card: str):
        self.cards.append(card)

    def _values(self) -> List[int]:
        return [CARD_VALUE[c.upper()] for c in self.cards]

    def _has_ace(self) -> bool:
        return any(c.upper() == "A" for c in self.cards)

    @property
    def hard_total(self) -> int:
        return sum(self._values())

    @property
    def soft_total(self) -> int:
        t = self.hard_total
        if self._has_ace() and t + 10 <= 21:
            return t + 10
        return t

    @property
    def best_total(self) -> int:
        s = self.soft_total
        if s <= 21:
            return s
        return self.hard_total

    @property
    def is_soft(self) -> bool:
        return self._has_ace() and self.hard_total + 10 <= 21

    @property
    def is_bust(self) -> bool:
        return self.hard_total > 21

    @property
    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.soft_total == 21

    @property
    def is_pair(self) -> bool:
        if len(self.cards) != 2:
            return False
        return CARD_VALUE[self.cards[0].upper()] == CARD_VALUE[self.cards[1].upper()]

    @property
    def pair_rank(self) -> int:
        if not self.is_pair:
            return 0
        return CARD_VALUE[self.cards[0].upper()]

    def copy(self) -> "Hand":
        return Hand(list(self.cards))


class Shoe:
    def __init__(self, num_decks: int = 6):
        self.num_decks = num_decks
        self.counts: Dict[int, int] = {}
        self._reset()

    def _reset(self):
        self.counts = {k: v * self.num_decks for k, v in INITIAL_DECK.items()}

    @property
    def total_cards(self) -> int:
        return sum(self.counts.values())

    def remove_card_by_value(self, value: int):
        v = value if value <= 10 else 10
        if self.counts.get(v, 0) > 0:
            self.counts[v] -= 1

    def remove_card(self, card_str: str):
        v = CARD_VALUE[card_str.strip().upper()]
        self.remove_card_by_value(v)

    def remove_cards(self, cards: List[str]):
        for c in cards:
            self.remove_card(c)

    def probability(self, value: int) -> float:
        tc = self.total_cards
        if tc == 0:
            return 0.0
        return self.counts.get(value, 0) / tc

    def copy(self) -> "Shoe":
        s = Shoe(self.num_decks)
        s.counts = dict(self.counts)
        return s

    def to_dict(self) -> dict:
        return {
            "num_decks": self.num_decks,
            "remaining": dict(self.counts),
            "total_remaining": self.total_cards,
            "by_label": {
                "A": self.counts[1],
                "2": self.counts[2],
                "3": self.counts[3],
                "4": self.counts[4],
                "5": self.counts[5],
                "6": self.counts[6],
                "7": self.counts[7],
                "8": self.counts[8],
                "9": self.counts[9],
                "10": self.counts[10],
            }
        }


@dataclass
class Rules:
    num_decks: int = 6
    dealer_stands_soft_17: bool = True
    double_any_two: bool = True
    double_9_10_11_only: bool = False
    double_10_11_only: bool = False
    double_after_split: bool = True
    max_splits: int = 3
    late_surrender: bool = True
    blackjack_pays: float = 1.5
    resplit_aces: bool = True
    hit_split_aces: bool = False

    def can_double(self, total: int) -> bool:
        if self.double_10_11_only:
            return total in (10, 11)
        if self.double_9_10_11_only:
            return total in (9, 10, 11)
        if self.double_any_two:
            return True
        return False

    def dealer_hit_target(self) -> int:
        return 18 if self.dealer_stands_soft_17 else 17
