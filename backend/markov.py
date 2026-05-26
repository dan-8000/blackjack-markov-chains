from functools import lru_cache
from collections import defaultdict
from typing import Dict, List, Tuple

from .models import CARD_VALUE, Hand, Shoe, Rules


def parse_cards(hand_str: str) -> List[str]:
    if not hand_str.strip():
        return []
    return [c.strip() for c in hand_str.split(",")]


def _card_val(rank: str) -> int:
    return CARD_VALUE[rank.strip().upper()]


def _dealer_must_hit(total: int, is_soft: bool, rules: Rules) -> bool:
    if total > 21:
        return False
    if total < 17:
        return True
    if total == 17 and is_soft and not rules.dealer_stands_soft_17:
        return True
    return False


def _apply_card(total: int, is_soft: bool, value: int) -> Tuple[int, bool]:
    if value == 1:
        if total + 11 <= 21:
            return (total + 11, True)
        else:
            new_total = total + 1
            if is_soft and new_total > 21:
                new_total -= 10
            return (new_total, False)

    new_total = total + value
    if is_soft:
        if new_total > 21:
            return (new_total - 10, False)
        else:
            return (new_total, True)
    else:
        return (new_total, False)


def _dealer_distribution(dealer_upcard: int, shoe: Shoe, rules: Rules) -> Dict[int, float]:

    @lru_cache(maxsize=100)
    def _draw(total: int, is_soft: bool) -> Dict[int, float]:
        if not _dealer_must_hit(total, is_soft, rules):
            return {total: 1.0}

        result = defaultdict(float)
        tc = shoe.total_cards
        if tc == 0:
            return {total: 1.0}

        for value, count in shoe.counts.items():
            if count == 0:
                continue
            prob = count / tc
            new_total, new_soft = _apply_card(total, is_soft, value)
            sub = _draw(new_total, new_soft)
            for ft, fp in sub.items():
                result[ft] += prob * fp

        return dict(result)

    result = defaultdict(float)
    tc = shoe.total_cards
    if tc == 0:
        return {dealer_upcard: 1.0}

    for hole_val, hole_cnt in shoe.counts.items():
        if hole_cnt == 0:
            continue
        prob = hole_cnt / tc

        hard = dealer_upcard + hole_val
        has_ace = (dealer_upcard == 1 or hole_val == 1)
        if has_ace and hard + 10 <= 21:
            start_total = hard + 10
            start_soft = True
        else:
            start_total = hard
            start_soft = False

        sub = _draw(start_total, start_soft)
        for final_total, final_prob in sub.items():
            result[final_total] += prob * final_prob

    return dict(result)


def _stand_result(player_total: int, dealer_upcard: int, shoe: Shoe, rules: Rules) -> float:
    if player_total > 21:
        return -1.0
    dist = _dealer_distribution(dealer_upcard, shoe, rules)
    ev = 0.0
    for dealer_total, prob in dist.items():
        if dealer_total > 21:
            ev += prob * 1.0
        elif player_total > dealer_total:
            ev += prob * 1.0
        elif player_total < dealer_total:
            ev += prob * -1.0
    return ev


