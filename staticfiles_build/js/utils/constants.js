export const CONSTANTS = {
    BUTTON_STATES: {
        NEXT_HAND: 'Next Hand',
        START_HAND: 'Start New Hand'
    },
    
    MESSAGES: {
        BUY_IN_REQUIRED: 'Buy-in required to play',
        HAND_COMPLETE: 'Hand complete! Click "Next Hand" to continue or "Exit" to leave the game.',
        DEFAULT_TURN: 'Your turn! Choose your action.'
    },
    
    ENDPOINTS: {
        START_HAND: '/start_hand/',
        MAKE_MOVE: '/make_move/',
        EXIT_GAME: '/exit_game/',
        BUY_IN: '/buy_in/'
    },

    GAME_CONFIG: {
        INITIAL_BUYIN: 200,
        MIN_BET: 1,
        MAX_BET: 200
    }
};

export default CONSTANTS;