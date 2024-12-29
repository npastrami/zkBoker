// Modal.js
import API from '../services/api.js';
import { helpers } from '../utils/helpers.js';

class Modal {
    constructor(modalId) {
        this.modal = document.getElementById(modalId);
    }

    show() {
        if (this.modal) {
            this.modal.style.display = 'block';
        }
    }

    hide() {
        if (this.modal) {
            this.modal.style.display = 'none';
        }
    }

    async handleBuyIn(sessionId, onSuccess) {
        try {
            const data = await API.buyIn(sessionId);
            
            if (data.success) {
                // Update the coins display in the top bar
                const coinDisplay = document.querySelector('.coin');
                if (coinDisplay) {
                    coinDisplay.textContent = `🪙 ${data.updated_balance}`;
                }
                
                if (typeof onSuccess === 'function') {
                    onSuccess(data);
                }
                
                return data;
            } else {
                throw new Error(data.message || 'Buy-in failed');
            }
        } catch (error) {
            console.error('Buy-in error:', error);
            throw error;
        }
    }
}

export default Modal;