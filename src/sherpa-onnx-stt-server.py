#!/usr/bin/env python3
"""Persistent STT HTTP server using sherpa-onnx.

Supported audio formats: WAV, FLAC, OGG, MP3, M4A, AAC, WMA, OPUS, AMR, 3GP.
Non-native formats are converted to 16kHz mono WAV via ffmpeg.
"""
from sherpa_onnx_stt_server import run

if __name__ == "__main__":
    run()
