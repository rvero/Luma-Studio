# Luma Studio

Aplicativo desktop para baixar e converter mídias, editar imagens, identificar cores e ampliar imagens com o Upscayl. O projeto está em desenvolvimento.

## Recursos

- Download com yt-dlp, incluindo escolha do formato e uso opcional dos cookies de navegadores compatíveis.
- Conversão de vídeo e áudio com FFmpeg, incluindo GIF e extração de áudio.
- Conversão e redimensionamento de imagens com ImageMagick, a partir de arquivos locais ou links diretos.
- Seletor de cores com lupa, valores HEX/RGB/HSL, paleta da imagem e histórico.
- Ampliação com o motor Upscayl, de 2× a 16×, com modelos compatíveis e processamento em lote.
- Compressão ZIP, de imagens, vídeos e áudios, com opções de qualidade conforme o tipo.

## Requisitos

- Python 3.10 ou superior, com Tkinter.
- [yt-dlp](https://github.com/yt-dlp/yt-dlp#installation), [FFmpeg](https://ffmpeg.org/download.html) e [ImageMagick](https://imagemagick.org/script/download.php), disponíveis no `PATH`.
- Para upscale: [Upscayl](https://github.com/upscayl/upscayl), seu motor e modelos instalados separadamente, além de hardware e drivers Vulkan compatíveis.
- No Linux, `xclip` (X11) ou `wl-clipboard` (Wayland) para copiar e colar imagens.

### Windows

Instale Python, FFmpeg e ImageMagick. No instalador do ImageMagick, adicione os executáveis ao PATH. No PowerShell, dentro da pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt yt-dlp
```

Abra `Iniciar Luma.bat`. O arquivo adiciona o ambiente virtual ao PATH ao iniciar, permitindo localizar o yt-dlp instalado nele. O FFmpeg e o ImageMagick também precisam estar disponíveis no PATH do sistema.

### Ubuntu

```sh
sudo apt install python3 python3-venv python3-tk imagemagick ffmpeg xclip wl-clipboard
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt yt-dlp
python app.py
```

### Arch Linux

```sh
sudo pacman -S python python-pip tk imagemagick ffmpeg xclip wl-clipboard
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt yt-dlp
python app.py
```

O suporte a sites e formatos depende das versões e dos recursos das ferramentas instaladas. Algumas publicações podem exigir autenticação ou não estar disponíveis para download.

## Uso

- **Baixar mídia:** informe o link, a pasta e o formato. A lista de navegadores mostra os navegadores compatíveis detectados; a presença na lista não garante acesso aos cookies.
- **Converter mídia:** escolha o arquivo e o formato de saída. Áudio convertido em vídeo recebe uma tela preta; GIF não contém som.
- **Editar imagem:** escolha um arquivo, cole uma imagem ou informe um link direto. A disponibilidade de AVIF e outros formatos depende da instalação do ImageMagick. Imagens baixadas por link têm limite de 50 MB.
- **Seletor de cores:** abra ou cole uma imagem e clique no ponto desejado. A paleta é gerada a partir da imagem; o histórico guarda cores selecionadas durante a sessão.
- **Upscale IA:** o aplicativo tenta detectar o Upscayl instalado. Também é possível informar a pasta ou os caminhos do motor e dos modelos. Escalas acima da nativa do modelo usam várias passagens e, quando necessário, redimensionamento. Escalas altas podem exigir muita memória. Confira as licenças dos modelos, inclusive as restrições de uso comercial.
- **Comprimir:** use ZIP para preservar o arquivo completo. A conversão sem perda de mídia pode produzir arquivos maiores e não preserva necessariamente todas as faixas e metadados; algumas fontes de áudio podem ter sua precisão reduzida pelo FLAC. Use ZIP para preservar os bytes originais.

Os atalhos Ctrl+C e Ctrl+V funcionam nos campos de texto. Nas telas de imagem, podem copiar e colar imagens quando o foco não estiver em um campo de texto. A transparência de imagens copiadas no Windows pode não ser preservada.

## Testes

Com o ambiente virtual ativado:

```sh
python -m unittest
```

Alguns testes abrem janelas Tkinter e exigem uma sessão gráfica. O aplicativo foi desenvolvido no Windows; Arch e Ubuntu ainda precisam de validação completa.
