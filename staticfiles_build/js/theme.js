// static/js/theme.js
document.addEventListener('DOMContentLoaded', () => {
    // Set initial theme (defaulting to dark)
    if (!localStorage.getItem('theme')) {
        localStorage.setItem('theme', 'dark');
    }
    
    document.documentElement.setAttribute('data-theme', localStorage.getItem('theme'));

    // Add theme toggle button to all pages
    const button = document.createElement('button');
    button.className = 'theme-toggle';
    button.innerHTML = localStorage.getItem('theme') === 'dark' ? '🌞' : '🌙';
    document.body.appendChild(button);

    // Toggle theme
    button.addEventListener('click', () => {
        const currentTheme = localStorage.getItem('theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        localStorage.setItem('theme', newTheme);
        document.documentElement.setAttribute('data-theme', newTheme);
        button.innerHTML = newTheme === 'dark' ? '🌞' : '🌙';
    });
});