import os
import zipfile
import shutil
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List

from .media_info import get_file_category, inspect_media
from .video_engine import VideoEngine
from .audio_engine import AudioEngine
from .image_engine import ImageEngine
from .document_engine import DocumentEngine

class UniversalConverter:
    """
    Roteador e executor universal de conversão de arquivos de qualquer formato.
    """

    @classmethod
    def convert(
        cls,
        input_path: str,
        output_dir: str,
        target_format: str,
        options: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Executa a conversão e retorna informações sobre o(s) arquivo(s) gerado(s).
        """
        options = options or {}
        input_file = Path(input_path).resolve()
        out_directory = Path(output_dir).resolve()
        out_directory.mkdir(parents=True, exist_ok=True)

        if not input_file.exists():
            raise FileNotFoundError(f"Arquivo de origem não existe: {input_path}")

        src_ext = input_file.suffix.lower().lstrip('.')
        tgt_ext = target_format.lower().lstrip('.')
        stem = input_file.stem
        src_cat = get_file_category(src_ext)
        tgt_cat = get_file_category(tgt_ext)

        target_filepath = str(out_directory / f"{stem}.{tgt_ext}")

        if progress_callback:
            progress_callback(5.0, f"Iniciando conversão de .{src_ext} para .{tgt_ext}...")

        # -------------------------------------------------------------
        # 1. VIDEO CONVERSIONS
        # -------------------------------------------------------------
        if src_cat == 'video':
            # Video to Video or Video to GIF
            if tgt_cat == 'video' or tgt_ext == 'gif':
                res_file = VideoEngine.convert_video(
                    input_path=str(input_file),
                    output_path=target_filepath,
                    target_format=tgt_ext,
                    quality=options.get('quality', 'high'),
                    resolution=options.get('resolution'),
                    fps=options.get('fps'),
                    vcodec=options.get('vcodec'),
                    acodec=options.get('acodec'),
                    audio_bitrate=options.get('audio_bitrate', '320k'),
                    progress_callback=progress_callback
                )
                return cls._build_result(res_file)

            # Video to Audio (Audio Extraction)
            elif tgt_cat == 'audio':
                res_file = AudioEngine.convert_audio(
                    input_path=str(input_file),
                    output_path=target_filepath,
                    target_format=tgt_ext,
                    bitrate=options.get('audio_bitrate', '320k'),
                    sample_rate=options.get('sample_rate'),
                    channels=options.get('channels'),
                    normalize=options.get('normalize', False),
                    quality=options.get('quality', 'high'),
                    progress_callback=progress_callback
                )
                return cls._build_result(res_file)

        # -------------------------------------------------------------
        # 2. AUDIO CONVERSIONS
        # -------------------------------------------------------------
        elif src_cat == 'audio':
            if tgt_cat == 'audio':
                res_file = AudioEngine.convert_audio(
                    input_path=str(input_file),
                    output_path=target_filepath,
                    target_format=tgt_ext,
                    bitrate=options.get('audio_bitrate', '320k'),
                    sample_rate=options.get('sample_rate'),
                    channels=options.get('channels'),
                    normalize=options.get('normalize', False),
                    quality=options.get('quality', 'high'),
                    progress_callback=progress_callback
                )
                return cls._build_result(res_file)

        # -------------------------------------------------------------
        # 3. IMAGE CONVERSIONS
        # -------------------------------------------------------------
        elif src_cat == 'image':
            # Image to Image or Image to PDF
            if tgt_cat == 'image' or tgt_ext == 'pdf':
                res_file = ImageEngine.convert_image(
                    input_path=str(input_file),
                    output_path=target_filepath,
                    target_format=tgt_ext,
                    quality=int(options.get('image_quality', 98)),
                    width=options.get('width'),
                    height=options.get('height'),
                    scale=options.get('scale'),
                    dpi=int(options.get('dpi', 300)),
                    strip_metadata=options.get('strip_metadata', False),
                    progress_callback=progress_callback
                )
                return cls._build_result(res_file)

        # -------------------------------------------------------------
        # 4. DOCUMENT CONVERSIONS
        # -------------------------------------------------------------
        elif src_cat == 'document':
            # PDF -> DOCX
            if src_ext == 'pdf' and tgt_ext == 'docx':
                res_file = DocumentEngine.pdf_to_docx(str(input_file), target_filepath, progress_callback)
                return cls._build_result(res_file)

            # PDF -> TXT / MD
            elif src_ext == 'pdf' and tgt_ext in ['txt', 'md']:
                res_file = DocumentEngine.pdf_to_text(str(input_file), target_filepath, fmt=tgt_ext)
                return cls._build_result(res_file)

            # PDF -> HTML
            elif src_ext == 'pdf' and tgt_ext in ['html', 'htm']:
                res_file = DocumentEngine.pdf_to_html(str(input_file), target_filepath)
                return cls._build_result(res_file)

            # PDF -> Images (PNG, JPG, WEBP)
            elif src_ext == 'pdf' and tgt_cat == 'image':
                img_dir = out_directory / f"{stem}_imagens"
                generated_images = DocumentEngine.pdf_to_images(
                    pdf_path=str(input_file),
                    output_dir=str(img_dir),
                    target_fmt=tgt_ext,
                    dpi=int(options.get('dpi', 300)),
                    progress_callback=progress_callback
                )
                if len(generated_images) == 1:
                    # Single page, copy to target file
                    shutil.copyfile(generated_images[0], target_filepath)
                    shutil.rmtree(str(img_dir), ignore_errors=True)
                    return cls._build_result(target_filepath)
                else:
                    # Multi-page, bundle into a convenient ZIP archive
                    zip_path = str(out_directory / f"{stem}_paginas_{tgt_ext}.zip")
                    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
                        for img_p in generated_images:
                            z.write(img_p, arcname=Path(img_p).name)
                    shutil.rmtree(str(img_dir), ignore_errors=True)
                    return cls._build_result(zip_path)

            # DOCX -> PDF
            elif src_ext == 'docx' and tgt_ext == 'pdf':
                res_file = DocumentEngine.docx_to_pdf(str(input_file), target_filepath, progress_callback)
                return cls._build_result(res_file)

            # DOCX -> TXT / MD / HTML
            elif src_ext == 'docx' and tgt_ext in ['txt', 'md', 'html']:
                res_file = DocumentEngine.docx_to_text(str(input_file), target_filepath, fmt=tgt_ext)
                return cls._build_result(res_file)

            # TXT / MD -> PDF
            elif src_ext in ['txt', 'md'] and tgt_ext == 'pdf':
                res_file = DocumentEngine.text_to_pdf(str(input_file), target_filepath, is_markdown=(src_ext == 'md'))
                return cls._build_result(res_file)

            # TXT / MD -> DOCX
            elif src_ext in ['txt', 'md'] and tgt_ext == 'docx':
                res_file = DocumentEngine.text_to_docx(str(input_file), target_filepath)
                return cls._build_result(res_file)

            # CSV -> XLSX
            elif src_ext == 'csv' and tgt_ext in ['xlsx', 'xls']:
                res_file = DocumentEngine.csv_to_xlsx(str(input_file), target_filepath)
                return cls._build_result(res_file)

            # XLSX -> CSV
            elif src_ext in ['xlsx', 'xls'] and tgt_ext == 'csv':
                res_file = DocumentEngine.xlsx_to_csv(str(input_file), target_filepath)
                return cls._build_result(res_file)

            # CSV / XLSX -> PDF
            elif src_ext in ['csv', 'xlsx', 'xls'] and tgt_ext == 'pdf':
                res_file = DocumentEngine.spreadsheet_to_pdf(str(input_file), target_filepath)
                return cls._build_result(res_file)

            # JSON -> CSV / XLSX
            elif src_ext == 'json' and tgt_ext in ['csv', 'xlsx']:
                res_file = DocumentEngine.json_to_csv_or_xlsx(str(input_file), target_filepath, target_fmt=tgt_ext)
                return cls._build_result(res_file)

        # Unsupported or unhandled pair
        raise ValueError(
            f"A rota de conversão de .{src_ext} ({src_cat}) para .{tgt_ext} ({tgt_cat}) não é suportada diretamente."
        )

    @classmethod
    def _build_result(cls, file_path: str) -> Dict[str, Any]:
        p = Path(file_path)
        size = p.stat().st_size
        return {
            'file_path': str(p),
            'filename': p.name,
            'size_bytes': size,
            'size_formatted': cls._format_size(size),
            'extension': p.suffix.lstrip('.')
        }

    @staticmethod
    def _format_size(bytes_num: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_num < 1024.0:
                return f"{bytes_num:.1f} {unit}" if unit != 'B' else f"{bytes_num} B"
            bytes_num /= 1024.0
        return f"{bytes_num:.1f} TB"
