#!/bin/bash

# Configuration for your Gemma model
MODEL_NAME="gemma4:e2b"
OLLAMA_URL="http://localhost:11434"

echo "🤖 Starting Claude Code with your Gemma model..."
echo "📍 Connecting to: $OLLAMA_URL"

# Set official environment variables to bridge to Ollama
export ANTHROPIC_BASE_URL=$OLLAMA_URL
export ANTHROPIC_AUTH_TOKEN="ollama" 

# Launch Claude Code using the correct local path
/home/mohammed/.local/bin/claude --model $MODEL_NAME
