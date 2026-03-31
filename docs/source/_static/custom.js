/**
 * LogEverything Documentation Theme Switcher
 * Provides dark/light theme toggle functionality with localStorage persistence
 */

(function() {
    'use strict';

    // Theme configuration
    const THEMES = {
        LIGHT: 'light',
        DARK: 'dark'
    };

    const STORAGE_KEY = 'logeverything-docs-theme';
    const THEME_ATTRIBUTE = 'data-theme';

    // Theme detection and management
    class ThemeManager {
        constructor() {
            this.currentTheme = this.getStoredTheme() || this.getSystemTheme();
            this.init();
        }

        init() {
            this.applyTheme(this.currentTheme);
            this.createThemeToggle();
            this.bindEvents();
        }

        getStoredTheme() {
            try {
                return localStorage.getItem(STORAGE_KEY);
            } catch (e) {
                console.warn('localStorage not available:', e);
                return null;
            }
        }

        getSystemTheme() {
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                return THEMES.DARK;
            }
            return THEMES.LIGHT;
        }

        setStoredTheme(theme) {
            try {
                localStorage.setItem(STORAGE_KEY, theme);
            } catch (e) {
                console.warn('Could not save theme preference:', e);
            }
        }

        applyTheme(theme) {
            document.documentElement.setAttribute(THEME_ATTRIBUTE, theme);
            this.currentTheme = theme;
            this.setStoredTheme(theme);
            this.updateToggleButton();
        }

        toggleTheme() {
            const newTheme = this.currentTheme === THEMES.LIGHT ? THEMES.DARK : THEMES.LIGHT;

            // Add switching animation class
            document.body.classList.add('theme-switching');

            // Apply new theme
            this.applyTheme(newTheme);

            // Add a subtle animation when switching themes
            document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';

            // Remove animation classes after transition
            setTimeout(() => {
                document.body.style.transition = '';
                document.body.classList.remove('theme-switching');
            }, 300);

            // Announce theme change to screen readers
            this.announceThemeChange(newTheme);
        }

        announceThemeChange(theme) {
            // Create a temporary announcement for screen readers
            const announcement = document.createElement('div');
            announcement.setAttribute('aria-live', 'polite');
            announcement.setAttribute('aria-atomic', 'true');
            announcement.style.position = 'absolute';
            announcement.style.left = '-10000px';
            announcement.style.width = '1px';
            announcement.style.height = '1px';
            announcement.style.overflow = 'hidden';
            announcement.textContent = `Theme switched to ${theme} mode`;

            document.body.appendChild(announcement);

            // Remove announcement after screen readers have time to read it
            setTimeout(() => {
                if (announcement.parentNode) {
                    announcement.parentNode.removeChild(announcement);
                }
            }, 1000);
        }

        createThemeToggle() {
            // Remove existing toggle if present
            const existingToggle = document.querySelector('.theme-toggle');
            if (existingToggle) {
                existingToggle.remove();
            }

            // Create toggle button
            const toggle = document.createElement('button');
            toggle.className = 'theme-toggle';
            toggle.setAttribute('aria-label', 'Toggle dark/light theme');
            toggle.setAttribute('title', 'Switch theme');

            // Add button to page
            document.body.appendChild(toggle);

            this.toggleButton = toggle;
            this.updateToggleButton();
        }

        updateToggleButton() {
            if (!this.toggleButton) return;

            const isDark = this.currentTheme === THEMES.DARK;
            const icon = isDark ? '☀️' : '🌙';
            const text = isDark ? 'Light' : 'Dark';
            const hasStoredPreference = !!this.getStoredTheme();

            this.toggleButton.innerHTML = `
                <span class="icon">${icon}</span>
                <span class="text">${text}</span>
            `;

            // Update accessibility attributes
            this.toggleButton.setAttribute('aria-label',
                `Switch to ${isDark ? 'light' : 'dark'} theme`);
            this.toggleButton.setAttribute('aria-pressed', isDark.toString());

            // Add preference indicator
            this.toggleButton.classList.toggle('has-preference', hasStoredPreference);

            // Update title with more context
            this.toggleButton.setAttribute('title',
                `Switch to ${isDark ? 'light' : 'dark'} theme${hasStoredPreference ? ' (preference saved)' : ''}`);
        }

        bindEvents() {
            // Toggle button click
            if (this.toggleButton) {
                this.toggleButton.addEventListener('click', () => {
                    this.toggleTheme();
                });
            }

            // System theme change detection
            if (window.matchMedia) {
                const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
                mediaQuery.addEventListener('change', (e) => {
                    // Only auto-switch if user hasn't manually set a preference
                    if (!this.getStoredTheme()) {
                        this.applyTheme(e.matches ? THEMES.DARK : THEMES.LIGHT);
                    }
                });
            }

            // Keyboard shortcut (Ctrl/Cmd + Shift + T)
            document.addEventListener('keydown', (e) => {
                if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
                    e.preventDefault();
                    this.toggleTheme();
                }
            });
        }
    }

    // Initialize theme manager when DOM is ready
    function initTheme() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                new ThemeManager();
            });
        } else {
            new ThemeManager();
        }
    }

    // Start initialization
    initTheme();

    // Expose theme manager for debugging
    window.LogEverythingTheme = ThemeManager;

})();

/**
 * Additional enhancements for the documentation
 */
(function() {
    'use strict';

    // Smooth scrolling for anchor links
    function initSmoothScrolling() {
        document.addEventListener('click', function(e) {
            const target = e.target.closest('a[href^="#"]');
            if (!target) return;

            const href = target.getAttribute('href');
            if (href === '#') return;

            const targetElement = document.querySelector(href);
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    }

    // Enhanced code block functionality
    function initCodeBlocks() {
        const codeBlocks = document.querySelectorAll('.highlight pre, .executable-code pre');

        codeBlocks.forEach(block => {
            // Add copy button to code blocks
            const copyButton = document.createElement('button');
            copyButton.className = 'copy-code-btn';
            copyButton.innerHTML = '📋';
            copyButton.title = 'Copy code';
            copyButton.setAttribute('aria-label', 'Copy code to clipboard');

            copyButton.addEventListener('click', async () => {
                const code = block.textContent;
                try {
                    await navigator.clipboard.writeText(code);
                    copyButton.innerHTML = '✅';
                    copyButton.title = 'Copied!';
                    setTimeout(() => {
                        copyButton.innerHTML = '📋';
                        copyButton.title = 'Copy code';
                    }, 2000);
                } catch (err) {
                    console.warn('Could not copy code:', err);
                    copyButton.innerHTML = '❌';
                    setTimeout(() => {
                        copyButton.innerHTML = '📋';
                    }, 2000);
                }
            });

            // Position the copy button
            const container = block.closest('.highlight, .executable-code');
            if (container) {
                container.style.position = 'relative';
                container.appendChild(copyButton);
            }
        });
    }

    // Initialize enhancements
    function initEnhancements() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                initSmoothScrolling();
                initCodeBlocks();
            });
        } else {
            initSmoothScrolling();
            initCodeBlocks();
        }
    }

    initEnhancements();

})();
