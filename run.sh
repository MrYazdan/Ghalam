#!/usr/bin/env bash
set -e

# Resolve true project directory even when called through symlink
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
    DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
cd "$SCRIPT_DIR"

# 1. If uv is available in PATH, use it directly with project directory
if command -v uv &>/dev/null; then
    exec uv run --project "$SCRIPT_DIR" "$SCRIPT_DIR/main.py" "$@"
fi

# 2. Check user bin paths for uv
if [ -x "$HOME/.local/bin/uv" ]; then
    exec "$HOME/.local/bin/uv" run --project "$SCRIPT_DIR" "$SCRIPT_DIR/main.py" "$@"
elif [ -x "$HOME/.cargo/bin/uv" ]; then
    exec "$HOME/.cargo/bin/uv" run --project "$SCRIPT_DIR" "$SCRIPT_DIR/main.py" "$@"
fi

# 3. If uv is not present, auto-install standalone uv (fastest & cleanest)
echo "[Ghalam] 'uv' not found on system. Installing standalone uv..."
if command -v curl &>/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    exec uv run --project "$SCRIPT_DIR" "$SCRIPT_DIR/main.py" "$@"
else
    # Standard fallback if curl is missing
    VENV_DIR="$SCRIPT_DIR/.venv"
    if [ ! -d "$VENV_DIR" ]; then
        echo "[Ghalam] Setting up local .venv..."
        python3 -m venv "$VENV_DIR"
        "$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" -q
    fi
    exec "$VENV_DIR/bin/python" "$SCRIPT_DIR/main.py" "$@"
fi
