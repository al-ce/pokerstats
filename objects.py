# TODO: are you using this? Doesn't seem like it
from functools import total_ordering
from random import shuffle


def line_break():
    print("\n", end="")


def any_in(items: list, container: iter, are_in: bool) -> bool:
    """Checks if any item from list 'items' is in list 'container'. Returns
    True of False based on are_in param (are ANY items in/not here?)"""
    for item in items:
        if item in container and are_in:
            return True
    return False


def all_in(items: list, container: iter, are_in: bool) -> bool:
    """Checks if all items from list 'items' are in list 'container'. Returns
    True of False based on are_in param (are ALL items in/not here?)"""
    for item in items:
        if item not in container and are_in:
            return False
    return True


def debug_print(string):
    print(string)


@total_ordering
class Card:
    def __init__(self, suit: str, rank: tuple):
        # id is used to concisely display the card
        self.rank = rank[1]
        self.suit = suit
        self.location = -1
        self.id = f"{rank[0]}{suit}"

    def __lt__(self, other):
        return self.rank < other.rank

    def __repr__(self):
        return f"{self.id}"


class Deck:
    rank = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    suits = ["C", "D", "S", "H"]

    def __init__(self):
        self.cards = self.initialize_deck()

    def initialize_deck(self) -> list:
        """Return a shuffled deck (randomized list of Cards). Called on each
        round."""
        deck = []
        for suit in self.suits:
            for i in range(2, 15):
                card = Card(suit, (self.rank[i - 2], i))
                deck.append(card)
        shuffle(deck)
        return deck


class Player:
    def __init__(self, id: int):
        self.id = id
        self.hole = []
        # Hands are given to this object by the HandCalculator
        self.hands = None
        self.highest_hand = None

    def __repr__(self):
        return f"Player {self.id}: {self.hole}"


class Dealer:

    streets = {"3": "Flop", "4": "Turn", "5": "River"}

    def __init__(self, players: list):
        self.deck = self.get_new_deck()
        # List of Player() objects
        self.players = [player for player in players]
        self.community_cards = []

    def burn_card(self):
        self.deck.pop()

    def deal_test_hands(self):
        """Allow user to test specific hands."""

        def get_user_card_input(j: int) -> list:
            some_list = []
            for i in range(j):
                c = input(f"  Card {i+1}:")
                r = c[0]
                s = c[1]
                rank = Deck.rank.index(r)
                card = Card(s, (r, rank + 2))
                debug_print(card)
                debug_print(card.rank)
                some_list.append(card)
            return some_list

        for player in self.players:
            debug_print(f"Player {player.id}:")
            hole = get_user_card_input(2)
            player.hole = sorted(hole, reverse=True)

        debug_print("Board Cards:")
        comm_cards = get_user_card_input(5)
        self.community_cards = comm_cards

    def deal_card(self, location=0) -> Card:
        card = self.deck.pop()
        card.location = location
        # Place card at the "bottom" of the deck so it can be used in
        # calculating odds. Since it's marked by the location attribute, we
        # know whether it's really in the deck (-1) or elsewhere (0, 1, 2, ...)
        self.deck.insert(0, card)
        return card

    def deal_flop(self):
        self.burn_card()
        [self.deal_to_community_cards() for i in range(3)]

    def deal_river(self):
        self.deal_to_community_cards()

    def deal_to_community_cards(self):
        card = self.deal_card()
        self.community_cards.append(card)

    def deal_to_players(self):
        for player in self.players:
            hole = []
            for _ in range(2):
                card = self.deal_card(player.id)
                hole.append(card)
            player.hole = sorted(hole, reverse=True)

    def deal_turn(self):
        self.burn_card()
        self.deal_to_community_cards()

    def get_new_deck(self) -> list:
        """Returns a shuffled Deck of Cards."""
        return Deck().cards

    def which_street(self, length: int) -> str:
        """Return which street is on display based on len of community cards"""
        return self.streets.get(str(length))


