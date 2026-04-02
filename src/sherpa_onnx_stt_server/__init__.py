"""STT server entry point: parse, validate, load model, start server."""

from .config import parse_args, validate_args
from .transcriber import Transcriber
from .server import create_server


def run():
    """Configure and start the audio transcription HTTP server."""
    args = parse_args()
    validate_args(args)

    transcriber = Transcriber(args)
    server = create_server(args.host, args.port, transcriber)

    print(f"Model loaded. Server ready at http://{args.host}:{args.port}")

    server.serve_forever()
