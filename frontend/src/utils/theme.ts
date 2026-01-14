// 1. Fallback Theme if config.json is missing or empty
const defaultTheme = {
  primaryColor: '#0070f3',
  backgroundColor: '#ffffff',
  secondaryBackgroundColor: '#f0f0f0',
  textColor: '#000000',
  accentColor: '#0070f3',
  font: 'Inter, sans-serif'
};

// 2. These are the functions that were "Not Defined"
async function loadThemeConfig() {
  try {
    const res = await fetch('/config.json');
    return await res.json();
  } catch (e) {
    return defaultTheme;
  }
}

function loadThemeConfigSync() {
  // In a browser, we usually can't do a true "sync" fetch easily, 
  // so we return the default if it's not already cached.
  return defaultTheme; 
}

// 3. Your theme application functions
export function getThemeCSSVariables(): Record<string, string> {
  const theme = loadThemeConfigSync() || defaultTheme;
  return {
    '--primary-color': theme.primaryColor || defaultTheme.primaryColor,
    '--background-color': theme.backgroundColor || defaultTheme.backgroundColor,
    '--secondary-background-color': theme.secondaryBackgroundColor || defaultTheme.secondaryBackgroundColor,
    '--text-color': theme.textColor || defaultTheme.textColor,
    '--accent-color': theme.accentColor || defaultTheme.accentColor,
    '--font-family': theme.font || defaultTheme.font
  };
}

export async function applyTheme(): Promise<void> {
  if (typeof document !== 'undefined') {
    const loadedTheme = await loadThemeConfig();
    const theme = loadedTheme || defaultTheme;
    const root = document.documentElement;

    root.style.setProperty('--primary-color', theme.primaryColor);
    root.style.setProperty('--background-color', theme.backgroundColor);
    root.style.setProperty('--secondary-background-color', theme.secondaryBackgroundColor);
    root.style.setProperty('--text-color', theme.textColor);
    root.style.setProperty('--accent-color', theme.accentColor);
    root.style.setProperty('--font-family', theme.font);
  }
}

export function applyThemeSync(): void {
  if (typeof document !== 'undefined') {
    const theme = loadThemeConfigSync() || defaultTheme;
    const root = document.documentElement;

    root.style.setProperty('--primary-color', theme.primaryColor);
    root.style.setProperty('--background-color', theme.backgroundColor);
    root.style.setProperty('--secondary-background-color', theme.secondaryBackgroundColor);
    root.style.setProperty('--text-color', theme.textColor);
    root.style.setProperty('--accent-color', theme.accentColor);
    root.style.setProperty('--font-family', theme.font);
  }
}