class HandCalculator:
    """Takes a Player object and a deck of dealt cards and calculates the
    Player's valid hands and ranks them."""

    def __init__(self, community_cards: list, player: Player):
        # The order of these attributes should be fixed, as calculating the
        # value of one usually depends on calculating the previous ones.
        self.player = player
        self.hole = player.hole
        # TODO:: Might not need the comm_cards attr
        self.comm_cards = community_cards
        self.dealt = sorted(self.hole + self.comm_cards, reverse=True)

        self.report_hands_to_player()

    def report_hands_to_player(self):
        self.player.hands = self.get_hands(self.dealt)

    def get_hands(self, cards: list) -> dict:
        # Return a simplified dict based on player's hands
        hands = self.matches_check(cards)
        hands = self.sort_matches(hands)

        # The following hands don't use kickers to break ties, so we simplify
        # the dict we pass on.
        hands = self.full_house_or_set_check(hands)
        hands = self.quads_check(hands)
        hands = self.which_straight_or_flush(cards, hands)
        hands = self.two_pair_check(hands)
        hands = self.one_pair_check(hands)
        return hands

    def which_straight_or_flush(self, cards: list, hands: dict) -> dict:
        straight = self.straight_check(cards)
        flush = self.flush_check(cards)

        if flush and straight == flush[-1] and straight - 4 == flush[0]:
            if straight == 14:
                return {"Royal Flush": straight}
            return {"Straight Flush": straight}
        elif straight:
            return {"Straight": straight}
        elif flush:
            return {"Flush": flush[-1]}
        return hands

    def straight_check(self, cards: list) -> int:
        ranks = [card.rank for card in cards]
        for rank in ranks:
            test_range = range(rank, rank - 5, -1)
            if set(test_range).issubset(ranks):
                return max(test_range)

        ace_five = [2, 3, 4, 5, 14]
        if set(ace_five).issubset(ranks):
            return 5

    def flush_check(self, cards: list) -> list:
        suited_count = {}
        for card in cards:
            suit = card.suit
            if suit in suited_count:
                suited_count[suit] += 1
            else:
                suited_count[suit] = 1
        flush = None
        for suit, count in suited_count.items():
            if count >= 5:
                ranks = [card.rank for card in cards if card.suit == suit]
                flush = sorted(ranks)
        return flush

    def quads_check(self, hands: dict) -> dict:
        if "Quads" in hands:
            return {"Quads": hands.get("Quads")}
        return hands

    def two_pair_check(self, hands: dict) -> dict:
        pairs = ["One Pair", "Low Pair"]
        if "Set" not in hands and all_in(pairs, hands, True):
            two_pair_dict = {
                "Two Pair": hands.get("One Pair"),
                "Low Pair": hands.get("Low Pair"),
                # High Card is the kicker in this situation
                "High Card": hands.get("High Card"),
            }
            return two_pair_dict
        return hands

    def one_pair_check(self, hands: dict) -> dict:
        others = ["Two Pair", "Set"]
        if "One Pair" in hands and all_in(others, hands, False):
            kickers = ["High Card", "Second Kicker", "Third Kicker"]
            one_pair_dict = {"One Pair": hands.get("One Pair")}
            for kicker in kickers:
                if kicker in hands:
                    one_pair_dict[kicker] = hands.get(kicker)
            return one_pair_dict
        return hands

    def full_house_or_set_check(self, hands: dict) -> dict:
        full_house = ["Set", "One Pair"]
        if all_in(full_house, hands, True):
            full_house_dict = {
                "Full House": hands.get("Set"),
                "One Pair": hands.get("One Pair"),
            }
            return full_house_dict
        elif "Set" in hands:
            # Don't need a third kicker for Set tiebreakers
            set_dict = {
                "Set": hands.get("Set"),
                "High Card": hands.get("High Card"),
                "Second Kicker": hands.get("Second Kicker"),
            }
            return set_dict
        return hands

    def matches_check(self, cards: list) -> dict:
        """Check for which cards match among the hole and comm cards."""

        matches = {}
        for card in cards:
            rank = card.rank
            if rank in matches:
                matches[rank] += 1
            else:
                matches[rank] = 1
        # Return a copy of matches dict with only keys with list of len 2+
        matches = {rank: size for rank, size in matches.items() if size > 1}
        return matches

    def sort_matches(self, matches: dict) -> dict:
        match_types = {2: "One Pair", 3: "Set", 4: "Quads"}
        hands = {
            "Low Pair": 0,
            "One Pair": 0,
            "Set": 0,
            "Quads": 0,
        }

        for rank, size in matches.items():
            match_type = match_types[size]
            temp = hands.get(match_type)
            if size == 2 and rank > temp:
                hands[match_type] = rank
                hands["Low Pair"] = temp
            elif size == 2 and rank < temp:
                low_pair = hands.get("Low Pair")
                # Ensure a third pair doesn't overwrite the lower of first two
                if low_pair == 0 or (low_pair != 0 and rank > low_pair):
                    hands["Low Pair"] = rank

            elif size == 3 and rank > hands.get("Set") and temp > 0:
                hands["Low Pair"] = hands.get("One Pair")
                hands["One Pair"] = temp
                hands["Set"] = rank
            elif size == 3 and rank < temp:
                hands["Low Pair"] = hands.get("One Pair")
                hands["One Pair"] = rank

            elif rank > temp:
                hands[match_type] = rank

        hands = self.add_kickers_to_hands(hands)

        return hands

    def add_kickers_to_hands(self, hands: dict) -> dict:
        # We only check against the matched ranks (ranks that are in pairs,
        # sets, or quads) because kickers are irrelevant in straights/flushes.
        matched_ranks = hands.values()
        dealt_ranks = []
        for card in self.dealt:
            if card.rank not in matched_ranks:
                dealt_ranks.append(card.rank)

        dealt_ranks.sort(reverse=True)
        # The number of unique dealt ranks
        length = len(dealt_ranks)
        hands["High Card"] = dealt_ranks[0] if dealt_ranks else 0
        kickers = ["Second", "Third", "Fourth", "Fifth"]
        i = 1
        for kicker in kickers:
            hands[f"{kicker} Kicker"] = dealt_ranks[i] if length > i else 0
            i += 1

        # hands["Second Kicker"] = dealt_ranks[1] if length > 1 else 0
        # hands["Third Kicker"] = dealt_ranks[2] if length > 2 else 0
        # hands["Fourth Kicker"] = dealt_ranks[3] if length > 3 else 0
        # hands["Fifth Kicker"] = dealt_ranks[4] if length > 4 else 0

        return {k: v for k, v in hands.items() if v > 0}


