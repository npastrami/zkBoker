// helpers.js
export const helpers = {
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },

    formatMoney(amount) {
        return `$${amount.toLocaleString()}`;
    },

    validateRaiseAmount(amount, minBet, maxBet) {
        const parsedAmount = parseInt(amount);
        return !isNaN(parsedAmount) && 
               parsedAmount >= minBet && 
               parsedAmount <= maxBet;
    }
};

export default helpers;