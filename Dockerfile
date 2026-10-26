# Imagem base oficial leve do Python
FROM python:3.12-slim

# Instala o FFmpeg e bibliotecas do sistema para processamento multimídia
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-dejavu-core \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Instalação das dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código fonte do conversor
COPY . .

# Cria os diretórios necessários
RUN mkdir -p uploads outputs

# Define a porta padrão do Render
ENV PORT=10000
EXPOSE 10000

# Executa o servidor da aplicação
CMD ["python", "server.py"]