class WinCalculator:

    rank_types = [
        "Royal Flush",
        "Straight Flush",
        "Quads",
        "Full House",
        "Flush",
        "Straight",
        "Set",
        "Two Pair",
        "One Pair",
        "High Card",
    ]

    card_ranks = [
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "Jack",
        "Queen",
        "King",
        "Ace",
    ]

    def __init__(self, players: list):
        self.players = players
        self.hands = sorted([(player.id, player.hands) for player in players])

        top_hands, top_ranked_hand = self.get_top_hands(self.hands)

        # TODO: Here's the top hands in the dealt cards
        # Prints as many player's hands as those that have the highest ranked
        # hand, and that hand (an attr for the Player obj)
        for pid, pdata in top_hands:
            debug_print(f"\\*\\{pid}\n\\*\\{self.players[pid - 1].highest_hand}")
            print(f"  {pdata}\n")
            # input("")

        win = self.resolve_ties(top_hands, top_ranked_hand)
        if win:
            print("--------")
            # TODO: this prints "win" mesage, but need to say how.
            # Also make print_msg its own method
            print(win)
            print("--------")

        # TODO: returns None, should return proper winner and winning hand etc.
        return None
        # input("")
        # self.determine_winner(top_hands)

    def designate_player_win_status(self, player_id):
        """Designates whether a player won in a hand, including split pots."""
        self.players[player_id - 1].is_winner = True

    def get_card_name(self, card_rank: int) -> str:
        """Converts a card's rank by int to its corresponding str.
        Relevant for face cards."""
        return self.card_ranks[card_rank - 2]

    def get_top_hands(self, hands: list) -> tuple:
        def set_player_highest_hand(player_id: int, hand_rank: str):
            self.players[player_id - 1].highest_hand = hand_rank

        temp_rank_data = {rank: [] for rank in self.rank_types}

        # for player id, all player's hands in self.hands
        for p_id, p_data in self.hands:
            # for the key 'rank' (value of []) in temp_rank_data
            for rank in temp_rank_data:
                # if the player has that rank in their hand
                if rank in p_data:
                    # append that player(s) & their data to the list, ignoring
                    # all other rank keys.
                    temp_rank_data[rank].append((p_id, p_data))
                    set_player_highest_hand(p_id, rank)
                    break

        # Remove empty keys
        sorted_players = {k: v for k, v in temp_rank_data.items() if v}
        # Only return highest ranked players/top hands by finding the first
        # non-empty key in the dict (which, since it's sorted, will be the
        # highest). Returns a list of tuples:
        # (player_id, {'hand_type': highest_ranked_card_in_that_hand})
        # and the top ranked hand (str)
        for rank in self.rank_types:
            if rank in sorted_players:
                top_hands = sorted_players.get(rank)
                return top_hands, rank

    def tag_msg(self, hand_type: str, card_name: str, msg: str) -> str:
        # Tags to put at the end of the message based on certain hand types
        if hand_type == "Royal Flush":
            return "\nRoyal Flush"
        elif hand_type == "High Card":
            return f"\n{card_name}-high"
        _high = ["Straight Flush", "Straight", "Flush"]
        suffix = " high" if hand_type in _high else "s"
        tag = f"\n{hand_type}, {card_name}{suffix}"
        return f"{msg}{tag}"

    def split_pot_msg(self, winners: list) -> str:
        msg = "Split Pot -"
        for player in winners:

            player_id = player[0]
            msg += f" Player {player_id},"
        return msg[:-1]

    def full_house_ties(self, top_hands: list, hand_type, card_name) -> str:
        """Resolve ties for a full house."""
        # Full houses tied by the set are resolved by the pair in the FH.
        # If that is also a tie, the pot is split.

        winners, pair_rank = self.tiebreaker_info(top_hands, "One Pair")
        if len(winners) > 1:
            msg = self.split_pot_msg(winners)
        else:
            player_id = winners[0][0]
            msg = f"Player {player_id} wins!"
        msg += f"\n{hand_type}, {card_name}s full of {pair_rank}s"
        return msg

    def _SFQ_ties(self, top_hands: list, hand_type, card_name) -> str:
        """Resolve ties for straights, flushes, or quads."""
        if len(top_hands) > 1:
            msg = self.split_pot_msg(top_hands)
        else:
            player_id = top_hands[0][0]
            msg = f"Player {player_id} wins!"
        msg = self.tag_msg(hand_type, card_name, msg)
        return msg

    def get_highest_value(self, top_hands: list, hand_type: str) -> int:
        # Return the highest rank of a given hand type (h_type).
        # top_hands = [(int, {hand_type: rank})]
        _list = sorted(top_hands, key=lambda d: d[1][hand_type], reverse=True)
        high_card = _list[0][1].get(hand_type)
        return high_card

    def potential_winners(
        self, top_hands: list, hand_type: str, high_card: int
    ) -> list:
        # Return a list of potential winners, i.e. all players that
        # have the highest ranking card of a given hand type (h_type)
        winners = []
        for pid, data in top_hands:
            if data.get(hand_type) == high_card:
                winners.append((pid, data))
        return winners

    def tiebreaker_info(self, top_hnds: list, hand_type: str) -> tuple:

        high_card = self.get_highest_value(top_hnds, hand_type)
        winners = self.potential_winners(top_hnds, hand_type, high_card)
        card_name = self.get_card_name(high_card)
        return winners, card_name

    def resolve_ties(self, top_hands: list, hand_type: str) -> list:
        """Return the winner(s) of the round and break ties if needed by
        calling the relevant tie breaking function."""

        func_call = {
            "Royal Flush": self._SFQ_ties,
            "Straight Flush": self._SFQ_ties,
            "Quads": self._SFQ_ties,
            "Full House": self.full_house_ties,
            "Flush": self._SFQ_ties,
            "Straight": self._SFQ_ties,
            "Set": print,
            "Two Pair": print,
            "One Pair": print,
            "High Card": print,
        }

        # Gather the first round of relevant info. Some of the tiebreaking info
        # functions might need to be called again depending on the kind of tie
        # that needs to be broken, e.g. a full house that needs to be broken by
        # the pair, a set or high card broken by one or more kickers, etc.
        winners, card_name = self.tiebreaker_info(top_hands, hand_type)
        msg = func_call[hand_type](winners, hand_type, card_name)
        return msg


