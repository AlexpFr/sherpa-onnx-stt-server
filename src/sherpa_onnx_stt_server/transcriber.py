"""Audio transcription via sherpa-onnx with automatic format conversion."""

import os
import subprocess
import tempfile
from pathlib import Path

import sherpa_onnx
import soundfile as sf

from .config import CONVERTIBLE_EXTENSIONS


class Transcriber:
    """Load a sherpa-onnx model and transcribe audio files.

    Supports WAV natively. Other formats (MP3, FLAC, OGG, etc.)
    are converted to 16kHz mono WAV via ffmpeg before transcription.
    """

    def __init__(self, args):
        """Initialize the recognizer from CLI arguments."""
        self.recognizer = self._create_recognizer(args)

    @staticmethod
    def _create_recognizer(args):
        """Build the recognizer based on model type (transducer, paraformer, whisper)."""
        if args.encoder and args.decoder and args.joiner:
            return sherpa_onnx.OfflineRecognizer.from_transducer(
                tokens=args.tokens,
                encoder=args.encoder,
                decoder=args.decoder,
                joiner=args.joiner,
                num_threads=args.num_threads,
                provider=args.provider,
                model_type="nemo_transducer",
            )

        if args.paraformer:
            return sherpa_onnx.OfflineRecognizer.from_paraformer(
                paraformer=args.paraformer,
                tokens=args.tokens,
                num_threads=args.num_threads,
                provider=args.provider,
            )

        if args.whisper_encoder and args.whisper_decoder:
            return sherpa_onnx.OfflineRecognizer.from_whisper(
                encoder=args.whisper_encoder,
                decoder=args.whisper_decoder,
                tokens=args.tokens,
                language=args.language,
                task=args.task,
                num_threads=args.num_threads,
                provider=args.provider,
            )

        raise ValueError("Unsupported model type")

    def transcribe(self, path):
        """Transcribe an audio file and return the result.

        Args:
            path: path to the audio file.

        Returns:
            sherpa-onnx result containing the transcribed text.
        """
        samples, sample_rate = self._read_audio(path)

        stream = self.recognizer.create_stream()
        stream.accept_waveform(sample_rate, samples)
        self.recognizer.decode_stream(stream)

        return stream.result

    def _read_audio(self, path):
        """Validate the file, read audio, and return (samples, sample_rate).

        Non-WAV files are converted via ffmpeg to 16kHz mono WAV.
        The temporary file is deleted after reading.
        """
        audio_path = Path(path)

        if not audio_path.is_file():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        ext = audio_path.suffix.lower()

        if ext == ".wav":
            samples, sample_rate = sf.read(path, dtype="float32")
            if samples.ndim == 2:
                samples = samples.mean(axis=1)
            return samples, sample_rate

        if ext not in CONVERTIBLE_EXTENSIONS:
            raise ValueError(
                f"Format '{ext}' not supported. "
                f"Accepted formats: .wav + conversion via ffmpeg ({', '.join(sorted(CONVERTIBLE_EXTENSIONS))})"
            )

        temp_wav = self._convert_to_wav(path)
        try:
            samples, sample_rate = sf.read(temp_wav, dtype="float32")
            if samples.ndim == 2:
                samples = samples.mean(axis=1)
            return samples, sample_rate
        finally:
            os.unlink(temp_wav)

    @staticmethod
    def _convert_to_wav(input_path):
        """Convert an audio file to 16kHz mono WAV via ffmpeg.

        Timeout of 60 seconds. The output file is created in a
        temporary directory.
        """
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name

        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-ac", "1", "-ar", "16000",
            "-loglevel", "error",
            wav_path,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg failed: {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            os.unlink(wav_path)
            raise RuntimeError("ffmpeg timeout (60s)")

        return wav_path
