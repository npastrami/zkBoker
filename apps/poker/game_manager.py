# poker/game_manager.py
from .config import PokerSettings
from .game_engine import RoundState, FoldAction, CallAction, CheckAction, RaiseAction, TerminalState
import eval7
from .rebel.player import ReBeL

class PokerGameManager:
    def __init__(self, session):
        self.session = session
        self.player = session.player
        self.deck = eval7.Deck()
        self.settings = PokerSettings()
        self.rebel_bot = ReBeL()
        self.buy_in_amount = 200
        self.total_pot = 0
        self.player_total_bet = 0 
        self.bot_total_bet = 0

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
    
    def validate_buy_in(self):
        """Validate if player has enough coins for buy-in"""
        return self.player.coins >= self.buy_in_amount

    def process_buy_in(self):
        """Process the buy-in transaction"""
        if not self.validate_buy_in():
            return False, "Insufficient coins for buy-in"
        
        try:
            self.player.remove_coins(self.buy_in_amount)
            self.player.save()
            self.session.current_coins = self.buy_in_amount
            self.session.save()
            return True, "Buy-in successful"
        except ValueError as e:
            return False, str(e)

    def process_exit_game(self):
        """Process player exit and return remaining coins"""
        try:
            # Get remaining stack
            remaining_stack = self.session.player_stack
            if remaining_stack > 0:
                # Add coins back to player's account
                self.player.add_coins(remaining_stack)
                
                # Update session
                self.session.current_coins = 0
                self.session.player_stack = 0
                self.session.save()
                
                print(f"Successfully returned {remaining_stack} coins to {self.player.username}")
                return remaining_stack
            return 0
        except Exception as e:
            print(f"Error in process_exit_game: {str(e)}")
            raise e

    def start_new_hand(self, continue_session=False):
        """Initialize a new hand of poker"""
        self.total_pot = 0
        self.player_total_bet = 0
        self.bot_total_bet = 0
        if not continue_session and (not hasattr(self.session, 'current_coins') or self.session.current_coins == 0):
            return {
                'requires_buy_in': True,
                'buy_in_amount': self.buy_in_amount
            }
        self.deck.shuffle()
        player_cards = self.deck.deal(2)
        bot_cards = self.deck.deal(2)
        
        print(f"[DEBUG] Bot was dealt these cards: {bot_cards}")
        
        player_cards = [str(c) for c in player_cards]
        bot_cards = [str(c) for c in bot_cards]
        
        # If continuing session, use existing stacks
        if continue_session:
            starting_player_stack = self.session.player_stack
            starting_bot_stack = self.session.bot_stack
            # Alternate button position each hand
            button = 1 if self.session.game_state.get('button', 0) == 0 else 0
        else:
            starting_player_stack = self.settings.STARTING_STACK
            starting_bot_stack = self.settings.STARTING_STACK
            button = 0  # Player starts as dealer
        
        # Initialize blinds based on button position
        if button == 0:  # Player is dealer/button
            pips = [self.settings.SMALL_BLIND, self.settings.BIG_BLIND]  # [player, bot]
            stacks = [
                starting_player_stack - self.settings.SMALL_BLIND,
                starting_bot_stack - self.settings.BIG_BLIND
            ]
        else:  # Bot is dealer/button
            pips = [self.settings.BIG_BLIND, self.settings.SMALL_BLIND]  # [player, bot]
            stacks = [
                starting_player_stack - self.settings.BIG_BLIND,
                starting_bot_stack - self.settings.SMALL_BLIND
            ]
        
        # Initialize round state
        round_state = RoundState(
            button=button,
            street=0,
            final_street=5,
            pips=pips,
            stacks=stacks,
            hands=[player_cards, bot_cards],
            deck=[str(c) for c in self.deck.cards],
            previous_state=None
        )

        # Update session
        self.session.player_cards = player_cards
        self.session.board_cards = []
        self.session.pot = sum(pips)  # Track pot correctly
        self.session.player_stack = stacks[0]
        self.session.bot_stack = stacks[1]
        self.session.current_street = 'preflop'
        self.session.game_state = self._serialize_game_state(round_state)
        self.session.save()
        
        # Determine first to act based on street and button position
        is_player_turn = button == 0 and round_state.street > 0 or button == 1 and round_state.street == 0

        return {
            'requires_buy_in': False,
            'pot': self.session.pot,
            'player_stack': self.session.player_stack,
            'bot_stack': self.session.bot_stack,
            'player_cards': self.convert_cards_to_display(player_cards),
            'board_cards': [],
            'legal_actions': self._get_legal_actions(round_state) if is_player_turn else [],
            'game_message': 'Your turn!' if is_player_turn else 'Waiting for bot...'
        }
        
    def process_player_action(self, action_type, amount=0):
        """Process a player's action and get the bot's response"""
        round_state = self._deserialize_game_state(self.session.game_state)
        print(f"[DEBUG] Initial state - Pot: {self.session.pot}, Player Stack: {self.session.player_stack}, Bot Stack: {self.session.bot_stack}")
        
        if round_state is None:  # Terminal state
            print("[DEBUG] Terminal state detected at start")
            return self._create_terminal_response()
        
        # Store current state for tracking changes
        initial_state = {
            'player_stack': self.session.player_stack,
            'bot_stack': self.session.bot_stack,
            'pot': self.session.pot,
            'pips': round_state.pips.copy() if hasattr(round_state, 'pips') else [0, 0],
            'street': round_state.street if hasattr(round_state, 'street') else 0
        }
        print(f"[DEBUG] Initial pips: {initial_state['pips']}, Initial stacks - Player: {initial_state['player_stack']}, Bot: {initial_state['bot_stack']}")
        
        # Create and apply player's action
        action = self._create_action(action_type, amount, round_state)
        next_state = round_state.proceed(action)
        print(f"[DEBUG] After player action - Pips: {next_state.pips if hasattr(next_state, 'pips') else 'Terminal'}")
        
        # Handle player fold
        if isinstance(action, FoldAction):
            # When player folds, only add matched bets to the pot
            matched_amount = min(initial_state['pips'])
            self.total_pot += matched_amount * 2
            current_pot = self.total_pot
            # Return excess chips to bot (the difference between their pip and the matched amount)
            bot_return = initial_state['pips'][1] - matched_amount if initial_state['pips'][1] > matched_amount else 0
            player_return = 0  # Player folded, they don't get anything back
        elif isinstance(action, CallAction):
            # Only add to pot if we're not just completing blinds
            if initial_state['pips'] != [1, 2] and initial_state['pips'] != [2, 1]:
                # Calculate how much more player needs to put in
                player_current = min(initial_state['pips'][0], initial_state['pips'][1])  # What player has in already
                to_match = max(initial_state['pips'][0], initial_state['pips'][1])        # What they need to match
                call_amount = to_match - player_current    # How much more they need to add
                
                if call_amount > 0:
                    self.total_pot += call_amount  # Just add the new chips
                    current_pot = self.total_pot
                    print(f"[DEBUG] Player called {call_amount}, adding to pot")
        else:
            # Track pips for current street
            current_street_pips = sum(initial_state['pips'])
            current_round_pips = sum(next_state.pips) if not isinstance(next_state, TerminalState) else 0
            
            # Handle pot calculation after player action
            if isinstance(next_state, TerminalState):
                self.total_pot += current_street_pips
                current_pot = self.total_pot
            else:
                if hasattr(next_state, 'street') and next_state.street > initial_state['street']:
                    self.total_pot += current_street_pips
                    current_pot = self.total_pot
                else:
                    current_pot = self.total_pot + current_round_pips
            
            bot_return = 0
            player_return = 0
                
        # Handle bot response
        try:
            if not isinstance(next_state, TerminalState):
                dummy_game_state = None
                bot_action = self.rebel_bot.get_action(dummy_game_state, next_state, 1)
                print(f"[DEBUG] Bot action: {self._action_to_string(bot_action)}")
                
                previous_state = next_state
                next_state = next_state.proceed(bot_action)
                bot_action_msg = f"Bot {self._action_to_string(bot_action)}"
                
                # Handle bot fold
                if isinstance(bot_action, FoldAction):
                    # When bot folds, winner gets only the matched bet plus existing pot
                    current_pips = previous_state.pips
                    player_return = current_pips[0]  # Return the full bet to player since bot folded
                    bot_return = 0  # Bot folded, they don't get anything back
                    # Do not modify total_pot since the bot folded and chips go back to player
                elif isinstance(bot_action, CallAction):
                    # Get the amount bot has to call from the previous state
                    previous_pips = previous_state.pips
                    call_amount = max(previous_pips)  # Amount bot needs to match
                    self.total_pot += call_amount * 2 # Add both bets to pot
                    current_pot = self.total_pot
                    print(f"[DEBUG] Bot called {call_amount}, adding {call_amount} to pot")
                elif isinstance(next_state, TerminalState):
                    final_street_pips = sum(previous_state.pips)
                    self.total_pot += final_street_pips
                    current_pot = self.total_pot
                else:
                    if hasattr(next_state, 'street') and next_state.street > previous_state.street:
                        street_end_pips = sum(previous_state.pips)
                        self.total_pot += street_end_pips
                    
                    current_pot = self.total_pot + sum(next_state.pips)
            else:
                bot_action_msg = "Hand complete!"
                
        except Exception as e:
            print(f"[DEBUG] Bot action error: {str(e)}")
            bot_action_msg = "Bot checks"
            if not isinstance(next_state, TerminalState):
                next_state = next_state.proceed(CheckAction())
        
        # Update stacks and pot based on final state
        if isinstance(next_state, TerminalState):
            if hasattr(next_state, 'deltas'):
                print(f"[DEBUG] Terminal state - Final pot: {self.total_pot}, Deltas: {next_state.deltas}")
                
                # Handle player fold
                if isinstance(action, FoldAction):
                    # If player folds, bot gets the pot
                    win_amount = self.session.pot
                    final_player_stack = initial_state['player_stack']  # Player gets nothing back
                    final_bot_stack = initial_state['bot_stack'] + win_amount  # Bot gets the pot
                    winner = "Bot"
                # Handle bot fold - bot_action will be defined in this case since we went through the bot response block
                elif 'bot_action' in locals() and isinstance(bot_action, FoldAction):
                    # If bot folds, player gets the pot and their unmatched raise back
                    win_amount = self.session.pot
                    final_player_stack = initial_state['player_stack'] + win_amount
                    final_bot_stack = initial_state['bot_stack']  # Bot gets nothing back
                    winner = "Player"
                # Handle normal win/loss (no fold)
                else:
                    if next_state.deltas[0] > 0:  # Player wins
                        win_amount = self.total_pot
                        final_player_stack = initial_state['player_stack'] + win_amount
                        final_bot_stack = initial_state['bot_stack']  # Bot gets nothing on loss
                        winner = "Player"
                    elif next_state.deltas[0] < 0:  # Bot wins
                        win_amount = self.total_pot
                        final_player_stack = initial_state['player_stack']  # Player gets nothing on loss
                        final_bot_stack = initial_state['bot_stack'] + win_amount
                        winner = "Bot"
                    else:  # Split pot
                        win_amount = self.total_pot // 2
                        final_player_stack = initial_state['player_stack'] + win_amount
                        final_bot_stack = initial_state['bot_stack'] + win_amount
                        winner = "Split"
                
                print(f"[DEBUG] {winner} wins {win_amount} - Final stacks - Player: {final_player_stack}, Bot: {final_bot_stack}")
                self.session.player_stack = final_player_stack
                self.session.bot_stack = final_bot_stack
                self.session.pot = self.total_pot  # Keep final pot for display
        else:
            # Update stacks and pot for ongoing hand
            self.session.player_stack = next_state.stacks[0]
            self.session.bot_stack = next_state.stacks[1]
            self.session.pot = current_pot
        
        self._update_session_from_round_state(next_state)
        
        # Prepare response data
        response_data = {
            'pot': self.session.pot,
            'player_stack': self.session.player_stack,
            'bot_stack': self.session.bot_stack,
            'player_cards': self.convert_cards_to_display(self.session.player_cards),
            'board_cards': self.convert_cards_to_display(self.session.board_cards),
            'legal_actions': self._get_legal_actions(next_state) if not isinstance(next_state, TerminalState) else [],
            'hand_complete': isinstance(next_state, TerminalState),
            'game_message': self._get_game_message(next_state, bot_action_msg)
        }
        
        # Reset pot tracking only after response is prepared
        if isinstance(next_state, TerminalState):
            self.session.pot = 0
            self.total_pot = 0
            self.session.save()
            print("[DEBUG] Pot reset for next hand")
        
        return response_data

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
                return f"You win ${self.total_pot}! Click 'Next Hand' to continue."
            elif round_state.deltas[0] < 0:
                return f"Bot wins ${self.total_pot}. Click 'Next Hand' to continue."
            else:
                split_amount = self.total_pot // 2
                return f"Split pot! Each player wins ${split_amount}. Click 'Next Hand' to continue."
        elif bot_action_msg:
            return f"{bot_action_msg}. Your turn!"
        return "Your turn! Choose your action."
    
    def _update_session_from_round_state(self, round_state):
        """Update session with current round state"""
        print(f"[DEBUG] Updating session from round state")
        print(f"[DEBUG] Round state type: {type(round_state)}")
        
        if isinstance(round_state, TerminalState):
            print("[DEBUG] Terminal state in update_session")
            if round_state.previous_state and round_state.previous_state.street > 0:
                street = round_state.previous_state.street
                visible_cards = round_state.previous_state.deck[:street]
                self.session.board_cards = [str(card) for card in visible_cards]
                # Don't modify pot in terminal state
        else:
            if round_state.street > 0:
                visible_cards = round_state.deck[:round_state.street]
                self.session.board_cards = [str(card) for card in visible_cards]
            
            # Update street name
            street_names = {0: 'preflop', 3: 'flop', 4: 'turn', 5: 'river'}
            self.session.current_street = street_names.get(round_state.street, self.session.current_street)
            
            # Only update pot if not terminal state
            if hasattr(round_state, 'pips'):
                current_pot = self.total_pot + sum(round_state.pips)
                print(f"[DEBUG] Current pot calculation in update_session: {self.total_pot} (total) + {sum(round_state.pips)} (current pips) = {current_pot}")
                if self.session.pot != current_pot:
                    self.session.pot = current_pot
        
        self.session.game_state = self._serialize_game_state(round_state)
        self.session.save()
        print(f"[DEBUG] Final session state - Pot: {self.session.pot}")
            
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
        """Serialize the game state for storage"""
        if isinstance(round_state, TerminalState):
            return {
                'terminal': True,
                'deltas': round_state.deltas if hasattr(round_state, 'deltas') else None,
                'button': round_state.previous_state.button if round_state.previous_state else 0,
                'total_pot': self.total_pot  # Save total_pot in the game state
            }
        return {
            'terminal': False,
            'button': round_state.button,
            'street': round_state.street,
            'final_street': round_state.final_street,
            'pips': round_state.pips,
            'stacks': round_state.stacks,
            'hands': [[str(c) for c in h] for h in round_state.hands],
            'deck': [str(c) for c in round_state.deck],
            'total_pot': self.total_pot  # Save total_pot in the game state
        }

    def _deserialize_game_state(self, state_dict):
        """Deserialize the stored game state"""
        if state_dict.get('terminal', False):
            return None

        # Restore total_pot from game state
        self.total_pot = state_dict.get('total_pot', 0)

        return RoundState(
            button=state_dict['button'],
            street=state_dict['street'],
            final_street=state_dict['final_street'],
            pips=state_dict['pips'],
            stacks=state_dict['stacks'],
            hands=state_dict['hands'],
            deck=state_dict['deck'],
            previous_state=None
        )
