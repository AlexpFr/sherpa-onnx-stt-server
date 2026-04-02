#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/AlexpFr/sherpa-onnx-stt-server.git"
INSTALL_DIR="$HOME/.sherpa-onnx-stt-server"

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

echo ""
echo "==> Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Download a model:"
echo "     mkdir -p $INSTALL_DIR/model && cd $INSTALL_DIR/model"
echo "     wget https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2"
echo "     tar xvf sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2"
echo "     rm sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2"
echo ""
echo "  2. Start the server:"
echo "     $INSTALL_DIR/.venv/bin/python $INSTALL_DIR/src/sherpa-onnx-stt-server.py --model-dir=$INSTALL_DIR/model/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8"
echo ""
echo "  3. Test it:"
echo "     curl -s -X POST http://127.0.0.1:8765 -F 'file=@/path/to/audio.wav'"
echo ""
echo "  4. Update later with:"
echo "     cd $INSTALL_DIR && git pull"
echo ""
