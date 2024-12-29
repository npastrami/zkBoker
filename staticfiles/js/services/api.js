// api.js
import { helpers } from '../utils/helpers.js';

class API {
    static async makeRequest(endpoint, data = {}) {
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': helpers.getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    static async startHand(sessionId, continueSession = false) {
        return this.makeRequest('/start_hand/', {
            session_id: sessionId,
            continue_session: continueSession
        });
    }

    static async makeMove(sessionId, action, amount = 0) {
        return this.makeRequest('/make_move/', {
            session_id: sessionId,
            action,
            amount: parseInt(amount)
        });
    }

    static async exitGame(sessionId) {
        return this.makeRequest('/exit_game/', {
            session_id: sessionId
        });
    }

    static async buyIn(sessionId) {
        return this.makeRequest('/buy_in/', {
            session_id: sessionId
        });
    }
}

export default API;