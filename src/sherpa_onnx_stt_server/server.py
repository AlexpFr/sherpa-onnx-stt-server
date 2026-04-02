"""HTTP server accepting POST requests with multipart file upload for audio transcription."""

import json
import os
import re
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .config import logger


def _json_default(o):
    """Serialize non-JSON objects (tuples, sherpa-onnx results) to native types."""
    if isinstance(o, (tuple, list)):
        return list(o)
    attrs = [a for a in dir(o) if not a.startswith("_")]
    return {a: getattr(o, a) for a in attrs}


def _parse_multipart(content_type, body):
    """Parse a multipart/form-data body and return (filename, file_bytes).

    Parses sequentially by searching for CRLF-delimited boundary markers
    instead of naively splitting on the boundary bytes (which can appear
    in binary file data).
    """
    match = re.search(r'boundary=(?:"([^"]+)"|(\S+))', content_type)
    if not match:
        raise ValueError("No boundary found in Content-Type header")

    boundary = (match.group(1) or match.group(2)).encode()
    crlf_boundary = b"\r\n--" + boundary
    end_marker = b"--" + boundary + b"--"

    # Find first boundary (preamble can exist before it)
    first = body.find(b"--" + boundary)
    if first == -1:
        raise ValueError("No boundary found in request body")

    # Skip past the first boundary line
    pos = body.find(b"\r\n", first)
    if pos == -1:
        raise ValueError("Malformed multipart body")
    pos += 2  # skip \r\n

    # Find next boundary marker
    next_boundary = body.find(crlf_boundary, pos)
    if next_boundary == -1:
        # Check for end marker
        end_pos = body.find(end_marker, pos)
        if end_pos == -1:
            raise ValueError("No closing boundary found")
        part = body[pos:end_pos]
    else:
        part = body[pos:next_boundary]

    # Split headers from file data
    header_end = part.find(b"\r\n\r\n")
    if header_end == -1:
        raise ValueError("No header/data separator found")

    header_section = part[:header_end].decode("utf-8", errors="replace")
    file_data = part[header_end + 4:]

    # Strip trailing \r\n if present
    if file_data.endswith(b"\r\n"):
        file_data = file_data[:-2]

    filename_match = re.search(r'filename="([^"]*)"', header_section)
    if not filename_match:
        filename_match = re.search(r"filename=([^\s;]+)", header_section)

    filename = filename_match.group(1) if filename_match else "upload"

    return filename, file_data


def _save_upload(file_bytes, original_filename):
    """Write uploaded bytes to a temp file preserving the original extension."""
    _, ext = os.path.splitext(original_filename)
    fd, path = tempfile.mkstemp(suffix=ext)
    try:
        os.write(fd, file_bytes)
    finally:
        os.close(fd)
    return path


class Handler(BaseHTTPRequestHandler):
    """Handle POST requests with audio file upload and delegate transcription."""

    transcriber = None

    def do_POST(self):
        tmp_path = None
        try:
            content_type = self.headers.get("Content-Type", "")

            if "multipart/form-data" not in content_type:
                raise ValueError(
                    "Expected multipart/form-data. "
                    'Upload with: curl -F "file=@audio.wav" http://host:port'
                )

            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0:
                raise ValueError("Empty request body")

            body = self.rfile.read(length)
            filename, file_bytes = _parse_multipart(content_type, body)

            if not file_bytes:
                raise ValueError("Uploaded file is empty")

            logger.info("Received file: %s (%d bytes)", filename, len(file_bytes))

            tmp_path = _save_upload(file_bytes, filename)
            result = self.transcriber.transcribe(tmp_path)

            data = json.dumps(result, ensure_ascii=False, default=_json_default).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        except ValueError as e:
            logger.error("Error 400: %s", e)
            self._send_error(400, str(e))
        except FileNotFoundError as e:
            logger.error("Error 404: %s", e)
            self._send_error(404, str(e))
        except Exception as e:
            logger.exception("Error 500: %s", e)
            self._send_error(500, str(e))
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

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
