#!/usr/bin/env bash
# ============================================================================
# Travel-Price Project — Claude Code Environment Setup
# ============================================================================
# This script configures PATH and environment variables so that every Bash
# command run by Claude Code inside this project has access to all required
# tools: Docker, Node.js (via NVM), Python (via project venv), and git.
#
# It is sourced automatically by the SessionStart hook (see settings.json)
# and writes exports into $CLAUDE_ENV_FILE when that variable is set.
# ============================================================================

# --- Homebrew (macOS, Intel — /usr/local) ---------------------------------
# Docker, git, and other Homebrew-installed CLIs live under /usr/local/bin.
# We source Homebrew's shellenv to get its paths (bin, sbin, man, info).
if [ -x /usr/local/bin/brew ]; then
  eval "$(/usr/local/bin/brew shellenv 2>/dev/null)"
fi

# --- Docker Desktop -------------------------------------------------------
# Docker Desktop for Mac installs the `docker` binary at /usr/local/bin/docker
# and CLI plugins (compose, buildx, etc.) under /usr/local/lib/docker/cli-plugins.
# The docker-credential-desktop helper also requires /usr/local/bin in PATH.
if [ -x /usr/local/bin/docker ]; then
  export PATH="/usr/local/bin:${PATH}"
fi

# --- NVM + Node.js --------------------------------------------------------
# This project's frontend requires Node.js (v22+ per Dockerfile, v25.6.0 installed).
# NVM is installed at ~/.nvm; we source it and use the default version.
export NVM_DIR="$HOME/.nvm"
if [ -s "$NVM_DIR/nvm.sh" ]; then
  source "$NVM_DIR/nvm.sh" --no-use 2>/dev/null
  # Use the NVM default version (v25.6.0) — adds node/npm/npx to PATH
  nvm use default --silent 2>/dev/null
fi

# --- Python virtual environment -------------------------------------------
# The backend requires Python 3.11+ with project dependencies (FastAPI,
# Playwright, pytest, etc.) installed in a local venv.
_VENV_DIR="/Users/mario/Travel-Price/backend/.venv"
if [ -f "${_VENV_DIR}/bin/activate" ]; then
  export VIRTUAL_ENV="${_VENV_DIR}"
  export PATH="${_VENV_DIR}/bin:${PATH}"
fi
unset _VENV_DIR

# --- System essentials -----------------------------------------------------
# Ensure /usr/bin is in PATH for git, curl, ssh, and other system tools.
case ":${PATH}:" in
  *":/usr/bin:"*) ;;
  *) export PATH="${PATH}:/usr/bin" ;;
esac

# --- Write to CLAUDE_ENV_FILE if set ---------------------------------------
# When Claude Code sets $CLAUDE_ENV_FILE, writing exports there makes them
# persist for the entire session (all subsequent Bash tool calls).
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo "export PATH=\"${PATH}\"" >> "$CLAUDE_ENV_FILE"
  [ -n "${VIRTUAL_ENV:-}" ] && echo "export VIRTUAL_ENV=\"${VIRTUAL_ENV}\"" >> "$CLAUDE_ENV_FILE"
  [ -n "${NVM_DIR:-}" ] && echo "export NVM_DIR=\"${NVM_DIR}\"" >> "$CLAUDE_ENV_FILE"
fi
