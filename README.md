# Replay de Webcam

POC simples em Python para visualizar uma webcam e salvar um replay dos últimos 10 segundos em MP4.

## Requisitos

- Python 3
- Webcam conectada

## Instalação

Na pasta do projeto, instale a dependência:

```bash
python -m pip install -r requirements.txt
```

## Como usar

Inicie o programa:

```bash
python main.py
```

- Pressione `R` para salvar os 10 segundos anteriores em um arquivo MP4.
- Pressione `Q` para encerrar o programa.

O programa mantém até 30 segundos de vídeo em buffer. Aguarde pelo menos 10 segundos após iniciar antes de pedir o primeiro replay. Os arquivos são salvos na pasta em que o programa foi executado.
