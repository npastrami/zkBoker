// gameEngine.js
import API from './api.js';
import Card from '../components/Card.js';
import GameInfo from '../components/GameInfo.js';
import Modal from '../components/Modal.js';
import { CONSTANTS } from '../utils/constants.js';

class GameEngine {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.gameInProgress = false;
        this.gameInfo = new GameInfo();
        this.buyInModal = new Modal('buyInModal');
        
        // Initialize after ensuring DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeButtons());
        } else {
            this.initializeButtons();
        }
    }

    initializeButtons() {
        // Initialize button references
        this.buttons = {
            fold: document.querySelector('.fold-button'),
            call: document.querySelector('.call-button'),
            raise: document.querySelector('.raise-button'),
            start: document.querySelector('.start-button'),
            exit: document.querySelector('.exit-button')
        };
        
        // Check if buttons exist before adding listeners
        if (this.buttons.fold) {
            this.buttons.fold.addEventListener('click', () => this.makeMove('fold'));
        }
        if (this.buttons.call) {
            this.buttons.call.addEventListener('click', () => this.makeMove('call'));
        }
        if (this.buttons.raise) {
            this.buttons.raise.addEventListener('click', () => this.makeMove('raise'));
        }
        if (this.buttons.start) {
            this.buttons.start.addEventListener('click', () => this.startNewHand());
        }
        if (this.buttons.exit) {
            this.buttons.exit.addEventListener('click', () => this.exitGame());
        }

        // Initialize raise input
        this.raiseInput = document.getElementById('raise-amount');
    }

    async startNewHand() {
        try {
            const data = await API.startHand(this.sessionId, this.gameInProgress);
            
            if (data.requires_buy_in) {
                this.buyInModal.show();
                return;
            }

            this.gameInProgress = true;
            if (data.pot !== undefined) {
                this.updateGameState(data);
                this.enableGameButtons(true);
                
                this.buttons.start.textContent = 'Next Hand';
                this.buttons.start.disabled = true;
                this.buttons.exit.disabled = false;
                
                this.gameInfo.showMessage(data.game_message || 'Your turn! Choose your action.');
            }
        } catch (error) {
            this.gameInfo.showError('Failed to start new hand');
        }
    }

    async makeMove(action) {
        try {
            const amount = action === 'raise' ? 
                parseInt(this.raiseInput.value) : 0;
            
            const data = await API.makeMove(this.sessionId, action, amount);
            this.updateGameState(data);
            
            if (data.hand_complete) {
                this.handleHandComplete();
            }
        } catch (error) {
            this.gameInfo.showError('Failed to make move');
        }
    }

    async exitGame() {
        if (this.gameInProgress) {
            if (!confirm(CONSTANTS.EXIT_CONFIRMATION_MESSAGE)) {
                return;
            }
        }
        
        try {
            const data = await API.exitGame(this.sessionId);
            if (data.success) {
                alert(`Game exited successfully! ${data.coins_returned} coins have been returned to your account.`);
                window.location.href = '/';
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            alert('Error exiting game. Please try again.');
        }
    }

    updateGameState(state) {
        this.gameInfo.updateValues(state);
        Card.updateContainer('board-cards', state.board_cards);
        Card.updateContainer('player-cards', state.player_cards);
        
        if (state.game_message) {
            this.gameInfo.showMessage(state.game_message);
        }
    }

    handleHandComplete() {
        this.gameInProgress = true;
        this.enableGameButtons(false);
        this.buttons.start.disabled = false;
        this.buttons.exit.disabled = false;
        
        this.gameInfo.showMessage(CONSTANTS.HAND_COMPLETE_MESSAGE);
    }

    enableGameButtons(enabled) {
        Object.values(this.buttons).forEach(button => {
            if (button !== this.buttons.start && button !== this.buttons.exit) {
                button.disabled = !enabled;
            }
        });
        this.raiseInput.disabled = !enabled;
    }
}

export default GameEngine;