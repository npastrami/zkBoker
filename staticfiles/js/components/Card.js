// Card.js
class Card {
    constructor(value, suit, suitSymbol) {
        this.value = value;
        this.suit = suit;
        this.suitSymbol = suitSymbol;
    }

    createElement() {
        const cardElement = document.createElement('div');
        cardElement.className = 'card';
        
        const valueSpan = document.createElement('span');
        valueSpan.className = 'card-value';
        valueSpan.textContent = this.value;
        
        const suitSpan = document.createElement('span');
        suitSpan.className = `card-suit ${this.suit.toLowerCase()}`;
        suitSpan.textContent = this.suitSymbol;
        
        cardElement.appendChild(valueSpan);
        cardElement.appendChild(suitSpan);
        
        return cardElement;
    }

    static updateContainer(containerId, cards) {
        const container = document.getElementById(containerId);
        container.innerHTML = '';
        cards.forEach(card => {
            const cardInstance = new Card(card.value, card.suit, card.suit_symbol);
            container.appendChild(cardInstance.createElement());
        });
    }
}

export default Card;