"""CLI configuration, logging, and argument validation."""

import argparse
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("stt")

CONVERTIBLE_EXTENSIONS = {
    ".mp3", ".m4a", ".aac", ".wma", ".opus", ".amr",
    ".3gp", ".webm", ".mp4", ".aiff", ".alac", ".flac", ".ogg",
}

MODEL_FILE_KEYWORDS = {
    "tokens": "tokens",
    "encoder": "encoder",
    "decoder": "decoder",
    "joiner": "joiner",
    "paraformer": "paraformer",
    "whisper-encoder": "whisper_encoder",
    "whisper_encoder": "whisper_encoder",
    "whisper-decoder": "whisper_decoder",
    "whisper_decoder": "whisper_decoder",
}


def auto_detect_model_files(args):
    """If --model-dir is provided, automatically detect model files.

    Explicit arguments (--tokens, --encoder, etc.) take priority.
    """
    if not args.model_dir:
        return

    model_dir = Path(args.model_dir)
    if not model_dir.is_dir():
        raise FileNotFoundError(f"--model-dir not found: {model_dir}")

    detected = {}
    for f in model_dir.iterdir():
        if not f.is_file():
            continue
        name = f.name.lower()
        for keyword, attr in MODEL_FILE_KEYWORDS.items():
            if keyword in name and attr not in detected:
                detected[attr] = str(f)
                break

    for attr, path in detected.items():
        if not getattr(args, attr, None):
            setattr(args, attr, path)
            logger.info(f"Auto-detected --{attr.replace('_', '-')} = {path}")


def assert_file_exists(path_str, name):
    """Check that a file exists. Raises an error otherwise."""
    if not path_str:
        raise ValueError(f"Missing argument: {name}")
    path = Path(path_str)
    if not path.is_file():
        raise FileNotFoundError(f"{name} not found: {path}")
    return str(path)


def validate_args(args):
    """Verify that exactly one model type is configured and its files exist."""
    selected = 0

    has_transducer = bool(args.encoder and args.decoder and args.joiner)
    has_paraformer = bool(args.paraformer)
    has_whisper = bool(args.whisper_encoder and args.whisper_decoder)

    selected += int(has_transducer)
    selected += int(has_paraformer)
    selected += int(has_whisper)

    if selected != 1:
        raise ValueError(
            "You must provide exactly one model type: "
            "transducer (--encoder --decoder --joiner), "
            "paraformer (--paraformer), "
            "or whisper (--whisper-encoder --whisper-decoder). "
            "You can also use --model-dir for automatic detection."
        )

    assert_file_exists(args.tokens, "--tokens")

    if has_transducer:
        assert_file_exists(args.encoder, "--encoder")
        assert_file_exists(args.decoder, "--decoder")
        assert_file_exists(args.joiner, "--joiner")

    if has_paraformer:
        assert_file_exists(args.paraformer, "--paraformer")

    if has_whisper:
        assert_file_exists(args.whisper_encoder, "--whisper-encoder")
        assert_file_exists(args.whisper_decoder, "--whisper-decoder")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Persistent STT HTTP server using sherpa-onnx"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)

    parser.add_argument("--tokens")
    parser.add_argument("--model-dir", help="Model folder: auto-detects tokens, encoder, decoder, joiner, paraformer, whisper-encoder, whisper-decoder")

    parser.add_argument("--encoder")
    parser.add_argument("--decoder")
    parser.add_argument("--joiner")

    parser.add_argument("--paraformer")

    parser.add_argument("--whisper-encoder")
    parser.add_argument("--whisper-decoder")
    parser.add_argument(
        "--language",
        default="fr",
        help="Whisper language, e.g.: fr, en, de",
    )
    parser.add_argument(
        "--task",
        default="transcribe",
        choices=["transcribe", "translate"],
        help="Whisper task",
    )

    parser.add_argument("--num-threads", type=int, default=4)
    parser.add_argument("--provider", default="cpu")

    args = parser.parse_args()
    auto_detect_model_files(args)
    return args
