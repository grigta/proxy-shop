#!/usr/bin/env python3
"""Compile translation files (.po to .mo) for the bot."""
import subprocess
import sys
from pathlib import Path


def main():
    """Compile all .po files to .mo files."""
    bot_dir = Path(__file__).parent
    locales_dir = bot_dir / "locales"
    
    if not locales_dir.exists():
        print(f"Error: locales directory not found: {locales_dir}")
        sys.exit(1)
    
    print(f"Compiling translations in {locales_dir}...")
    
    try:
        # Compile all .po files to .mo
        result = subprocess.run(
            ["pybabel", "compile", "-d", str(locales_dir), "-D", "messages"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        print("✅ Translations compiled successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error compiling translations:")
        print(e.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: pybabel not found. Install it with: pip install Babel")
        sys.exit(1)


if __name__ == "__main__":
    main()
