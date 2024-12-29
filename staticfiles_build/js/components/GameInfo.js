// GameInfo.js
class GameInfo {
    constructor() {
        this.elements = {
            pot: document.getElementById('pot'),
            playerStack: document.getElementById('player-stack'),
            botStack: document.getElementById('bot-stack'),
            message: document.getElementById('game-message')
        };
    }

    updateValues(state) {
        this.elements.pot.textContent = `$${state.pot}`;
        this.elements.playerStack.textContent = `$${state.player_stack}`;
        this.elements.botStack.textContent = `$${state.bot_stack}`;
    }

    showMessage(message, display = true) {
        this.elements.message.style.display = display ? 'block' : 'none';
        if (message) {
            this.elements.message.textContent = message;
        }
    }

    showError(message) {
        this.showMessage(`Error: ${message}`);
    }
}

export default GameInfo;