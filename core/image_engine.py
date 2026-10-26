import os
import io
from pathlib import Path
from typing import Optional, Callable, List, Tuple
from PIL import Image, ImageOps

try:
    import pymupdf
except ImportError:
    import fitz as pymupdf

class ImageEngine:
    """
    Motor de conversão de imagens com altíssima fidelidade e preservação de qualidade.
    """

    @classmethod
    def convert_image(
        cls,
        input_path: str,
        output_path: str,
        target_format: str,
        quality: int = 98,
        width: Optional[int] = None,
        height: Optional[int] = None,
        scale: Optional[float] = None,
        dpi: int = 300,
        strip_metadata: bool = False,
        background_color: Tuple[int, int, int] = (255, 255, 255),
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> str:
        input_file = Path(input_path).resolve()
        output_file = Path(output_path).resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)
        target_fmt = target_format.lower().lstrip('.')

        if progress_callback:
            progress_callback(10.0, "Carregando imagem...")

        # Handle SVG input via PyMuPDF rasterization if needed
        is_svg_input = input_file.suffix.lower() == '.svg'
        if is_svg_input:
            img = cls._load_svg(str(input_file), dpi=dpi)
        else:
            img = Image.open(str(input_file))

        # Auto-orient using EXIF data (e.g. smartphone cameras)
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        if progress_callback:
            progress_callback(30.0, "Processando geometria e cores...")

        # Handle Resizing
        orig_w, orig_h = img.size
        new_w, new_h = orig_w, orig_h

        if scale and scale > 0:
            new_w = max(1, int(orig_w * scale))
            new_h = max(1, int(orig_h * scale))
        elif width and height:
            new_w, new_h = width, height
        elif width:
            new_w = width
            new_h = max(1, int(orig_h * (width / orig_w)))
        elif height:
            new_h = height
            new_w = max(1, int(orig_w * (height / orig_h)))

        if (new_w, new_h) != (orig_w, orig_h):
            img = img.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)

        if progress_callback:
            progress_callback(60.0, f"Codificando para {target_fmt.upper()} com máxima qualidade...")

        # Convert to target format
        cls._save_image(
            img=img,
            output_file=output_file,
            target_fmt=target_fmt,
            quality=quality,
            dpi=dpi,
            strip_metadata=strip_metadata,
            background_color=background_color
        )

        if progress_callback:
            progress_callback(100.0, "Imagem salva com sucesso!")

        return str(output_file)

    @classmethod
    def _load_svg(cls, svg_path: str, dpi: int = 300) -> Image.Image:
        """Carrega e rasteriza um arquivo vetorial SVG em alta resolução"""
        doc = pymupdf.open(svg_path)
        page = doc[0]
        # Calculate zoom factor from DPI (default 72 dpi)
        zoom = dpi / 72.0
        mat = pymupdf.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=True)
        img_data = pix.tobytes("png")
        doc.close()
        return Image.open(io.BytesIO(img_data))

    @classmethod
    def _save_image(
        cls,
        img: Image.Image,
        output_file: Path,
        target_fmt: str,
        quality: int,
        dpi: int,
        strip_metadata: bool,
        background_color: Tuple[int, int, int]
    ):
        save_kwargs = {}
        if not strip_metadata and 'exif' in img.info:
            save_kwargs['exif'] = img.info['exif']

        # Format-specific adjustments
        if target_fmt in ['jpg', 'jpeg']:
            # JPEG doesn't support alpha transparency; blend with solid background
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                alpha = img.convert('RGBA')
                bg = Image.new('RGB', alpha.size, background_color)
                bg.paste(alpha, mask=alpha.split()[3])
                img = bg
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # subsampling=0 ensures 4:4:4 chroma subsampling (no color fringing)
            img.save(
                output_file,
                format='JPEG',
                quality=quality,
                subsampling=0,
                optimize=True,
                progressive=True,
                dpi=(dpi, dpi),
                **save_kwargs
            )

        elif target_fmt == 'png':
            img.save(
                output_file,
                format='PNG',
                optimize=True,
                compress_level=9,
                dpi=(dpi, dpi),
                **save_kwargs
            )

        elif target_fmt == 'webp':
            lossless = (quality >= 100)
            img.save(
                output_file,
                format='WEBP',
                quality=quality,
                lossless=lossless,
                method=6,  # Highest quality compression effort
                **save_kwargs
            )

        elif target_fmt == 'ico':
            # Generate multi-resolution crisp Windows ICO
            sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            img.save(output_file, format='ICO', sizes=sizes)

        elif target_fmt in ['tiff', 'tif']:
            img.save(
                output_file,
                format='TIFF',
                compression='tiff_lzw',
                dpi=(dpi, dpi),
                **save_kwargs
            )

        elif target_fmt == 'bmp':
            if img.mode in ('RGBA', 'LA'):
                alpha = img.convert('RGBA')
                bg = Image.new('RGB', alpha.size, background_color)
                bg.paste(alpha, mask=alpha.split()[3])
                img = bg
            img.save(output_file, format='BMP')

        elif target_fmt == 'gif':
            img.save(output_file, format='GIF', optimize=True)

        elif target_fmt == 'pdf':
            # Save image as a high resolution PDF document
            if img.mode == 'RGBA':
                alpha = img.convert('RGBA')
                bg = Image.new('RGB', alpha.size, background_color)
                bg.paste(alpha, mask=alpha.split()[3])
                img = bg
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(output_file, format='PDF', resolution=dpi)

        elif target_fmt == 'svg':
            # Vector container embedding high quality raster image
            cls._save_as_svg_wrapper(img, output_file)

        else:
            # Fallback to Pillow's native handler
            img.save(output_file, dpi=(dpi, dpi), **save_kwargs)

    @classmethod
    def _save_as_svg_wrapper(cls, img: Image.Image, output_file: Path):
        """Salva a imagem dentro de um container vetorial SVG de alta resolução"""
        import base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        b64 = base64.b64encode(buffer.getvalue()).decode('ascii')
        w, h = img.size

        svg_content = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <image width="{w}" height="{h}" xlink:href="data:image/png;base64,{b64}"/>
</svg>'''
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(svg_content)

    @classmethod
    def combine_images_to_pdf(
        cls,
        image_paths: List[str],
        output_path: str,
        dpi: int = 300,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> str:
        """Combina múltiplas imagens em um único documento PDF em ordem"""
        output_file = Path(output_path).resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)

        images = []
        total = len(image_paths)

        for idx, p in enumerate(image_paths):
            if progress_callback:
                progress_callback((idx / total) * 80.0, f"Processando imagem {idx+1}/{total}...")
            img = Image.open(p)
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass
            if img.mode != 'RGB':
                alpha = img.convert('RGBA')
                bg = Image.new('RGB', alpha.size, (255, 255, 255))
                bg.paste(alpha, mask=alpha.split()[3])
                img = bg
            images.append(img)

        if not images:
            raise ValueError("Nenhuma imagem fornecida para o PDF.")

        if progress_callback:
            progress_callback(85.0, "Gerando documento PDF consolidado...")

        first_img = images[0]
        rest_imgs = images[1:] if len(images) > 1 else []
        first_img.save(
            str(output_file),
            format='PDF',
            save_all=True,
            append_images=rest_imgs,
            resolution=dpi
        )

        if progress_callback:
            progress_callback(100.0, "PDF criado com sucesso!")

        return str(output_file)
