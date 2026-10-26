import os
import re
import subprocess
from pathlib import Path
from typing import Optional, Callable

class AudioEngine:
    """
    Motor de conversão e processamento de áudio com fidelidade profissional.
    """

    @classmethod
    def convert_audio(
        cls,
        input_path: str,
        output_path: str,
        target_format: str,
        bitrate: str = "320k",
        sample_rate: Optional[int] = None,
        channels: Optional[int] = None,
        normalize: bool = False,
        quality: str = "high",
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> str:
        input_file = Path(input_path).resolve()
        output_file = Path(output_path).resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)
        target_fmt = target_format.lower().lstrip('.')

        total_duration = cls._get_duration(str(input_file))

        cmd = ['ffmpeg', '-y', '-i', str(input_file), '-vn']

        # Audio filters
        af_filters = []
        if normalize:
            # EBU R128 broadcast standard audio normalization
            af_filters.append('loudnorm=I=-16:TP=-1.5:LRA=11')

        if af_filters:
            cmd.extend(['-af', ','.join(af_filters)])

        if sample_rate:
            cmd.extend(['-ar', str(sample_rate)])

        if channels:
            cmd.extend(['-ac', str(channels)])

        # Target codec & bitrate mapping
        if target_fmt == 'mp3':
            cmd.extend([
                '-c:a', 'libmp3lame',
                '-b:a', bitrate or '320k',
                '-id3v2_version', '3'
            ])

        elif target_fmt == 'wav':
            # PCM 24-bit for ultra/high, 16-bit for standard
            pcm_codec = 'pcm_s24le' if quality in ['ultra', 'high'] else 'pcm_s16le'
            cmd.extend(['-c:a', pcm_codec])

        elif target_fmt == 'flac':
            cmd.extend(['-c:a', 'flac', '-compression_level', '8'])

        elif target_fmt in ['m4a', 'aac']:
            cmd.extend(['-c:a', 'aac', '-b:a', bitrate or '320k'])

        elif target_fmt == 'ogg':
            cmd.extend(['-c:a', 'libvorbis', '-qscale:a', '9'])

        elif target_fmt == 'opus':
            cmd.extend(['-c:a', 'libopus', '-b:a', '256k', '-vbr', 'on'])

        elif target_fmt == 'aiff':
            cmd.extend(['-c:a', 'pcm_s24be'])

        elif target_fmt == 'alac':
            cmd.extend(['-c:a', 'alac'])

        elif target_fmt == 'wma':
            cmd.extend(['-c:a', 'wmav2', '-b:a', '192k'])

        else:
            cmd.extend(['-c:a', 'aac', '-b:a', bitrate or '320k'])

        cmd.extend(['-progress', 'pipe:1', str(output_file)])

        cls._run_with_progress(cmd, total_duration, progress_callback)
        return str(output_file)

    @classmethod
    def _get_duration(cls, filepath: str) -> float:
        try:
            cmd = [
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                filepath
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return float(res.stdout.strip())
        except Exception:
            return 0.0

    @classmethod
    def _run_with_progress(
        cls,
        cmd: list,
        total_duration: float,
        progress_callback: Optional[Callable[[float, str], None]]
    ):
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        time_pattern = re.compile(r'out_time_ms=(\d+)')
        output_buffer = []

        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            line = line.strip()
            if not line:
                continue

            output_buffer.append(line)
            if len(output_buffer) > 50:
                output_buffer.pop(0)

            if line.startswith('out_time_ms='):
                m = time_pattern.search(line)
                if m and total_duration > 0:
                    current_ms = int(m.group(1))
                    current_sec = current_ms / 1_000_000.0
                    pct = min(99.0, (current_sec / total_duration) * 100.0)
                    if progress_callback:
                        progress_callback(pct, f"Processando áudio... ({pct:.1f}%)")

        return_code = process.wait()
        if return_code != 0:
            error_msg = "\n".join(output_buffer)
            raise RuntimeError(f"Erro na conversão de áudio FFmpeg (código {return_code}):\n{error_msg}")

        if progress_callback:
            progress_callback(100.0, "Áudio convertido com sucesso!")
