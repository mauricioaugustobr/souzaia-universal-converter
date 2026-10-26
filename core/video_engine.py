import os
import re
import subprocess
from pathlib import Path
from typing import Optional, Callable, Dict, Any

class VideoEngine:
    """
    Motor de conversão de vídeo e extração de áudio com alta qualidade via FFmpeg.
    """

    @staticmethod
    def _parse_time(time_str: str) -> float:
        try:
            parts = time_str.strip().split(':')
            if len(parts) == 3:
                h, m, s = parts
                return float(h) * 3600 + float(m) * 60 + float(s)
        except Exception:
            pass
        return 0.0

    @classmethod
    def convert_video(
        cls,
        input_path: str,
        output_path: str,
        target_format: str,
        quality: str = "high",
        resolution: Optional[str] = None,
        fps: Optional[int] = None,
        vcodec: Optional[str] = None,
        acodec: Optional[str] = None,
        audio_bitrate: str = "320k",
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> str:
        input_file = Path(input_path).resolve()
        output_file = Path(output_path).resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)
        target_fmt = target_format.lower().lstrip('.')

        # Retrieve duration first for progress calculation
        total_duration = cls._get_duration(str(input_file))

        # Check if converting to GIF
        if target_fmt == 'gif':
            return cls._convert_to_gif(
                str(input_file),
                str(output_file),
                fps=fps or 15,
                resolution=resolution,
                progress_callback=progress_callback
            )

        # Base ffmpeg command
        cmd = ['ffmpeg', '-y', '-i', str(input_file)]

        # Video filters (scaling, fps)
        vf_filters = []
        if resolution and resolution != 'original':
            # e.g., '1920x1080', '1280x720', '3840x2160', '854x480'
            if 'x' in resolution:
                w, h = resolution.split('x')
                vf_filters.append(f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1")
            elif resolution in ['1080p', '1080']:
                vf_filters.append("scale=-2:1080:flags=lanczos")
            elif resolution in ['720p', '720']:
                vf_filters.append("scale=-2:720:flags=lanczos")
            elif resolution in ['4k', '2160p']:
                vf_filters.append("scale=-2:2160:flags=lanczos")
            elif resolution in ['480p', '480']:
                vf_filters.append("scale=-2:480:flags=lanczos")

        if fps:
            vf_filters.append(f"fps={fps}")

        if vf_filters:
            cmd.extend(['-vf', ','.join(vf_filters)])

        # Quality presets
        # 'ultra', 'high', 'balanced', 'web'
        crf_map = {
            'ultra': '16',
            'high': '18',
            'balanced': '22',
            'web': '26'
        }
        crf = crf_map.get(quality, '18')

        # Codec configuration based on target container
        if target_fmt == 'mp4':
            codec = vcodec or 'libx264'
            cmd.extend(['-c:v', codec])
            if codec in ['libx264', 'libx265']:
                cmd.extend(['-crf', crf, '-preset', 'slow' if quality in ['ultra', 'high'] else 'medium'])
                cmd.extend(['-pix_fmt', 'yuv420p'])
            cmd.extend(['-c:a', acodec or 'aac', '-b:a', audio_bitrate, '-movflags', '+faststart'])

        elif target_fmt == 'webm':
            cmd.extend(['-c:v', vcodec or 'libvpx-vp9', '-crf', crf, '-b:v', '0'])
            cmd.extend(['-c:a', acodec or 'libopus', '-b:a', '192k'])

        elif target_fmt == 'mkv':
            codec = vcodec or 'libx264'
            cmd.extend(['-c:v', codec, '-crf', crf, '-preset', 'medium'])
            cmd.extend(['-c:a', acodec or 'aac', '-b:a', audio_bitrate])

        elif target_fmt == 'mov':
            if quality == 'ultra':
                # Apple ProRes 422 HQ
                cmd.extend(['-c:v', 'prores_ks', '-profile:v', '3', '-c:a', 'pcm_s24le'])
            else:
                cmd.extend(['-c:v', vcodec or 'libx264', '-crf', crf, '-c:a', acodec or 'aac', '-b:a', audio_bitrate])

        elif target_fmt == 'avi':
            cmd.extend(['-c:v', 'libxvid', '-qscale:v', '2', '-c:a', 'libmp3lame', '-b:a', audio_bitrate])

        elif target_fmt == 'flv':
            cmd.extend(['-c:v', 'libx264', '-crf', crf, '-c:a', 'aac', '-b:a', '192k'])

        elif target_fmt == 'wmv':
            cmd.extend(['-c:v', 'wmv2', '-b:v', '5000k', '-c:a', 'wmav2', '-b:a', '192k'])

        else:
            # Generic fallback
            cmd.extend(['-c:v', 'libx264', '-crf', crf, '-c:a', 'aac', '-b:a', audio_bitrate])

        cmd.extend(['-progress', 'pipe:1', str(output_file)])

        cls._run_with_progress(cmd, total_duration, progress_callback)
        return str(output_file)

    @classmethod
    def _convert_to_gif(
        cls,
        input_path: str,
        output_path: str,
        fps: int = 15,
        resolution: Optional[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> str:
        """
        Converte vídeo para GIF animado de altíssima qualidade usando palettegen em 2 passos.
        """
        total_duration = cls._get_duration(input_path)
        scale_filter = "scale=w=480:h=-1:flags=lanczos"
        if resolution and 'x' in resolution:
            w, h = resolution.split('x')
            scale_filter = f"scale={w}:{h}:flags=lanczos"
        elif resolution in ['720p', '720']:
            scale_filter = "scale=w=720:h=-1:flags=lanczos"
        elif resolution in ['1080p', '1080']:
            scale_filter = "scale=w=1080:h=-1:flags=lanczos"

        filter_complex = (
            f"[0:v] fps={fps},{scale_filter},split [a][b]; "
            f"[a] palettegen=max_colors=256:reserve_transparent=1:stats_mode=single [p]; "
            f"[b][p] paletteuse=dither=bayer:bayer_scale=3"
        )

        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-filter_complex', filter_complex,
            '-progress', 'pipe:1',
            output_path
        ]

        cls._run_with_progress(cmd, total_duration, progress_callback)
        return output_path

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
        speed_pattern = re.compile(r'speed=\s*([\d\.]+)x')

        current_speed = "1.0x"
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

            if line.startswith('speed='):
                m = speed_pattern.search(line)
                if m:
                    current_speed = f"{m.group(1)}x"

            if line.startswith('out_time_ms='):
                m = time_pattern.search(line)
                if m and total_duration > 0:
                    current_ms = int(m.group(1))
                    current_sec = current_ms / 1_000_000.0
                    pct = min(99.0, (current_sec / total_duration) * 100.0)
                    if progress_callback:
                        progress_callback(pct, f"Convertendo vídeo... ({pct:.1f}% a {current_speed})")

        return_code = process.wait()
        if return_code != 0:
            error_msg = "\n".join(output_buffer)
            raise RuntimeError(f"Erro na conversão FFmpeg (código {return_code}):\n{error_msg}")

        if progress_callback:
            progress_callback(100.0, "Conversão concluída!")
