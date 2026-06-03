# Ollama Setup & Optimization History (April 2026)

This document records the optimization steps taken for Mohammed's Medical AI Drone project.

## 1. System Fixes for GPU (NVIDIA GTX 1660 Ti)
- Added user `ollama` to `video` and `render` groups to allow access to GPU hardware.
- Command: `sudo usermod -aG video,render ollama`

## 2. Remote & Docker Access Fix
- Modified `/etc/systemd/system/ollama.service` to bind to `0.0.0.0` instead of `localhost` so Open WebUI (Docker) can connect.
- Added: `Environment="OLLAMA_HOST=0.0.0.0"`
- Commands: `sudo systemctl daemon-reload && sudo systemctl restart ollama`

## 3. Storage Optimization (The Big Cleanup)
- **Root Partition Cleanup:**
    - Purged old Linux kernel (6.8.0-101-generic) modules and tools (~1 GB).
    - Removed unused `flatpak` (Mission Center) and `snap` (Chromium) apps (~5 GB).
    - Vacuumed system journals to 50MB.
- **Ollama Specific Cleanup:**
    - Deleted unused/redundant GPU libraries (CUDA 12 and MLX) from `/usr/local/lib/ollama/` that weren't needed for the GTX 1660 Ti.
    - Result: Recovered ~4.8 GB of system space.

## 4. Model Path
- All models are stored in `/home/mohammed/ollama_models` (External Home Partition with 13GB free).

## 5. Model Migration: E4B → E2B (April 3, 2026)
- **Deleted:** `gemma4:e4b` (9.6 GB) and `gemma4-fast` (9.6 GB) — freed ~9 GB
- **Installed:** `gemma4:e2b` (7.2 GB) — smaller model, faster inference
- **Performance Comparison:**
    - E4B: 13.7 tokens/s (eval), 73%/27% CPU/GPU split
    - E2B: 36 tokens/s (eval), 73%/27% CPU/GPU split — **2.6x faster**
- **Note:** E2B (5.1B total params) is Q4_K_M quantized at 7.2 GB. It still exceeds the 6 GB VRAM so partial CPU offload remains, but inference is significantly faster due to fewer active parameters.

## 6. Antigravity IDE Integration (April 3, 2026)
- Installed **Continue.dev** extension (v1.2.22) in Antigravity IDE.
- Configured to use `gemma4:e2b` via Ollama at `http://127.0.0.1:11434`.
- Features: Chat assistant + Tab autocomplete with local Gemma 4.
- Config file: `~/.continue/config.json`

## 7. Deployment Commands (For Reference)
- Run WebUI: `docker start open-webui` (Port 3000)
- Control Ollama: `sudo systemctl status/restart ollama`
- Test model: `ollama run gemma4:e2b "your prompt"`
