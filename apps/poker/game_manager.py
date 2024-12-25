# poker/game_manager.py
from .config import PokerSettings
from .game_engine import RoundState, FoldAction, CallAction, CheckAction, RaiseAction, TerminalState
import eval7
from .rebel.player import ReBeL

class PokerGameManager:
    def __init__(self, session):
        self.session = session
        self.deck = eval7.Deck()
        self.settings = PokerSettings()
        self.rebel_bot = ReBeL()

    def _convert_action_to_string(self, action_type):
        """Convert action class to string representation"""
        action_map = {
            FoldAction: 'fold',
            CallAction: 'call',
            CheckAction: 'check',
            RaiseAction: 'raise'
        }
        return action_map.get(action_type, 'unknown')

    def _get_legal_actions(self, round_state):
        """Convert legal actions to string list"""
        legal_actions = round_state.legal_actions()
        return [self._convert_action_to_string(action) for action in legal_actions]

    def start_new_hand(self):
        """Initialize a new hand of poker"""
        self.deck.shuffle()
        player_cards = self.deck.deal(2)
        bot_cards = self.deck.deal(2)
        deck = self.deck
        
        # [ADDED] Debug print to show which cards the bot was dealt
        print(f"[DEBUG] Bot was dealt these cards: {bot_cards}")
        
        player_cards = [str(c) for c in player_cards]
        bot_cards = [str(c) for c in bot_cards]
        
        # Determine final street based on River of Blood rules
        final_street = 5
        # while self.deck.cards[final_street-1].suit in [1, 2]:  # Diamond or Heart
        #     final_street += 1
        # final_street = min(final_street, 48)

        # Initialize game state
        pips = [self.settings.SMALL_BLIND, self.settings.BIG_BLIND]
        stacks = [
            self.settings.STARTING_STACK - self.settings.SMALL_BLIND,
            self.settings.STARTING_STACK - self.settings.BIG_BLIND
        ]
        full_deck_as_strings = [str(c) for c in deck.cards]
        round_state = RoundState(
            button=0,
            street=0,
            final_street=final_street,
            pips=pips,
            stacks=stacks,
            hands=[player_cards, bot_cards],
            deck=full_deck_as_strings,
            previous_state=None
        )

        # Update session
        self.session.player_cards = [str(card) for card in player_cards]
        self.session.board_cards = []
        self.session.pot = sum(pips)
        self.session.player_stack = stacks[0]
        self.session.bot_stack = stacks[1]
        self.session.current_street = 'preflop'
        self.session.game_state = self._serialize_game_state(round_state)
        self.session.save()

        return {
            'pot': self.session.pot,
            'player_stack': self.session.player_stack,
            'bot_stack': self.session.bot_stack,
            'player_cards': self.convert_cards_to_display(player_cards),
            'board_cards': [],
            'legal_actions': self._get_legal_actions(round_state),
            'game_message': 'Your turn! Choose your action.'
        }

    def process_player_action(self, action_type, amount=0):
        """Process a player's action and get the bot's response"""
        round_state = self._deserialize_game_state(self.session.game_state)
        if round_state is None:  # Terminal state
            return {
                'pot': self.session.pot,
                'player_stack': self.session.player_stack,
                'bot_stack': self.session.bot_stack,
                'player_cards': self.convert_cards_to_display(self.session.player_cards),
                'board_cards': self.convert_cards_to_display(self.session.board_cards),
                'legal_actions': [],
                'hand_complete': True,
                'game_message': 'Hand complete! Start a new hand to continue.'
            }
        
        # Create action object
        action = self._create_action(action_type, amount, round_state)
        
        # Apply player's action
        next_state = round_state.proceed(action)
        
        # Get bot's response if hand isn't over
        try:
            if not isinstance(next_state, TerminalState):
                dummy_game_state = None  # ReBeL bot doesn't need this
                bot_action = self.rebel_bot.get_action(dummy_game_state, next_state, 1)
                next_state = next_state.proceed(bot_action)
                bot_action_msg = f"Bot {self._action_to_string(bot_action)}"
                print(f"[DEBUG] Bot's action: {bot_action_msg}")
            else:
                bot_action_msg = "Hand complete!"
        except Exception as e:
            print(f"Bot action error: {str(e)}")
            bot_action_msg = "Bot checks"
            if not isinstance(next_state, TerminalState):
                next_state = next_state.proceed(CheckAction())
                print("[DEBUG] Bot encountered an error and defaulted to check.")

        # Update session
        self._update_session_from_round_state(next_state)
        
        # Get visible board cards from appropriate state
        if isinstance(next_state, TerminalState) and next_state.previous_state:
            street = next_state.previous_state.street
            visible_cards = next_state.previous_state.deck[:street] if street > 0 else []
        else:
            street = next_state.street if not isinstance(next_state, TerminalState) else 0
            visible_cards = next_state.deck[:street] if street > 0 else []
        
        return {
            'pot': self.session.pot,
            'player_stack': self.session.player_stack,
            'bot_stack': self.session.bot_stack,
            'player_cards': self.convert_cards_to_display(self.session.player_cards),
            'board_cards': self.convert_cards_to_display(visible_cards),
            'legal_actions': self._get_legal_actions(next_state) if not isinstance(next_state, TerminalState) else [],
            'hand_complete': isinstance(next_state, TerminalState),
            'game_message': self._get_game_message(next_state, bot_action_msg)
        }
        
    def _create_action(self, action_type, amount, round_state):
        """Convert action_type string to action object"""
        if action_type == 'fold':
            return FoldAction()
        elif action_type == 'call':
            return CallAction()
        elif action_type == 'check':
            return CheckAction()
        elif action_type == 'raise':
            min_raise, max_raise = round_state.raise_bounds()
            amount = max(min_raise, min(max_raise, amount))
            return RaiseAction(amount)
        return CheckAction()

    def _action_to_string(self, action):
        """Convert action object to readable string"""
        if isinstance(action, FoldAction):
            return "folds"
        elif isinstance(action, CallAction):
            return "calls"
        elif isinstance(action, CheckAction):
            return "checks"
        elif isinstance(action, RaiseAction):
            return f"raises to {action.amount}"
        return "unknown action"

    def _get_game_message(self, round_state, bot_action_msg=""):
        """Generate appropriate game message based on state"""
        if isinstance(round_state, TerminalState):
            if round_state.deltas[0] > 0:
                return f"You win ${round_state.deltas[0]}! Click 'Start New Hand' to continue."
            elif round_state.deltas[0] < 0:
                return f"Bot wins ${-round_state.deltas[0]}. Click 'Start New Hand' to continue."
            else:
                return "It's a tie! Click 'Start New Hand' to continue."
        elif bot_action_msg:
            return f"{bot_action_msg}. Your turn!"
        return "Your turn! Choose your action."

    def _update_session_from_round_state(self, round_state):
        """Update session with current round state"""
        if isinstance(round_state, TerminalState):
            # Handle end of hand
            self.session.pot = 0
            self.session.player_stack += round_state.deltas[0]
            self.session.bot_stack += round_state.deltas[1]
            
            # Get final board cards from previous state
            if round_state.previous_state and round_state.previous_state.street > 0:
                street = round_state.previous_state.street
                visible_cards = round_state.previous_state.deck[:street]
                self.session.board_cards = [str(card) for card in visible_cards]
        else:
            # Update session with current state
            self.session.pot = sum(round_state.pips)
            self.session.player_stack = round_state.stacks[0]
            self.session.bot_stack = round_state.stacks[1]
            
            # Update board cards if we're past preflop
            if round_state.street > 0:
                visible_cards = round_state.deck[:round_state.street]
                self.session.board_cards = [str(card) for card in visible_cards]
            
            # Update street name
            if round_state.street == 0:
                self.session.current_street = 'preflop'
            elif round_state.street == 3:
                self.session.current_street = 'flop'
            elif round_state.street == 4:
                self.session.current_street = 'turn'
            elif round_state.street >= 5:
                self.session.current_street = 'river'
                
        # Save the new game state
        self.session.game_state = self._serialize_game_state(round_state)
        self.session.save()
        
    def _is_hand_complete(self, round_state):
        return hasattr(round_state, 'deltas')

    def convert_cards_to_display(self, cards):
        suits = {
            'h': {'name': 'hearts', 'symbol': '♥'},
            'd': {'name': 'diamonds', 'symbol': '♦'},
            'c': {'name': 'clubs', 'symbol': '♣'},
            's': {'name': 'spades', 'symbol': '♠'}
        }
        
        display_cards = []
        for card in cards:
            if isinstance(card, str):
                value = card[0].upper()
                suit = card[1].lower()
            else:
                value = str(card)[0].upper()
                suit = str(card)[1].lower()
                
            display_cards.append({
                'value': value,
                'suit': suits[suit]['name'],
                'suit_symbol': suits[suit]['symbol']
            })
        return display_cards

    def _serialize_game_state(self, round_state):
        if hasattr(round_state, 'deltas'):
            return {
                'terminal': True,
                'deltas': round_state.deltas
            }
        return {
            'button': round_state.button,
            'street': round_state.street,
            'final_street': round_state.final_street,
            'pips': round_state.pips,
            'stacks': round_state.stacks,
            'hands': [[str(c) for c in h] for h in round_state.hands],
            'deck': [str(c) for c in round_state.deck]
        }

    def _deserialize_game_state(self, state_dict):
        """Load deck/hands back as strings, which player.py wants."""
        if state_dict.get('terminal', False):
            return None

        return RoundState(
            button=state_dict['button'],
            street=state_dict['street'],
            final_street=state_dict['final_street'],
            pips=state_dict['pips'],
            stacks=state_dict['stacks'],
            hands=state_dict['hands'],  # list-of-lists of strings
            deck=state_dict['deck'],    # list of strings
            previous_state=None
        )
