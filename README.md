# sherpa-onnx-stt-server

A persistent HTTP server that receives audio files and returns their text transcription via [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx).

## How It Works

The server listens over HTTP and accepts POST requests containing an audio file path in JSON format:

```bash
curl -s -X POST http://127.0.0.1:8765 \
  -H "Content-Type: application/json" \
  -d '{"file":"/path/to/audio.wav"}'
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

### Manual Install

```bash
git clone https://github.com/AlexpFr/sherpa-onnx-stt-server.git
cd sherpa-onnx-stt-server

mkdir -p $HOME/.sherpa-onnx
cp src/sherpa-onnx-stt-server.py src/sherpa_onnx_stt_server/ wrapperSherpa.sh $HOME/.sherpa-onnx/

cd $HOME/.sherpa-onnx
python -m venv .venv
source .venv/bin/activate

pip install sherpa-onnx soundfile numpy
```

### Model

The server supports three types of sherpa-onnx models:

| Type | Required Arguments |
|------|-------------------|
| Transducer (NeMo) | `--tokens` `--encoder` `--decoder` `--joiner` |
| Paraformer | `--tokens` `--paraformer` |
| Whisper | `--tokens` `--whisper-encoder` `--whisper-decoder` |

All types support `--model-dir` for automatic file detection.

### Download Model (487 MB)

```bash
mkdir -p $HOME/.sherpa-onnx/model
cd $HOME/.sherpa-onnx/model
wget https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2
tar xvf sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2 --strip-components=1
rm sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2
```

## Usage

### Starting the Server

With `--model-dir` (automatic file detection):

```bash
$HOME/.sherpa-onnx/.venv/bin/python $HOME/.sherpa-onnx/sherpa-onnx-stt-server.py --model-dir=$HOME/.sherpa-onnx/model
```

Or with explicit paths:

```bash
MODEL_DIR="$HOME/.sherpa-onnx/model"

$HOME/.sherpa-onnx/.venv/bin/python $HOME/.sherpa-onnx/sherpa-onnx-stt-server.py \
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

```bash
$HOME/.sherpa-onnx/wrapperSherpa.sh /path/to/audio.wav
```

### Systemd Service

Create file `/etc/systemd/system/sherpa-onnx-stt-server.service`:

```ini
[Unit]
Description=sherpa-onnx-stt-server - Audio transcription server
After=network.target

[Service]
Type=simple
WorkingDirectory=%h/.sherpa-onnx
ExecStart=%h/.sherpa-onnx/.venv/bin/python sherpa-onnx-stt-server.py --model-dir=%h/.sherpa-onnx/model
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

## Project Structure

```
~/.sherpa-onnx/                        Installation folder
├── sherpa-onnx-stt-server.py          Entry point
├── sherpa_onnx_stt_server/
│   ├── __init__.py                    Orchestration (parse -> validate -> load -> serve)
│   ├── config.py                      CLI, logging, argument validation
│   ├── transcriber.py                 Transcriber: model, audio reading, conversion, inference
│   └── server.py                      HTTP server (POST only)
├── wrapperSherpa.sh                   Bash wrapper for quick transcription
├── .venv/                             Python virtual environment
└── model/                             Model files
```
