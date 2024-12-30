class GameTable {
    constructor() {
        this.createGameModal = document.getElementById('createGameModal');
        this.joinGameModal = document.getElementById('joinGameModal');
        this.createGameForm = document.getElementById('createGameForm');
        this.joinGameForm = document.getElementById('joinGameForm');
        this.gameIdInput = document.getElementById('selectedGameId');
        this.playModeSelect = document.getElementById('playMode');
        this.botSelectionGroup = document.getElementById('botSelectionGroup');
        
        // Get CSRF token
        this.csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        this.bindEvents();
        this.initializeSorting();
    }

    bindEvents() {
        // Join game buttons
        document.querySelectorAll('.join-game-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const gameId = e.target.dataset.gameId;
                this.showJoinGameModal(gameId);
            });
        });

        // Play mode selection
        if (this.playModeSelect) {
            this.playModeSelect.addEventListener('change', () => {
                this.toggleBotSelection();
            });
        }

        // Form submission
        if (this.joinGameForm) {
            this.joinGameForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleJoinGame();
            });
        }

        // Cancel buttons
        document.querySelectorAll('.cancel-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                this.hideModal(modal);
            });
        });

        // Game type filter
        const gameTypeFilter = document.getElementById('gameTypeFilter');
        if (gameTypeFilter) {
            gameTypeFilter.addEventListener('change', (e) => {
                this.filterGames(e.target.value);
            });
        }
    }

    showJoinGameModal(gameId) {
        if (this.joinGameModal && this.gameIdInput) {
            this.gameIdInput.value = gameId;
            this.joinGameModal.style.display = 'block';
            this.toggleBotSelection();
        }
    }

    hideModal(modal) {
        if (modal) {
            modal.style.display = 'none';
            const form = modal.querySelector('form');
            if (form) form.reset();
        }
    }

    toggleBotSelection() {
        if (this.botSelectionGroup && this.playModeSelect) {
            this.botSelectionGroup.style.display = 
                this.playModeSelect.value === 'bot' ? 'block' : 'none';
        }
    }

    async handleJoinGame() {
        const formData = {
            game_id: this.gameIdInput.value,
            play_mode: this.playModeSelect.value,
            num_hands: document.getElementById('numHands').value,
            initial_stack: document.getElementById('initialStack').value,
            max_rebuys: document.getElementById('maxRebuys').value
        };

        // Add bot ID if in bot mode
        if (formData.play_mode === 'bot') {
            formData.player_bot_id = document.getElementById('playerBotSelect').value;
        }

        // Validate required fields
        if (!formData.game_id || !formData.num_hands || !formData.initial_stack) {
            alert('Please fill in all required fields');
            return;
        }

        try {
            console.log('Sending join game request:', formData);
            const response = await fetch('/game/join/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                credentials: 'same-origin',
                body: JSON.stringify(formData)
            });

            console.log('Response received:', response);
            const data = await response.json();
            console.log('Response data:', data);

            if (data.success) {
                window.location.href = data.redirect_url;
            } else {
                alert(data.message || 'Failed to join game');
            }
        } catch (error) {
            console.error('Error joining game:', error);
            alert('Failed to join game. Please try again.');
        }
    }

    initializeSorting() {
        const sortBy = document.getElementById('sortBy');
        if (sortBy) {
            sortBy.addEventListener('change', (e) => {
                this.sortGames(e.target.value);
            });
        }
    }

    sortGames(sortBy) {
        const tbody = document.querySelector('.game-table tbody');
        if (!tbody) return;

        const rows = Array.from(tbody.querySelectorAll('tr'));

        rows.sort((a, b) => {
            let aVal, bVal;
            switch(sortBy) {
                case 'user':
                    aVal = a.cells[0]?.textContent ?? '';
                    bVal = b.cells[0]?.textContent ?? '';
                    return aVal.localeCompare(bVal);
                case 'hands':
                    aVal = parseInt(a.cells[3]?.textContent?.split('/')[0] ?? '0');
                    bVal = parseInt(b.cells[3]?.textContent?.split('/')[0] ?? '0');
                    return bVal - aVal;
                case 'game_type':
                    aVal = a.cells[2]?.textContent ?? '';
                    bVal = b.cells[2]?.textContent ?? '';
                    return aVal.localeCompare(bVal);
                case 'posted_on':
                    aVal = new Date(a.cells[4]?.textContent ?? 0);
                    bVal = new Date(b.cells[4]?.textContent ?? 0);
                    return bVal - aVal;
                default:
                    return 0;
            }
        });

        rows.forEach(row => tbody.appendChild(row));
    }

    filterGames(type) {
        const rows = document.querySelectorAll('.game-table tbody tr');
        rows.forEach(row => {
            const gameTypeCell = row.querySelector('td:nth-child(3)');
            const gameType = gameTypeCell?.textContent?.toLowerCase() ?? '';
            row.style.display = (type === 'all' || gameType === type) ? '' : 'none';
        });
    }
}

// Initialize when the document is ready
document.addEventListener('DOMContentLoaded', () => {
    new GameTable();
});