# poker/game_engine.py
from collections import namedtuple
import eval7

# Game constants
SMALL_BLIND = 1
BIG_BLIND = 2
STARTING_STACK = 200
STREET_NAMES = ['Flop', 'Turn', 'River']

# Action types
FoldAction = namedtuple('FoldAction', [])
CallAction = namedtuple('CallAction', [])
CheckAction = namedtuple('CheckAction', [])
RaiseAction = namedtuple('RaiseAction', ['amount'])
TerminalState = namedtuple('TerminalState', ['deltas', 'previous_state'])

# Helper functions
CCARDS = lambda cards: ','.join(map(str, cards))
PCARDS = lambda cards: '[{}]'.format(' '.join(map(str, cards)))
PVALUE = lambda name, value: ', {} ({})'.format(name, value)
STATUS = lambda players: ''.join([PVALUE(p.name, p.bankroll) for p in players])

class RoundState(namedtuple('_RoundState', ['button', 'street', 'final_street', 'pips', 'stacks', 'hands', 'deck', 'previous_state'])):
    '''
    Encodes the game tree for one round of poker.
    '''
    # def showdown(self):
    #     '''
    #     Compares the players' hands and computes payoffs.
    #     '''
    #     score0 = eval7.evaluate(self.deck.peek(self.final_street) + self.hands[0])
    #     score1 = eval7.evaluate(self.deck.peek(self.final_street) + self.hands[1])
    #     if score0 > score1:
    #         delta = STARTING_STACK - self.stacks[1]
    #     elif score0 < score1:
    #         delta = self.stacks[0] - STARTING_STACK
    #     else:  # split the pot
    #         delta = (self.stacks[0] - self.stacks[1]) // 2
    #     return TerminalState([delta, -delta], self)
    def showdown(self):
        '''
        Compares the players' hands and computes payoffs.
        '''
        # Convert string cards back to eval7 Card objects for evaluation
        board_cards = [eval7.Card(card) for card in self.deck[:self.final_street]]
        hand0 = [eval7.Card(card) for card in self.hands[0]]
        hand1 = [eval7.Card(card) for card in self.hands[1]]
        
        score0 = eval7.evaluate(board_cards + hand0)
        score1 = eval7.evaluate(board_cards + hand1)
        
        if score0 > score1:
            delta = STARTING_STACK - self.stacks[1]
        elif score0 < score1:
            delta = self.stacks[0] - STARTING_STACK
        else:  # split the pot
            delta = (self.stacks[0] - self.stacks[1]) // 2
        return TerminalState([delta, -delta], self)

    def legal_actions(self):
        '''
        Returns a set which corresponds to the active player's legal moves.
        '''
        active = self.button % 2
        continue_cost = self.pips[1-active] - self.pips[active]
        if continue_cost == 0:
            bets_forbidden = (self.stacks[0] == 0 or self.stacks[1] == 0)
            return {CheckAction} if bets_forbidden else {CheckAction, RaiseAction}
        raises_forbidden = (continue_cost == self.stacks[active] or self.stacks[1-active] == 0)
        return {FoldAction, CallAction} if raises_forbidden else {FoldAction, CallAction, RaiseAction}

    def raise_bounds(self):
        '''
        Returns a tuple of the minimum and maximum legal raises.
        '''
        active = self.button % 2
        continue_cost = self.pips[1-active] - self.pips[active]
        max_contribution = min(self.stacks[active], self.stacks[1-active] + continue_cost)
        min_contribution = min(max_contribution, continue_cost + max(continue_cost, BIG_BLIND))
        return (self.pips[active] + min_contribution, self.pips[active] + max_contribution)

    def proceed_street(self):
        '''
        Resets the players' pips and advances the game tree to the next round of betting.
        '''
        if self.street == self.final_street:
            return self.showdown()
        new_street = 3 if self.street == 0 else self.street + 1
        return RoundState(1, new_street, self.final_street, [0, 0], self.stacks, self.hands, self.deck, self)

    def proceed(self, action):
        active = self.button % 2
        
        if isinstance(action, FoldAction):
            delta = (self.stacks[0] - STARTING_STACK 
                    if active == 0 else STARTING_STACK - self.stacks[1])
            return TerminalState([delta, -delta], self)
        
        elif isinstance(action, CallAction):
            if self.button == 0:
                # sb calls bb
                return RoundState(
                    button=1,
                    street=0,
                    final_street=self.final_street,
                    pips=[BIG_BLIND] * 2,
                    stacks=[STARTING_STACK - BIG_BLIND] * 2,
                    hands=self.hands,
                    deck=self.deck,
                    previous_state=self
                )
            new_pips = list(self.pips)
            new_stacks = list(self.stacks)
            contribution = new_pips[1 - active] - new_pips[active]
            new_stacks[active] -= contribution
            new_pips[active] += contribution
            
            state = RoundState(
                button=self.button + 1,
                street=self.street,
                final_street=self.final_street,
                pips=new_pips,
                stacks=new_stacks,
                hands=self.hands,
                deck=self.deck,
                previous_state=self
            )
            return state.proceed_street()
        
        elif isinstance(action, CheckAction):
            if (self.street == 0 and self.button > 0) or self.button > 1:
                return self.proceed_street()
            return RoundState(
                button=self.button + 1,
                street=self.street,
                final_street=self.final_street,
                pips=self.pips,
                stacks=self.stacks,
                hands=self.hands,
                deck=self.deck,
                previous_state=self
            )
        
        elif isinstance(action, RaiseAction):
            new_pips = list(self.pips)
            new_stacks = list(self.stacks)
            contribution = action.amount - new_pips[active]
            new_stacks[active] -= contribution
            new_pips[active] += contribution
            return RoundState(
                button=self.button + 1,
                street=self.street,
                final_street=self.final_street,
                pips=new_pips,
                stacks=new_stacks,
                hands=self.hands,
                deck=self.deck,
                previous_state=self
            )

        else:
            # Fallback if for some reason 'action' is none of the above
            raise ValueError(f"Unknown action type: {action}")


class GameState:
    '''
    Encodes the state of a multi-round poker game.
    '''
    def __init__(self, player_bankroll=0, bot_bankroll=0):
        self.player_bankroll = player_bankroll
        self.bot_bankroll = bot_bankroll
        self.round_num = 0
        
    def increment_round(self):
        self.round_num += 1

    def update_bankrolls(self, player_delta, bot_delta):
        self.player_bankroll += player_delta
        self.bot_bankroll += bot_delta