export interface ThemeConfig {
  primaryColor: string;
  backgroundColor: string;
  secondaryBackgroundColor: string;
  textColor: string;
  accentColor: string;
  font: string;
}

export interface ThemeData {
  theme: ThemeConfig;
}

let themeCache: ThemeConfig | null = null;

/**
 * Load theme configuration from config.json file
 * In development, this reads from a static file
 * In production, this should be loaded from an API endpoint
 */
export async function loadThemeConfig(): Promise<ThemeConfig> {
  // Check cache first
  if (themeCache) {
    return themeCache;
  }

  try {
    // In development, fetch from the public directory
    // In production, this should be an API call to the backend
    const response = await fetch('/config.json');
    if (!response.ok) {
      throw new Error('Failed to load configuration');
    }

    const configData = await response.json();
    const themeData = configData.theme;
    themeCache = themeData;
    return themeCache as ThemeConfig;
  } catch (error) {
    console.warn('Failed to load theme from config file, using defaults:', error);

    // Default theme configuration as fallback
    const defaultTheme: ThemeConfig = {
      primaryColor: "#00C2FF",
      backgroundColor: "#F5F7FA",
      secondaryBackgroundColor: "#FFFFFF",
      textColor: "#1A202C",
      accentColor: "#FF6B6B",
      font: "Poppins"
    };

    themeCache = defaultTheme;
    return defaultTheme;
  }
}

/**
 * Load theme synchronously for SSR/initial render
 * Returns default theme to avoid hydration mismatches
 */
export function loadThemeConfigSync(): ThemeConfig {
  if (themeCache) {
    return themeCache;
  }

  // Default theme for initial render
  const defaultTheme: ThemeConfig = {
    primaryColor: "#00C2FF",
    backgroundColor: "#F5F7FA",
    secondaryBackgroundColor: "#FFFFFF",
    textColor: "#1A202C",
    accentColor: "#FF6B6B",
    font: "Poppins"
  };

  return defaultTheme;
}

/**
 * Get CSS variables for the theme (synchronous version)
 */
export function getThemeCSSVariables(): Record<string, string> {
  const theme = loadThemeConfigSync();
  return {
    '--primary-color': theme.primaryColor,
    '--background-color': theme.backgroundColor,
    '--secondary-background-color': theme.secondaryBackgroundColor,
    '--text-color': theme.textColor,
    '--accent-color': theme.accentColor,
    '--font-family': theme.font
  };
}

/**
 * Apply theme to CSS custom properties (async version)
 */
export async function applyTheme(): Promise<void> {
  if (typeof document !== 'undefined') {
    const theme = await loadThemeConfig();
    const root = document.documentElement;

    root.style.setProperty('--primary-color', theme.primaryColor);
    root.style.setProperty('--background-color', theme.backgroundColor);
    root.style.setProperty('--secondary-background-color', theme.secondaryBackgroundColor);
    root.style.setProperty('--text-color', theme.textColor);
    root.style.setProperty('--accent-color', theme.accentColor);
    root.style.setProperty('--font-family', theme.font);
  }
}

/**
 * Apply theme synchronously using cached/default theme
 */
export function applyThemeSync(): void {
  if (typeof document !== 'undefined') {
    const theme = loadThemeConfigSync();
    const root = document.documentElement;

    root.style.setProperty('--primary-color', theme.primaryColor);
    root.style.setProperty('--background-color', theme.backgroundColor);
    root.style.setProperty('--secondary-background-color', theme.secondaryBackgroundColor);
    root.style.setProperty('--text-color', theme.textColor);
    root.style.setProperty('--accent-color', theme.accentColor);
    root.style.setProperty('--font-family', theme.font);
  }
}