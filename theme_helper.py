#!/usr/bin/env python3
"""
Theme Configuration Helper for TGYN Admin Portal

This script helps you easily update the theme configuration in config.json
with predefined color schemes or custom colors.
"""

import json
import os
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """Load the current configuration"""
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    else:
        print("❌ config.json not found!")
        return {}

def save_config(config: Dict[str, Any]) -> None:
    """Save the configuration"""
    with open("config.json", 'w') as f:
        json.dump(config, f, indent=2)
    print("✅ Configuration saved!")

def get_predefined_themes() -> Dict[str, Dict[str, str]]:
    """Return predefined theme options"""
    return {
        "default": {
            "primaryColor": "#00C2FF",
            "backgroundColor": "#F5F7FA",
            "secondaryBackgroundColor": "#FFFFFF",
            "textColor": "#1A202C",
            "accentColor": "#FF6B6B",
            "font": "Poppins"
        },
        "dark": {
            "primaryColor": "#00C2FF",
            "backgroundColor": "#1A202C",
            "secondaryBackgroundColor": "#2D3748",
            "textColor": "#F7FAFC",
            "accentColor": "#FF6B6B",
            "font": "Poppins"
        },
        "nature": {
            "primaryColor": "#38A169",
            "backgroundColor": "#F0FFF4",
            "secondaryBackgroundColor": "#FFFFFF",
            "textColor": "#22543D",
            "accentColor": "#DD6B20",
            "font": "Poppins"
        },
        "sunset": {
            "primaryColor": "#ED8936",
            "backgroundColor": "#FEFCBF",
            "secondaryBackgroundColor": "#FFFFFF",
            "textColor": "#744210",
            "accentColor": "#E53E3E",
            "font": "Poppins"
        },
        "ocean": {
            "primaryColor": "#3182CE",
            "backgroundColor": "#EBF8FF",
            "secondaryBackgroundColor": "#FFFFFF",
            "textColor": "#2A4365",
            "accentColor": "#805AD5",
            "font": "Poppins"
        }
    }

def display_current_theme(config: Dict[str, Any]) -> None:
    """Display the current theme settings"""
    theme = config.get("theme", {})
    print("\n🎨 Current Theme:")
    print("=" * 40)
    for key, value in theme.items():
        print(f"{key}: {value}")
    print()

def display_predefined_themes() -> None:
    """Display available predefined themes"""
    themes = get_predefined_themes()
    print("\n🎨 Available Predefined Themes:")
    print("=" * 40)
    for name, theme in themes.items():
        print(f"\n📌 {name.upper()}:")
        for key, value in theme.items():
            print(f"   {key}: {value}")

def apply_predefined_theme(config: Dict[str, Any], theme_name: str) -> Dict[str, Any]:
    """Apply a predefined theme"""
    themes = get_predefined_themes()
    if theme_name in themes:
        config["theme"] = themes[theme_name]
        print(f"✅ Applied '{theme_name}' theme!")
        return config
    else:
        print(f"❌ Theme '{theme_name}' not found!")
        return config

def customize_theme_interactive(config: Dict[str, Any]) -> Dict[str, Any]:
    """Interactive theme customization"""
    theme = config.get("theme", get_predefined_themes()["default"])

    print("\n🎨 Theme Customization")
    print("=" * 40)
    print("Enter new values (press Enter to keep current value):")

    fields = ["primaryColor", "backgroundColor", "secondaryBackgroundColor", "textColor", "accentColor", "font"]

    for field in fields:
        current = theme.get(field, "")
        new_value = input(f"{field} [{current}]: ").strip()
        if new_value:
            theme[field] = new_value

    config["theme"] = theme
    print("✅ Theme customized!")
    return config

def main():
    """Main function"""
    print("🎯 TGYN Admin Portal - Theme Configuration Helper")
    print("=" * 50)

    config = load_config()
    if not config:
        return

    while True:
        print("\nChoose an option:")
        print("1. View current theme")
        print("2. Apply predefined theme")
        print("3. Customize theme manually")
        print("4. Save and exit")
        print("5. Exit without saving")

        choice = input("\nEnter your choice (1-5): ").strip()

        if choice == "1":
            display_current_theme(config)
            display_predefined_themes()

        elif choice == "2":
            theme_name = input("Enter theme name: ").strip().lower()
            config = apply_predefined_theme(config, theme_name)

        elif choice == "3":
            config = customize_theme_interactive(config)

        elif choice == "4":
            save_config(config)
            print("🎉 Theme updated! Remember to:")
            print("   1. Restart the backend server")
            print("   2. Refresh the frontend application")
            break

        elif choice == "5":
            print("👋 Exiting without saving changes.")
            break

        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()