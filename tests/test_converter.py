import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.universal_converter import UniversalConverter
from core.media_info import inspect_media

def run_tests():
    print("=== INICIANDO TESTES DO SOUZAIA UNIVERSAL CONVERTER ===")
    test_dir = Path("temp_test_suite")
    test_dir.mkdir(exist_ok=True)
    out_dir = test_dir / "outputs"
    out_dir.mkdir(exist_ok=True)

    try:
        # 1. Test Image Conversions
        print("\n[1/4] Testando Imagens (PNG -> WEBP, JPG, ICO, PDF)...")
        from PIL import Image
        img_path = test_dir / "sample.png"
        img = Image.new("RGBA", (200, 200), (43, 108, 176, 255))
        img.save(img_path)

        for tgt in ['webp', 'jpg', 'ico', 'pdf', 'bmp']:
            res = UniversalConverter.convert(str(img_path), str(out_dir), tgt)
            print(f"  -> PNG para {tgt.upper()}: OK ({res['filename']} - {res['size_formatted']})")

        # 2. Test Documents (TXT -> PDF, TXT -> DOCX, DOCX -> PDF, CSV -> XLSX)
        print("\n[2/4] Testando Documentos...")
        txt_path = test_dir / "documento.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("# Relatorio Executivo SOUZAIA\nEste e um documento de teste oficial.\n- Item 1\n- Item 2\n")

        res_pdf = UniversalConverter.convert(str(txt_path), str(out_dir), "pdf")
        print(f"  -> TXT para PDF: OK ({res_pdf['filename']} - {res_pdf['size_formatted']})")

        res_docx = UniversalConverter.convert(str(txt_path), str(out_dir), "docx")
        print(f"  -> TXT para DOCX: OK ({res_docx['filename']} - {res_docx['size_formatted']})")

        res_docx_pdf = UniversalConverter.convert(res_docx['file_path'], str(out_dir), "pdf")
        print(f"  -> DOCX para PDF: OK ({res_docx_pdf['filename']} - {res_docx_pdf['size_formatted']})")

        # PDF to Images
        res_pdf_img = UniversalConverter.convert(res_pdf['file_path'], str(out_dir), "png")
        print(f"  -> PDF para PNG (300 DPI): OK ({res_pdf_img['filename']} - {res_pdf_img['size_formatted']})")

        # CSV to XLSX and PDF
        csv_path = test_dir / "tabela.csv"
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("Nome,Cargo,Salario,Status\nMauricio,Engenheiro,15000,Ativo\nAna,Diretora,22000,Ativo\n")

        res_xlsx = UniversalConverter.convert(str(csv_path), str(out_dir), "xlsx")
        print(f"  -> CSV para XLSX: OK ({res_xlsx['filename']} - {res_xlsx['size_formatted']})")

        res_table_pdf = UniversalConverter.convert(res_xlsx['file_path'], str(out_dir), "pdf")
        print(f"  -> XLSX para PDF: OK ({res_table_pdf['filename']} - {res_table_pdf['size_formatted']})")

        # 3. Test Audio & Video Generation via FFmpeg
        print("\n[3/4] Testando Audio e Video com FFmpeg...")
        import subprocess
        # Generate 1 second synthetic sine wave audio
        synth_audio = test_dir / "sine.wav"
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=1000:duration=1",
            str(synth_audio)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        res_mp3 = UniversalConverter.convert(str(synth_audio), str(out_dir), "mp3")
        print(f"  -> WAV para MP3 (320kbps): OK ({res_mp3['filename']} - {res_mp3['size_formatted']})")

        res_flac = UniversalConverter.convert(str(synth_audio), str(out_dir), "flac")
        print(f"  -> WAV para FLAC (Lossless): OK ({res_flac['filename']} - {res_flac['size_formatted']})")

        # Generate 1 second test video
        synth_video = test_dir / "test_video.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=1000:duration=1",
            "-c:v", "libx264", "-c:a", "aac", str(synth_video)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        res_webm = UniversalConverter.convert(str(synth_video), str(out_dir), "webm")
        print(f"  -> MP4 para WEBM: OK ({res_webm['filename']} - {res_webm['size_formatted']})")

        res_gif = UniversalConverter.convert(str(synth_video), str(out_dir), "gif")
        print(f"  -> MP4 para GIF (Palettegen Alta Qualidade): OK ({res_gif['filename']} - {res_gif['size_formatted']})")

        res_ext_audio = UniversalConverter.convert(str(synth_video), str(out_dir), "mp3")
        print(f"  -> MP4 extraindo Audio para MP3: OK ({res_ext_audio['filename']} - {res_ext_audio['size_formatted']})")

        # 4. Media Inspection
        print("\n[4/4] Testando Inspecao de Midia...")
        info = inspect_media(str(synth_video))
        print(f"  -> Inspecao Video: {info['category']} | {info['details'].get('resolution')} | {info['details'].get('duration_formatted')}")
        print(f"  -> Formatos compativeis sugeridos: {info['target_formats']}")

        print("\n=======================================================")
        print(">>> TODOS OS TESTES PASSARAM COM 100% DE SUCESSO! <<<")
        print("=======================================================")

    finally:
        # Cleanup test files
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)

if __name__ == '__main__':
    run_tests()
