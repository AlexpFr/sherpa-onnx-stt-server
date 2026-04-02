"""HTTP server accepting POST requests for audio transcription."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .config import logger


def _json_default(o):
    """Serialize non-JSON objects (tuples, sherpa-onnx results) to native types."""
    if isinstance(o, (tuple, list)):
        return list(o)
    attrs = [a for a in dir(o) if not a.startswith("_")]
    return {a: getattr(o, a) for a in attrs}


class Handler(BaseHTTPRequestHandler):
    """Handle POST requests and delegate transcription to the Transcriber."""

    transcriber = None

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0:
                raise ValueError("Empty request body")

            body = self.rfile.read(length)
            payload = json.loads(body.decode("utf-8"))
            logger.info("Request received: %s", payload)

            audio_file = payload.get("file")
            if not audio_file:
                raise ValueError("Missing JSON field 'file'")

            result = self.transcriber.transcribe(audio_file)

            data = json.dumps(result, ensure_ascii=False, default=_json_default).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        except json.JSONDecodeError:
            logger.exception("Invalid JSON")
            self._send_error(400, "Invalid JSON")
        except ValueError as e:
            logger.error("Error 400: %s", e)
            self._send_error(400, str(e))
        except FileNotFoundError as e:
            logger.error("Error 404: %s", e)
            self._send_error(404, str(e))
        except Exception as e:
            logger.exception("Error 500: %s", e)
            self._send_error(500, str(e))

    def _send_error(self, status, message):
        """Send a JSON error response."""
        data = json.dumps({"error": message}, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        return


def create_server(host, port, transcriber):
    """Create the HTTP server with the provided Transcriber."""
    Handler.transcriber = transcriber
    return ThreadingHTTPServer((host, port), Handler)
