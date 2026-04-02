#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/AlexpFr/sherpa-onnx-stt-server.git"
INSTALL_DIR="$HOME/.sherpa-onnx"

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

# Clone repository
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

echo "==> Cloning repository..."
git clone --depth 1 "$REPO_URL" "$TMP_DIR/sherpa-onnx-stt-server"

# Copy files to install directory
echo "==> Setting up installation directory..."
mkdir -p "$INSTALL_DIR"
cp "$TMP_DIR/sherpa-onnx-stt-server/src/sherpa-onnx-stt-server.py" "$INSTALL_DIR/"
cp -r "$TMP_DIR/sherpa-onnx-stt-server/src/sherpa_onnx_stt_server" "$INSTALL_DIR/"
cp "$TMP_DIR/sherpa-onnx-stt-server/wrapperSherpa.sh" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/wrapperSherpa.sh"

# Create virtual environment
echo "==> Creating Python virtual environment..."
cd "$INSTALL_DIR"
python3 -m venv .venv 2>/dev/null || python -m venv .venv

# Install dependencies
echo "==> Installing Python dependencies..."
"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/.venv/bin/pip" install sherpa-onnx soundfile numpy

echo ""
echo "==> Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Download a model:"
echo "     mkdir -p $INSTALL_DIR/model && cd $INSTALL_DIR/model"
echo "     wget https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2"
echo "     tar xvf sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2 --strip-components=1"
echo "     rm sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2"
echo ""
echo "  2. Start the server:"
echo "     $INSTALL_DIR/.venv/bin/python $INSTALL_DIR/sherpa-onnx-stt-server.py --model-dir=$INSTALL_DIR/model"
echo ""
echo "  3. Test it:"
echo "     curl -s -X POST http://127.0.0.1:8765 -H 'Content-Type: application/json' -d '{\"file\":\"/path/to/audio.wav\"}'"
echo ""
