#!/bin/sh
# Tiny Wheels installer.
#   ./install.sh               install the "tinywheels" command
#   ./install.sh --uninstall   remove it again
set -e

DIR=$(cd "$(dirname "$0")" && pwd)
BIN="$HOME/.local/bin"
LINK="$BIN/tinywheels"

if [ "$1" = "--uninstall" ] || [ "$1" = "uninstall" ]; then
    if [ -L "$LINK" ]; then
        rm "$LINK"
        echo "Removed $LINK"
    else
        echo "Nothing to remove: $LINK is not installed."
    fi
    echo "Your records are kept in ~/.local/share/tinywheels/ (delete that folder to remove them too)."
    exit 0
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 is not installed. On Arch Linux run:  sudo pacman -S python"
    exit 1
fi
if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 8))'; then
    echo "Tiny Wheels needs Python 3.8 or newer (you have $(python3 --version))."
    exit 1
fi

chmod +x "$DIR/tinywheels.py"
mkdir -p "$BIN"
if [ -e "$LINK" ] && [ ! -L "$LINK" ]; then
    echo "$LINK already exists and is not a link, so I won't overwrite it."
    exit 1
fi
ln -sfn "$DIR/tinywheels.py" "$LINK"
echo "Installed: $LINK -> $DIR/tinywheels.py"

case ":$PATH:" in
    *":$BIN:"*)
        echo "Done! Type  tinywheels  to play." ;;
    *)
        echo
        echo "One more step: $BIN is not in your PATH yet."
        echo "Add this line to the end of ~/.bashrc (bash) or ~/.zshrc (zsh):"
        echo
        echo '    export PATH="$HOME/.local/bin:$PATH"'
        echo
        echo "(fish users run:  fish_add_path ~/.local/bin)"
        echo "Then open a new terminal and type  tinywheels" ;;
esac
