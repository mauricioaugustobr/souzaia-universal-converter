#!/usr/bin/env python3
"""
SOUZAIA Universal Converter - Interface de Linha de Comando (CLI)
Exemplos de uso:
  python cli.py video.mp4 -t mp3
  python cli.py foto.png -t webp --quality 100
  python cli.py relatorio.pdf -t docx
  python cli.py documento.docx -t pdf
  python cli.py gravacao.wav -t flac
  python cli.py video.mp4 -t gif --fps 15
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.universal_converter import UniversalConverter
from core.media_info import inspect_media, get_file_category

def main():
    parser = argparse.ArgumentParser(
        description="SOUZAIA Universal Converter - Conversor de Alta Fidelidade (Documento, Foto, Áudio e Vídeo)"
    )
    parser.add_argument("input", help="Caminho do arquivo de entrada")
    parser.add_argument("-t", "--target", required=True, help="Extensão de destino (ex: mp4, mp3, pdf, docx, png, webp, gif, flac)")
    parser.add_argument("-o", "--output-dir", default="./outputs", help="Diretório de saída (padrão: ./outputs)")
    parser.add_argument("-q", "--quality", default="high", choices=["ultra", "high", "balanced", "web"], help="Nível de qualidade para áudio/vídeo")
    parser.add_argument("--iq", "--image-quality", type=int, default=98, help="Qualidade de imagem (1 a 100, padrão: 98)")
    parser.add_argument("--res", "--resolution", default=None, help="Resolução de vídeo/imagem (ex: 1080p, 720p, 1920x1080)")
    parser.add_argument("--fps", type=int, default=None, help="Taxa de quadros por segundo (FPS)")
    parser.add_argument("--bitrate", default="320k", help="Taxa de bits de áudio (ex: 320k, 256k, 192k)")
    parser.add_argument("--dpi", type=int, default=300, help="DPI para documentos e imagens (padrão: 300)")
    parser.add_argument("--normalize", action="store_true", help="Normalizar volume do áudio (EBU R128)")
    parser.add_argument("--info", action="store_true", help="Apenas exibe informações detalhadas da mídia")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"\n[ERRO] Arquivo não encontrado: {input_path}")
        sys.exit(1)

    if args.info:
        info = inspect_media(str(input_path))
        print("\n=== METADADOS DA MÍDIA ===")
        print(f"Arquivo: {info['filename']}")
        print(f"Categoria: {info['category'].upper()}")
        print(f"Tamanho: {info['size_formatted']}")
        print("Detalhes:", info['details'])
        print("Formatos sugeridos:", ", ".join(info['target_formats']))
        return

    print("\n=======================================================")
    print(f" SOUZAIA UNIVERSAL CONVERTER")
    print(f" Convertendo: {input_path.name} -> .{args.target.lower()}")
    print("=======================================================\n")

    # Force UTF-8 stdout if needed on Windows
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    def on_progress(pct: float, message: str):
        bar_len = 25
        filled = int(bar_len * (pct / 100.0))
        bar = "#" * filled + "-" * (bar_len - filled)
        try:
            sys.stdout.write(f"\r[{bar}] {pct:5.1f}% | {message}")
            sys.stdout.flush()
        except Exception:
            pass

    options = {
        'quality': args.quality,
        'image_quality': args.iq,
        'resolution': args.res,
        'fps': args.fps,
        'audio_bitrate': args.bitrate,
        'dpi': args.dpi,
        'normalize': args.normalize
    }

    try:
        result = UniversalConverter.convert(
            input_path=str(input_path),
            output_dir=args.output_dir,
            target_format=args.target,
            options=options,
            progress_callback=on_progress
        )
        print("\n\n[SUCESSO] Arquivo gerado:")
        print(f"  -> Caminho: {result['file_path']}")
        print(f"  -> Tamanho final: {result['size_formatted']}")
        print("=======================================================\n")
    except Exception as e:
        print(f"\n\n[FALHA NA CONVERSÃO]: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