def compute_evs(
    player_hand: Hand,
    dealer_upcard_str: str,
    shoe: Shoe,
    rules: Rules,
    splits_remaining: int = None,
    is_double_allowed: bool = True,
    is_surrender_allowed: bool = True,
) -> Dict[str, Tuple[float, str]]:
    """
    Calcula el valor esperado (EV) de cada accion legal.

    Retorna un dict: {accion: (ev, "RECOMENDADO" | "")}
    """
    if splits_remaining is None:
        splits_remaining = rules.max_splits

    dealer_upcard = _card_val(dealer_upcard_str)
    player_total = player_hand.best_total
    is_soft = player_hand.is_soft

    results: Dict[str, float] = {}

    if player_hand.is_blackjack:
        return {"BLACKJACK": (rules.blackjack_pays, "RECOMENDADO")}

    if player_total > 21:
        return {"BUST": (-1.0, "")}

    if is_surrender_allowed and rules.late_surrender:
        results["RENDIRSE"] = -0.5

    stand_ev = _stand_result(player_total, dealer_upcard, shoe, rules)
    results["PLANTARSE"] = stand_ev

    @lru_cache(maxsize=2000)
    def _hit_ev(total: int, soft: bool, can_double: bool) -> float:
        ev = 0.0
        tc = shoe.total_cards
        if tc == 0:
            return 0.0

        for value, count in shoe.counts.items():
            if count == 0:
                continue
            prob = count / tc
            new_total, new_soft = _apply_card(total, soft, value)

            if new_total > 21:
                ev += prob * (-1.0)
            else:
                s_ev = _stand_result(new_total, dealer_upcard, shoe, rules)
                if can_double:
                    h_ev = _hit_ev(new_total, new_soft, False)
                    ev += prob * max(s_ev, h_ev)
                else:
                    ev += prob * max(s_ev, _hit_ev(new_total, new_soft, False))

        return ev

    hit_ev = _hit_ev(player_total, is_soft, False)
    results["PEDIR"] = hit_ev

    if is_double_allowed and len(player_hand.cards) == 2 and rules.can_double(player_total):
        double_ev = 0.0
        tc = shoe.total_cards
        for value, count in shoe.counts.items():
            if count == 0:
                continue
            prob = count / tc
            new_total, _ = _apply_card(player_total, is_soft, value)
            if new_total > 21:
                double_ev += prob * (-2.0)
            else:
                s_ev = _stand_result(new_total, dealer_upcard, shoe, rules)
                double_ev += prob * 2.0 * s_ev
        results["DOBLAR"] = double_ev

    if player_hand.is_pair and splits_remaining > 0:
        split_ev = 0.0
        pair_val = player_hand.pair_rank

        tc = shoe.total_cards
        if tc > 0:
            for value1, cnt1 in shoe.counts.items():
                if cnt1 == 0:
                    continue
                p1 = cnt1 / tc
                hand1 = Hand([_val_to_str(pair_val), _val_to_str(value1)])
                ev1 = max(
                    _hit_ev(hand1.best_total, hand1.is_soft, rules.double_after_split),
                    _stand_result(hand1.best_total, dealer_upcard, shoe, rules),
                )

                for value2, cnt2 in shoe.counts.items():
                    if cnt2 == 0:
                        continue
                    p2 = cnt2 / tc
                    hand2 = Hand([_val_to_str(pair_val), _val_to_str(value2)])
                    ev2 = max(
                        _hit_ev(hand2.best_total, hand2.is_soft, rules.double_after_split),
                        _stand_result(hand2.best_total, dealer_upcard, shoe, rules),
                    )
                    split_ev += p1 * p2 * (ev1 + ev2)

        results["DIVIDIR"] = split_ev

    best_action = max(results, key=lambda k: results[k])
    return {k: (v, "RECOMENDADO" if k == best_action else "") for k, v in results.items()}


def compute_full_breakdown(
    player_hand: Hand,
    dealer_upcard_str: str,
    shoe: Shoe,
    rules: Rules,
) -> dict:
    """
    Devuelve EVs + desglose de probabilidades para cada accion.
    """
    evs = compute_evs(player_hand, dealer_upcard_str, shoe, rules)

    dealer_upcard = _card_val(dealer_upcard_str)
    dealer_dist = _dealer_distribution(dealer_upcard, shoe, rules)

    dist_formatted = {}
    for total, prob in dealer_dist.items():
        label = "BUST" if total > 21 else str(total)
        dist_formatted[label] = dist_formatted.get(label, 0) + prob * 100
    dist_formatted = {k: round(v, 2) for k, v in dist_formatted.items()}

    return {
        "jugador": {
            "cartas": player_hand.cards,
            "total": player_hand.best_total,
            "es_suave": player_hand.is_soft,
            "es_blackjack": player_hand.is_blackjack,
            "es_par": player_hand.is_pair,
        },
        "crupier": {
            "carta_visible": dealer_upcard_str.upper(),
            "distribucion_final": dist_formatted,
        },
        "acciones": {
            accion: {"valor_esperado": round(ev, 4), "recomendada": tag == "RECOMENDADO"}
            for accion, (ev, tag) in evs.items()
        },
        "zapato": shoe.to_dict(),
    }


def _val_to_str(value: int) -> str:
    if value == 1:
        return "A"
    elif 2 <= value <= 9:
        return str(value)
    else:
        return "10"
