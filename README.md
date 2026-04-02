# sherpa-onnx-stt-server

A persistent HTTP server that receives audio files and returns their text transcription via [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx).

## How It Works

The server listens over HTTP and accepts POST requests with the audio file uploaded as `multipart/form-data`:

```bash
curl -s -X POST http://127.0.0.1:8765 \
  -F "file=@/path/to/audio.wav"
```

Response:

```json
{"text": "Transcribed text"}
```

**Supported formats**: WAV (native), MP3, FLAC, OGG, M4A, AAC, WMA, OPUS, AMR, 3GP, WebM, MP4, AIFF, ALAC. Non-WAV formats are automatically converted to 16kHz mono WAV via ffmpeg.

## Installation

### Prerequisites

- Python 3.13+
- ffmpeg (for non-WAV format conversion)

### Quick Install

```bash
curl -sSL https://raw.githubusercontent.com/AlexpFr/sherpa-onnx-stt-server/main/install.sh | bash
```

The installer will:
- Clone the repository to `~/.sherpa-onnx-stt-server`
- Create a Python virtual environment and install dependencies
- Download the model automatically (uses `aria2c` with 16 parallel connections if available, otherwise `wget`, then `curl`)
- Create and start a systemd user service
- Create a `sherpa-onnx-offline` symlink in `~/.local/bin` for easy access

### Manual Install

```bash
git clone https://github.com/AlexpFr/sherpa-onnx-stt-server.git
cd sherpa-onnx-stt-server

mkdir -p $HOME/.sherpa-onnx-stt-server
cp -r src wrapperSherpa.sh $HOME/.sherpa-onnx-stt-server/

cd $HOME/.sherpa-onnx-stt-server
python -m venv .venv
source .venv/bin/activate

pip install sherpa-onnx soundfile numpy

# Create symlink for wrapper
mkdir -p $HOME/.local/bin
ln -s $HOME/.sherpa-onnx-stt-server/wrapperSherpa.sh $HOME/.local/bin/sherpa-onnx-offline
chmod +x $HOME/.local/bin/sherpa-onnx-offline
```

### Model

The server supports three types of sherpa-onnx models:

| Type | Required Arguments |
|------|-------------------|
| Transducer (NeMo) | `--tokens` `--encoder` `--decoder` `--joiner` |
| Paraformer | `--tokens` `--paraformer` |
| Whisper | `--tokens` `--whisper-encoder` `--whisper-decoder` |

All types support `--model-dir` for automatic file detection.

The installer automatically downloads the model (~487 MB). If you need to download it manually:

```bash
mkdir -p $HOME/.sherpa-onnx-stt-server/model
cd $HOME/.sherpa-onnx-stt-server/model

# Using aria2c (fastest, 16 parallel connections)
aria2c -x 16 -s 16 https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2

# Or using wget
wget https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2

# Or using curl
curl -L -O https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2

tar -xjf sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2
rm sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2
```

For faster extraction, install `lbzip2`:

```bash
# Debian/Ubuntu
sudo apt install lbzip2

# Then use:
tar -xvI lbzip2 -f sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2
```

## Usage

### Quick Transcription (Bash Wrapper)

After installation, use the `sherpa-onnx-offline` command:

```bash
sherpa-onnx-offline /path/to/audio.wav
```

This invokes the wrapper which sends the audio to the running server and returns the transcription.

### Starting the Server

The systemd user service is automatically created and started during installation.

Manage the service:

```bash
# Start/stop/restart
systemctl --user start sherpa-onnx-stt-server
systemctl --user stop sherpa-onnx-stt-server
systemctl --user restart sherpa-onnx-stt-server

# Check status
systemctl --user status sherpa-onnx-stt-server

# View logs
journalctl --user -u sherpa-onnx-stt-server -f
```

Manual start (if not using systemd):

With `--model-dir` (automatic file detection):

```bash
$HOME/.sherpa-onnx-stt-server/.venv/bin/python $HOME/.sherpa-onnx-stt-server/src/sherpa-onnx-stt-server.py --model-dir=$HOME/.sherpa-onnx-stt-server/model/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8
```

Or with explicit paths:

```bash
MODEL_DIR="$HOME/.sherpa-onnx-stt-server/model/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8"

$HOME/.sherpa-onnx-stt-server/.venv/bin/python $HOME/.sherpa-onnx-stt-server/src/sherpa-onnx-stt-server.py \
  --tokens="$MODEL_DIR/tokens.txt" \
  --encoder="$MODEL_DIR/encoder.int8.onnx" \
  --decoder="$MODEL_DIR/decoder.int8.onnx" \
  --joiner="$MODEL_DIR/joiner.int8.onnx"
```

### Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--model-dir` | - | Model folder (automatic file detection) |
| `--host` | `127.0.0.1` | Listen address |
| `--port` | `8765` | Listen port |
| `--num-threads` | `4` | CPU threads |
| `--provider` | `cpu` | Provider (cpu/cuda) |
| `--language` | `fr` | Language (Whisper only) |
| `--task` | `transcribe` | Task (Whisper: transcribe/translate) |

### Bash Wrapper

The installer creates a symlink `~/.local/bin/sherpa-onnx-offline` pointing to `wrapperSherpa.sh`. Ensure `~/.local/bin` is in your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Then use:

```bash
sherpa-onnx-offline /path/to/audio.wav
```

Or manually with the wrapper script:

```bash
$HOME/.sherpa-onnx-stt-server/wrapperSherpa.sh /path/to/audio.wav
```

### Systemd Service

The installer automatically creates and starts the user service. The service file is located at `$HOME/.config/systemd/user/sherpa-onnx-stt-server.service`.

To manually recreate or modify the service:

Create file `$HOME/.config/systemd/user/sherpa-onnx-stt-server.service`:

```ini
[Unit]
Description=sherpa-onnx-stt-server - Audio transcription server
After=network.target

[Service]
Type=simple
WorkingDirectory=%h/.sherpa-onnx-stt-server
ExecStart=%h/.sherpa-onnx-stt-server/.venv/bin/python sherpa-onnx-stt-server.py --model-dir=%h/.sherpa-onnx-stt-server/model/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

Enable and start (user mode):

```bash
systemctl --user daemon-reload
systemctl --user enable --now sherpa-onnx-stt-server
```

> **Note**: The installer handles all of this automatically. The steps above are only needed if you want to manually configure the service.

## Project Structure

```
~/.sherpa-onnx-stt-server/                        Installation folder
├── src/
│   ├── sherpa-onnx-stt-server.py          Entry point
│   └── sherpa_onnx_stt_server/
│       ├── __init__.py                    Orchestration (parse -> validate -> load -> serve)
│       ├── config.py                      CLI, logging, argument validation
│       ├── transcriber.py                 Transcriber: model, audio reading, conversion, inference
│       └── server.py                      HTTP server (POST only)
├── wrapperSherpa.sh                   Bash wrapper for quick transcription
├── .venv/                             Python virtual environment
└── model/                             Model files

~/.local/bin/
└── sherpa-onnx-offline -> ~/.sherpa-onnx-stt-server/wrapperSherpa.sh

~/.config/systemd/user/
└── sherpa-onnx-stt-server.service     Systemd user service
```
