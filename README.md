# 🚀 SOUZAIA Universal Converter
### Conversor Universal de Alta Fidelidade (Documentos, Fotos, Áudio e Vídeo)

O **SOUZAIA Universal Converter** é uma aplicação completa e autônoma desenvolvida para converter qualquer formato de mídia e documento para qualquer outro formato compatível, garantindo preservação máxima de nitidez, fidelidade cromática, áudio de alta resolução e diagramação impecável.

---

## 🌟 Recursos Principais

- **Interface Gráfica Moderna (Web App)**: Visual futurista Glassmorphism escuro, arrastar-e-soltar (Drag & Drop), suporte para colar direto com `Ctrl + V`, barra de progresso em tempo real e download em lote `.ZIP`.
- **Interface de Linha de Comando (CLI)**: Para automações e usuários avançados no terminal.
- **100% Local e Privado**: Nenhum arquivo é enviado para servidores de terceiros. Todo o processamento ocorre no próprio hardware da sua máquina.
- **Padrão de Qualidade Profissional**:
  - **Vídeos**: H.264 / H.265 / ProRes / VP9 com CRF 18 (visualmente sem perdas), áudio 320 kbps e exportação para GIF animado com filtro `palettegen` de 2 passos.
  - **Áudios**: Extração direta de vídeos e conversão entre formatos com taxas de até 320 kbps CBR, PCM 24-bit e FLAC nível 8 (Lossless), com normalização EBU R128 opcional.
  - **Fotos e Imagens**: Reamostragem com algoritmo **LANCZOS**, suporte a até 300/600 DPI, perfis de cor preservados, subamostragem cromática 4:4:4 para evitar degradação de bordas e conversão inteligente para `.ICO` multi-resolução e `.PDF`.
  - **Documentos**: Conversão precisa entre **PDF, Word (.DOCX), Excel (.XLSX), CSV, TXT, Markdown (.MD) e HTML**, com renderização de páginas em 300 DPI ultra-nítidas.

---

## 📂 Formatos Suportados

| Categoria | Extensões Suportadas | Exemplos de Conversão |
| :--- | :--- | :--- |
| **🎬 Vídeos** | `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, `.flv`, `.wmv`, `.m4v`, `.mpg`, `.3gp`, `.ts`, `.gif` | MP4 ➔ WEBM, MKV ➔ MP4, Vídeo ➔ GIF fluido, Vídeo ➔ MP3 / WAV (extrair áudio) |
| **🎵 Áudios** | `.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`, `.m4a`, `.opus`, `.wma`, `.aiff`, `.alac` | WAV ➔ MP3 (320 kbps), FLAC ➔ WAV 24-bit, Áudio ➔ OPUS / OGG |
| **🖼️ Fotos & Imagens** | `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`, `.bmp`, `.tiff`, `.ico`, `.svg` | PNG ➔ WEBP, Imagem ➔ Ícone (.ICO), PNG ➔ PDF, SVG ➔ PNG (300 DPI) |
| **📄 Documentos** | `.pdf`, `.docx`, `.txt`, `.md`, `.html`, `.csv`, `.xlsx`, `.json`, `.xml` | PDF ➔ DOCX, DOCX ➔ PDF, TXT/MD ➔ PDF, CSV ➔ XLSX, PDF ➔ Imagens (300 DPI) |

---

## ⚡ Como Usar

### 1. Opção 1: Aplicativo Desktop Nativo (Sem navegador, 100% autônomo)
Dê dois cliques no arquivo:
```cmd
iniciar_conversor_desktop.bat
```
Ou execute no terminal:
```bash
.\.venv\Scripts\python.exe gui.py
```
*Abre uma janela nativa do Windows para selecionar qualquer arquivo, escolher a extensão e converter com barra de progresso imediata.*

### 2. Opção 2: Interface Web Moderna no Navegador
Dê dois cliques no arquivo:
```cmd
iniciar_conversor.bat
```
Ou execute no terminal:
```bash
.\.venv\Scripts\python.exe server.py
```
*Inicia o servidor e abre automaticamente em `http://127.0.0.1:5000`.*

### 3. Opção 3: Linha de Comando (CLI)
Você pode converter qualquer arquivo diretamente pelo terminal:

```bash
# Converter vídeo para MP3 a 320 kbps
.\.venv\Scripts\python.exe cli.py meu_video.mp4 -t mp3

# Converter foto para WebP com qualidade máxima
.\.venv\Scripts\python.exe cli.py foto.png -t webp --iq 100

# Converter relatório PDF para documento Word (.docx)
.\.venv\Scripts\python.exe cli.py relatorio.pdf -t docx

# Converter documento Word para PDF elegante
.\.venv\Scripts\python.exe cli.py contrato.docx -t pdf

# Extrair páginas do PDF em imagens PNG de 300 DPI
.\.venv\Scripts\python.exe cli.py catalogo.pdf -t png --dpi 300

# Converter vídeo para GIF animado ultra-nítido
.\.venv\Scripts\python.exe cli.py animacao.mp4 -t gif --fps 15

# Converter planilha CSV para Excel (.xlsx) com colunas auto-ajustadas
.\.venv\Scripts\python.exe cli.py dados.csv -t xlsx
```

---

## 🛠️ Estrutura do Projeto

```
SOUZAIA Aplicações/
├── core/
│   ├── media_info.py           # Análise e extração de metadados de arquivos
│   ├── video_engine.py         # Motor de vídeo e GIFs com FFmpeg
│   ├── audio_engine.py         # Motor de áudio de alta fidelidade
│   ├── image_engine.py         # Motor de imagens com Pillow & Lanczos
│   ├── document_engine.py      # Motor de documentos (PDF, DOCX, XLSX, etc.)
│   └── universal_converter.py  # Roteador central de conversões
├── static/
│   ├── css/style.css           # Estilos e temas Glassmorphism escuro
│   ├── js/app.js               # Lógica interativa, fila e uploads
│   └── index.html              # Interface Single-Page Application
├── cli.py                      # Interface de Linha de Comando
├── server.py                   # Servidor web local assíncrono (aiohttp)
├── iniciar_conversor.bat       # Inicializador para Windows em 1 clique
└── tests/
    └── test_converter.py       # Suíte de testes automatizados
```

Desenvolvido para **SOUZAIA Aplicações**.
