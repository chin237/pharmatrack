// Dark mode toggle - the actual switching happens by adding/removing the
// "dark" class on <html>; theme.css defines what each color variable
// becomes under html.dark. Preference is remembered in localStorage.

function applyTheme(isDark) {
    document.documentElement.classList.toggle('dark', isDark);
}

function toggleTheme() {
    const isDark = !document.documentElement.classList.contains('dark');
    applyTheme(isDark);
    localStorage.setItem('pharmatrack-theme', isDark ? 'dark' : 'light');
}

document.addEventListener('DOMContentLoaded', () => {
    // Sync the visible toggle switch (only present on the Settings page)
    // with whatever theme is actually active right now.
    const toggle = document.getElementById('dark-mode-toggle');
    if (toggle) {
        toggle.checked = document.documentElement.classList.contains('dark');
        toggle.addEventListener('change', toggleTheme);
    }
});