def main(d: Dealer):

    # TODO: make an 'auto-deal' func that automates these
    d.deal_to_players()
    d.deal_flop()
    d.deal_turn()
    d.deal_river()

    # d.deal_test_hands()

    for player in d.players:
        h = HandCalculator(d.community_cards, player)

        debug_print(h.hole)
        debug_print(h.comm_cards)
        debug_print("**********")
        # hands = h.get_hands(h.dealt)

    w = WinCalculator(d.players)
    debug_print("----------------------------------------")

    # debug_print(hands)
    # if "Two Pair" in hands:
    #     input("")
    # debug_print("**********")

    # s = h.straight_check(h.dealt)
    # if s:
    #     debug_print(s)
    #     input("")
    #
    # f = h.flush_check(h.dealt)
    # if f:
    #     debug_print(f)
    #     input("")

    # matches = h.matches_check(h.dealt)
    # debug_print(matches)
    # sorted_matches = h.sort_matches(matches)

    # for k, v in sorted_matches.items():
    #     debug_print(k, ':', v)

    # if "Low Pair" in sorted_matches:
    #     input("")
    # if "Set" in sorted_matches and "One Pair" in sorted_matches:
    #     input("")
    # if "Set" in sorted_matches and "Low Pair" in sorted_matches:
    #     input("")
    # if "Quads" in sorted_matches:
    #     input("")

    line_break()
    line_break()


i = 2
players = [Player(i + 1) for i in range(i)]

for i in range(200000):
    d = Dealer(players)
    main(d)
