import GameEngine from './services/gameEngine.js';
import Modal from './components/Modal.js';
import { CONSTANTS } from './utils/constants.js';
import API from './services/api.js';

class Game {
    constructor(config) {
        this.sessionId = config.sessionId;
        this.userCoins = config.userCoins;
        this.csrfToken = config.csrfToken;
        this.initialize();
    }

    initialize() {
        try {
            this.gameEngine = new GameEngine(this.sessionId);
            this.buyInModal = new Modal('buyInModal');
            this.bindEvents();
            console.log('Game initialized with config:', this);
        } catch (error) {
            console.error('Game initialization failed:', error);
        }
    }

    bindEvents() {
        document.querySelector('.modal-buttons').addEventListener('click', async (e) => {
            if (e.target.tagName === 'BUTTON') {
                if (e.target.textContent === 'Yes') {
                    await this.handleBuyInConfirmation();
                } else {
                    this.buyInModal.hide();
                }
            }
        });
    }

    async handleBuyInConfirmation() {
        try {
            await this.buyInModal.handleBuyIn(this.sessionId, async () => {
                this.buyInModal.hide();
                const startButton = document.querySelector('.start-button');
                if (startButton) {
                    startButton.textContent = CONSTANTS.BUTTON_STATES.NEXT_HAND;
                }
                await this.gameEngine.startNewHand();
            });
        } catch (error) {
            console.error('Buy-in failed:', error);
            alert(error.message || 'Failed to process buy-in');
        }
    }

    showMessage(message) {
        const messageElement = document.getElementById('game-message');
        if (messageElement) {
            messageElement.style.display = 'block';
            messageElement.textContent = message;
        }
    }
}

export default Game;