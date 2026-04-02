#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/AlexpFr/sherpa-onnx-stt-server.git"
INSTALL_DIR="$HOME/.sherpa-onnx-stt-server"
MODEL_URL="https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2"
MODEL_NAME="sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8"
MODEL_ARCHIVE="sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2"

echo "==> Installing sherpa-onnx-stt-server to $INSTALL_DIR"

# Check prerequisites
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
  echo "Error: Python 3.13+ is required but not found." >&2
  exit 1
fi

if ! command -v ffmpeg &>/dev/null; then
  echo "Warning: ffmpeg not found. Non-WAV audio formats will not be supported." >&2
fi

if ! command -v git &>/dev/null; then
  echo "Error: git is required but not found." >&2
  exit 1
fi

# Clone repository directly into install directory
echo "==> Cloning repository..."
git clone "$REPO_URL" "$INSTALL_DIR"

# Create virtual environment
echo "==> Creating Python virtual environment..."
cd "$INSTALL_DIR"
python3 -m venv .venv 2>/dev/null || python -m venv .venv

# Install dependencies
echo "==> Installing Python dependencies..."
"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/.venv/bin/pip" install sherpa-onnx soundfile numpy

# Download model
echo ""
echo "==> Downloading model (~487 MB)..."
MODEL_DIR="$INSTALL_DIR/model"
mkdir -p "$MODEL_DIR"
cd "$MODEL_DIR"

if command -v aria2c &>/dev/null; then
  echo "    Using aria2c (16 parallel connections)..."
  aria2c -x 16 -s 16 "$MODEL_URL"
elif command -v wget &>/dev/null; then
  echo "    Using wget..."
  wget "$MODEL_URL"
elif command -v curl &>/dev/null; then
  echo "    Using curl..."
  curl -L -O "$MODEL_URL"
else
  echo "Error: aria2c, wget, or curl is required to download the model." >&2
  exit 1
fi

echo "    Extracting model..."
tar xvf "$MODEL_ARCHIVE"
rm "$MODEL_ARCHIVE"
echo "    Model downloaded to $MODEL_DIR/$MODEL_NAME"

# Create systemd user service
echo ""
echo "==> Setting up systemd user service..."
SYSTEMD_DIR="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_DIR"

cat > "$SYSTEMD_DIR/sherpa-onnx-stt-server.service" << EOF
[Unit]
Description=sherpa-onnx-stt-server - Audio transcription server
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/.venv/bin/python $INSTALL_DIR/src/sherpa-onnx-stt-server.py --model-dir=$INSTALL_DIR/model/$MODEL_NAME
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

echo "    Reloading systemd daemon..."
systemctl --user daemon-reload
echo "    Enabling and starting service..."
systemctl --user enable --now sherpa-onnx-stt-server.service
echo "    Service started successfully."

# Create symlink for wrapper
echo ""
echo "==> Creating symlink for sherpa-onnx-offline..."
LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN"

# Remove existing symlink if present
rm -f "$LOCAL_BIN/sherpa-onnx-offline"

ln -s "$INSTALL_DIR/wrapperSherpa.sh" "$LOCAL_BIN/sherpa-onnx-offline"
chmod +x "$INSTALL_DIR/wrapperSherpa.sh"
chmod +x "$LOCAL_BIN/sherpa-onnx-offline"
echo "    Symlink created: $LOCAL_BIN/sherpa-onnx-offline -> $INSTALL_DIR/wrapperSherpa.sh"

echo ""
echo "==> Installation complete!"
echo ""
echo "Usage:"
echo "  Transcribe an audio file:"
echo "    sherpa-onnx-offline /path/to/audio.wav"
echo ""
echo "  Start/stop/restart the server:"
echo "    systemctl --user start sherpa-onnx-stt-server"
echo "    systemctl --user stop sherpa-onnx-stt-server"
echo "    systemctl --user restart sherpa-onnx-stt-server"
echo ""
echo "  Check service status:"
echo "    systemctl --user status sherpa-onnx-stt-server"
echo ""
echo "  View logs:"
echo "    journalctl --user -u sherpa-onnx-stt-server -f"
echo ""
