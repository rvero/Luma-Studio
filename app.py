import os
import colorsys
import webbrowser
import shutil
import subprocess
import tempfile
import threading
import re
import zipfile
import urllib.parse
import urllib.request
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageTk, ImageOps
from core import download_command, image_command, media_command, pixel_hex
import image_clipboard
from color_tools import image_palette, magnified_pixel
from browser_detection import detect_browsers
from icons import make_icon, make_logo, logo_image
from visual_design import swatch_text_color
from task_utils import hidden_flags, progress_from_line, suggested_name, compression_command, upscale_plan

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('blue')
# Consistent surfaces for secondary actions and inputs across all screens.
ctk.ThemeManager.theme['CTkButton'].update(fg_color='#29384e', hover_color='#405675', corner_radius=8)
ctk.ThemeManager.theme['CTkOptionMenu'].update(fg_color='#29384e', button_color='#405675', button_hover_color='#536b90', corner_radius=8)
ctk.ThemeManager.theme['CTkSegmentedButton'].update(fg_color='#101a28', selected_color='#526fbb', selected_hover_color='#6483d3', unselected_color='#29384e', unselected_hover_color='#405675')
ctk.ThemeManager.theme['CTkEntry'].update(fg_color='#0f1722', border_color='#344255', text_color='#edf2fb', placeholder_text_color='#9aaac0', corner_radius=8)
BG = '#0b1018'
PANEL = '#151d29'
MUTED = '#8e9caf'
ACCENT = '#7c9cff'

class SmoothScrollFrame(ctk.CTkScrollableFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind_all('<Button-4>', self._linux_wheel, add='+')
        self.bind_all('<Button-5>', self._linux_wheel, add='+')
        self.bind('<Configure>', self._update_region, add='+')
        self._parent_canvas.bind('<Configure>', self._update_region, add='+')

    def _update_region(self, event=None):
        if not self.winfo_exists(): return
        canvas = self._parent_canvas
        width = max(canvas.winfo_width(), self.winfo_reqwidth())
        height = max(canvas.winfo_height(), self.winfo_reqheight())
        canvas.configure(scrollregion=(0, 0, width, height))
        if self.winfo_reqheight() <= canvas.winfo_height(): canvas.yview_moveto(0)

    def _linux_wheel(self, event):
        if self.winfo_exists() and self.check_if_master_is_canvas(event.widget):
            self._animate_scroll(-1 if event.num == 4 else 1, 5)

    def _mouse_wheel_all(self, event):
        if self.winfo_exists() and self.check_if_master_is_canvas(event.widget):
            direction = -1 if event.delta > 0 else 1
            if event.delta: self._animate_scroll(direction, 5)

    def _animate_scroll(self, direction, remaining):
        if not self.winfo_exists() or remaining <= 0: return
        first, last = self._parent_canvas.yview()
        if (direction < 0 and first <= 0) or (direction > 0 and last >= 1): return
        self._parent_canvas.yview_scroll(direction * 8, 'units')
        if remaining > 1: self.after(12, lambda: self._animate_scroll(direction, remaining - 1))

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('Luma Studio')
        self.window_icon = ImageTk.PhotoImage(logo_image(64))
        self.iconphoto(True, self.window_icon)
        if os.name == 'nt':
            icon_path = Path(__file__).parent / 'assets' / 'luma.ico'
            if icon_path.is_file(): self.iconbitmap(default=str(icon_path))
        self.geometry('1120x760')
        self.minsize(850, 600)
        self.configure(fg_color=BG)
        self.image = None
        self.image_path = None
        self.preview_photo = None
        self.color_history = []
        self.palette_colors = []
        self.temp = tempfile.TemporaryDirectory(prefix='luma-')
        self.task_running = False
        self.up_config = None
        self.protocol('WM_DELETE_WINDOW', self.close_app)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color='#101722')
        self.sidebar.grid(row=0, column=0, sticky='nsew')
        self.sidebar.grid_propagate(False)
        brand = ctk.CTkFrame(self.sidebar, fg_color='transparent')
        brand.pack(fill='x', padx=22, pady=(28, 32))
        self.brand_image = make_logo(40)
        ctk.CTkLabel(brand, text='', image=self.brand_image, width=40, height=40).pack(side='left')
        brand_text = ctk.CTkFrame(brand, fg_color='transparent')
        brand_text.pack(side='left', padx=(12, 0))
        ctk.CTkLabel(brand_text, text='Luma', anchor='w', height=24, font=ctk.CTkFont(size=21, weight='bold'), text_color='#f3f6ff').pack(fill='x')
        ctk.CTkLabel(brand_text, text='STUDIO', anchor='w', height=16, font=ctk.CTkFont(size=10, weight='bold'), text_color='#a5b6cf').pack(fill='x')
        self.nav = {}
        self.nav_icons = {key: make_icon(key) for key in ('download', 'convert', 'image', 'picker', 'upscale', 'compress')}
        for name, icon in [('Baixar mídia', 'download'), ('Converter mídia', 'convert'), ('Editar imagem', 'image'), ('Seletor de cores', 'picker'), ('Upscale IA', 'upscale'), ('Comprimir', 'compress')]:
            button = ctk.CTkButton(self.sidebar, text=name, image=self.nav_icons[icon], compound='left', anchor='w', font=ctk.CTkFont(size=13), height=44, corner_radius=10, fg_color='transparent', hover_color='#25334a', text_color='#b9c5d8', command=lambda n=name: self.show(n))
            button.pack(fill='x', padx=12, pady=3)
            self.nav[name] = button
        self.content = ctk.CTkFrame(self, fg_color=BG)
        self.content.grid(row=0, column=1, sticky='nsew', padx=30, pady=24)
        footer = ctk.CTkFrame(self, fg_color='#101722', corner_radius=0)
        self.progress_footer = footer
        self.progress_label = ctk.CTkLabel(footer, text='Pronto', width=180, anchor='w', text_color=MUTED)
        self.progress_label.pack(side='left', padx=(10, 8))
        self.progress_bar = ctk.CTkProgressBar(footer, height=8, progress_color=ACCENT)
        self.progress_bar.pack(side='left', fill='x', expand=True, padx=(0, 12), pady=12); self.progress_bar.set(0)
        self.bind_all('<Control-v>', self.paste_shortcut, add='+')
        self.bind_all('<Control-c>', self.copy_shortcut, add='+')
        self.show('Baixar mídia')

    def close_app(self):
        self.temp.cleanup()
        self.destroy()

    def show(self, page):
        self.current_page = page
        for child in self.content.winfo_children(): child.destroy()
        for name, button in self.nav.items():
            button.configure(fg_color='#263653' if name == page else 'transparent', text_color='#f7f9ff' if name == page else '#c3cee0')
        {'Baixar mídia': self.download_page, 'Converter mídia': self.media_page, 'Editar imagem': self.edit_page, 'Seletor de cores': self.color_page, 'Upscale IA': self.upscale_page, 'Comprimir': self.compress_page}[page]()

    def header(self, eyebrow, title, subtitle):
        ctk.CTkLabel(self.content, text=title, anchor='w', height=34, text_color='#f3f6ff', font=ctk.CTkFont(size=26, weight='bold')).pack(fill='x', pady=(0, 18))

    def card(self):
        f = SmoothScrollFrame(self.content, fg_color=PANEL, corner_radius=14, scrollbar_button_color='#40506a', scrollbar_button_hover_color='#627a9b')
        f.pack(fill='both', expand=True)
        self.current_card = f
        return f

    def label(self, parent, text):
        ctk.CTkLabel(parent, text=text[:1].upper() + text[1:].lower(), text_color='#c5d1e2', font=ctk.CTkFont(size=12, weight='bold')).pack(anchor='w', padx=24, pady=(14, 4))

    def entry(self, parent, placeholder=''):
        e = ctk.CTkEntry(parent, placeholder_text=placeholder, height=42, fg_color='#0f1722', border_color='#344255', corner_radius=8)
        e.pack(fill='x', padx=24)
        return e

    def button(self, parent, text, command):
        b = ctk.CTkButton(parent, text=text, command=command, height=42, fg_color=ACCENT, hover_color='#6686e3', text_color='#101725', font=ctk.CTkFont(weight='bold'), corner_radius=8)
        b.pack(anchor='w', padx=24, pady=(18, 10))
        return b

    def status(self, parent, text=''):
        self.status_label = ctk.CTkLabel(parent, text='', text_color=MUTED, wraplength=650, justify='left')
        self.status_label.pack(anchor='w', padx=24, pady=(0, 8))

    def set_status(self, text):
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            error = text.startswith(('Não foi possível', 'Erro', 'Falhou'))
            self.status_label.configure(text=text, text_color='#ffb4ab' if error else '#b4c3d8')

    def set_progress(self, value=None, label=None):
        if value is None:
            self.progress_bar.configure(mode='indeterminate'); self.progress_bar.start()
            self.progress_label.configure(text=label or 'Processando…')
        else:
            self.progress_bar.stop(); self.progress_bar.configure(mode='determinate')
            self.progress_bar.set(max(0, min(1, value / 100)))
            self.progress_label.configure(text=label or f'{value:.0f}%')

    def report_progress(self, value, label=None):
        self.after(0, lambda: self.set_progress(value, label))

    def run_process(self, cmd, duration=None, downloader=False):
        if duration:
            cmd = cmd[:-1] + ['-progress', 'pipe:1', '-nostats', cmd[-1]]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, errors='replace', creationflags=hidden_flags(), bufsize=1)
        lines = []
        for line in process.stdout:
            lines.append(line)
            if len(lines) > 60: lines.pop(0)
            percent = progress_from_line(line) if downloader else None
            if duration and line.startswith('out_time_us='):
                try: percent = int(line.split('=', 1)[1]) / 1000000 / duration * 100
                except ValueError: pass
            if percent is not None: self.report_progress(min(99, percent))
            elif downloader and ('[ExtractAudio]' in line or '[Merger]' in line or '[VideoConvertor]' in line):
                self.report_progress(None, 'Convertendo…')
        if process.wait(): raise RuntimeError(''.join(lines)[-1500:] or 'A tarefa falhou.')

    def run_background(self, task, done):
        if self.task_running:
            self.set_status('Aguarde a tarefa em andamento.'); return
        self.task_running = True
        self.progress_footer.grid(row=1, column=1, sticky='ew', padx=30, pady=(0, 14))
        self.set_progress(None)
        def finish(result=None, error=None):
            self.task_running = False
            self.progress_bar.stop(); self.progress_footer.grid_remove()
            if error is not None:
                self.set_status('Não foi possível concluir: ' + error)
            else:
                done(result)
        def worker():
            try:
                result = task()
                self.after(0, lambda: finish(result=result))
            except Exception as exc:
                msg = str(exc)
                self.after(0, lambda: finish(error=msg))
        threading.Thread(target=worker, daemon=True).start()

    def download_page(self):
        self.header('yt-dlp', 'Baixar mídia', 'Baixe vídeos do YouTube, Instagram, Facebook, X/Twitter e outros sites suportados.')
        card = self.card()
        self.label(card, 'LINK DO VÍDEO')
        url_row = ctk.CTkFrame(card, fg_color='transparent'); url_row.pack(fill='x', padx=24)
        self.url = ctk.CTkEntry(url_row, placeholder_text='https://...', height=42, fg_color='#0f1722', border_color='#344255'); self.url.pack(side='left', fill='x', expand=True)
        ctk.CTkButton(url_row, text='Colar', width=75, height=42, fg_color='#29384e', command=lambda: self.paste_to_entry(self.url)).pack(side='left', padx=(8,0))
        self.label(card, 'PASTA DE DESTINO')
        row = ctk.CTkFrame(card, fg_color='transparent'); row.pack(fill='x', padx=24)
        self.destination = ctk.CTkEntry(row, height=42, fg_color='#0f1722', border_color='#344255'); self.destination.pack(side='left', fill='x', expand=True)
        self.destination.insert(0, str(Path.home() / 'Downloads'))
        ctk.CTkButton(row, text='Escolher', width=100, height=42, fg_color='#29384e', command=self.choose_destination).pack(side='left', padx=(8, 0))
        ctk.CTkButton(row, text='Colar', width=75, height=42, fg_color='#29384e', command=lambda: self.paste_to_entry(self.destination)).pack(side='left', padx=(8,0))
        self.label(card, 'FORMATO DE SAÍDA')
        self.download_format = ctk.CTkOptionMenu(card, values=['Original', 'MP4', 'MKV', 'WEBM', 'MOV', 'MP3', 'M4A', 'OPUS', 'WAV', 'FLAC', 'VORBIS'], height=40, fg_color='#29384e')
        self.download_format.pack(fill='x', padx=24)
        ctk.CTkButton(card, text='Ver sites suportados', fg_color='transparent', anchor='w', command=lambda: webbrowser.open('https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md')).pack(anchor='w', padx=24)
        self.label(card, 'LOGIN OPCIONAL · COOKIES DO NAVEGADOR')
        self.browser = ctk.CTkOptionMenu(card, values=['Sem login'] + detect_browsers(), height=40, fg_color='#29384e')
        self.browser.pack(fill='x', padx=24)
        self.button(card, 'Iniciar download', self.download)
        self.status(card, 'Alguns sites exigem login ou restringem downloads. Mantenha o yt-dlp atualizado; MP3 precisa de FFmpeg.')

    def choose_destination(self):
        path = filedialog.askdirectory()
        if path: self.destination.delete(0, 'end'); self.destination.insert(0, path)

    def download(self):
        url, dest = self.url.get().strip(), self.destination.get().strip()
        exe = shutil.which('yt-dlp')
        if not exe: self.set_status('yt-dlp não encontrado. Instale-o e confira se está no PATH.'); return
        if urllib.parse.urlparse(url).scheme not in ('http', 'https') or not os.path.isdir(dest): self.set_status('Informe um link HTTP(S) e uma pasta existente.'); return
        browser = self.browser.get()
        cmd = download_command(exe, url, dest, browser=None if browser == 'Sem login' else browser.lower(), format_name=self.download_format.get().lower())
        self.set_status('Download em andamento. Aguarde...')
        def task():
            self.run_process(cmd, downloader=True)
            return 'Download concluído em ' + dest
        self.run_background(task, self.set_status)

    def media_page(self):
        self.header('FFmpeg', 'Converter vídeo e áudio', 'Converta um arquivo ou extraia o áudio de um vídeo.')
        card = self.card()
        self.label(card, 'ARQUIVO DE ORIGEM')
        row = ctk.CTkFrame(card, fg_color='transparent'); row.pack(fill='x', padx=24)
        self.media_source = ctk.CTkEntry(row, placeholder_text='Escolha um vídeo ou áudio', height=42, fg_color='#0f1722', border_color='#344255')
        self.media_source.pack(side='left', fill='x', expand=True)
        ctk.CTkButton(row, text='Abrir arquivo', width=110, height=42, fg_color='#29384e', command=self.choose_media).pack(side='left', padx=(8, 0))
        ctk.CTkButton(row, text='Colar', width=75, height=42, fg_color='#29384e', command=lambda: self.paste_to_entry(self.media_source)).pack(side='left', padx=(8,0))
        self.label(card, 'TIPO DE CONVERSÃO')
        self.media_type = ctk.CTkSegmentedButton(card, values=['Vídeo', 'Áudio'], command=self.change_media_type)
        self.media_type.pack(fill='x', padx=24); self.media_type.set('Vídeo')
        self.label(card, 'FORMATO DE SAÍDA')
        self.media_format = ctk.CTkOptionMenu(card, values=['MP4', 'MKV', 'WEBM', 'MOV', 'GIF'], height=40, fg_color='#29384e', button_color='#405675', button_hover_color='#526b90')
        self.media_format.pack(fill='x', padx=24)
        self.label(card, 'QUALIDADE')
        self.media_quality = ctk.CTkOptionMenu(card, values=['Equilibrada', 'Alta', 'Menor arquivo'], height=40, fg_color='#29384e', button_color='#405675', button_hover_color='#526b90')
        self.media_quality.pack(fill='x', padx=24)
        self.button(card, 'Escolher destino e converter', self.convert_media)
        self.status(card, 'Áudio para vídeo cria uma tela preta; vídeo para áudio extrai o som. GIF não contém áudio.')

    def change_media_type(self, kind):
        formats = ['MP4', 'MKV', 'WEBM', 'MOV', 'GIF'] if kind == 'Vídeo' else ['MP3', 'M4A', 'OGG', 'OPUS', 'WAV', 'FLAC']
        self.media_format.configure(values=formats); self.media_format.set(formats[0])

    def choose_media(self):
        path = filedialog.askopenfilename(filetypes=[('Vídeo e áudio', '*.mp4 *.mkv *.webm *.mov *.avi *.mp3 *.m4a *.ogg *.opus *.wav *.flac *.aac *.wma *.mpeg *.mpg *.gif'), ('Todos os arquivos', '*.*')])
        if path:
            self.media_source.delete(0, 'end')
            self.media_source.insert(0, path)

    def convert_media(self):
        source = self.media_source.get().strip()
        exe = shutil.which('ffmpeg')
        if not exe:
            self.set_status('FFmpeg não encontrado. Instale-o e confira se está no PATH.'); return
        if not os.path.isfile(source):
            self.set_status('Escolha um arquivo de vídeo ou áudio existente.'); return
        fmt = self.media_format.get().lower()
        quality = self.media_quality.get()
        output = filedialog.asksaveasfilename(initialdir=str(Path(source).parent), initialfile=suggested_name(source, fmt), defaultextension='.' + fmt, filetypes=[(fmt.upper(), '*.' + fmt)])
        if not output: return
        if not output.lower().endswith('.' + fmt):
            self.set_status('O nome de saída deve terminar em .' + fmt); return
        if os.path.exists(output):
            self.set_status('Escolha um novo nome: a conversão não substitui arquivos existentes.'); return
        self.set_status('Conversão em andamento. Aguarde...')
        def task():
            probe = subprocess.run([exe, '-hide_banner', '-i', source], capture_output=True, text=True, errors='replace', creationflags=hidden_flags())
            info = probe.stderr
            audio_only = 'Audio:' in info and 'Video:' not in info
            if audio_only and fmt == 'gif': raise ValueError('GIF exige uma origem com imagem ou vídeo.')
            duration = self.parse_duration(info)
            self.run_process(media_command(exe, source, output, fmt, quality, audio_only=audio_only), duration=duration)
            return 'Conversão concluída: ' + output
        self.run_background(task, self.set_status)

    @staticmethod
    def parse_duration(info):
        match = re.search(r'Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)', info)
        if not match: return None
        h, m, sec = match.groups()
        duration = int(h)*3600 + int(m)*60 + float(sec)
        return duration if duration > 0 else None

    def compress_page(self):
        self.header('', 'Comprimir arquivo', '')
        card = self.card()
        self.label(card, 'Arquivo de origem')
        row = ctk.CTkFrame(card, fg_color='transparent'); row.pack(fill='x', padx=24)
        self.compress_source = ctk.CTkEntry(row, height=42, placeholder_text='Escolha um arquivo')
        self.compress_source.pack(side='left', fill='x', expand=True)
        ctk.CTkButton(row, text='Abrir', width=90, command=self.choose_compress).pack(side='left', padx=(8,0))
        ctk.CTkButton(row, text='Colar', width=75, command=lambda: self.paste_to_entry(self.compress_source)).pack(side='left', padx=(8,0))
        self.label(card, 'Tipo')
        self.compress_kind = ctk.CTkOptionMenu(card, values=['Arquivo ZIP', 'Imagem', 'Vídeo', 'Áudio'], command=self.compression_changed)
        self.compress_kind.pack(fill='x', padx=24)
        self.label(card, 'Qualidade')
        self.compress_quality = ctk.CTkOptionMenu(card, values=['Sem perda', 'Com perda'])
        self.compress_quality.pack(fill='x', padx=24); self.compress_quality.set('Sem perda'); self.compress_quality.configure(state='disabled')
        self.button(card, 'Comprimir', self.compress_file)
        self.status(card)
        ctk.CTkLabel(card, text='Para preservar o arquivo inteiro, use ZIP. Sem perda pode aumentar o tamanho.', text_color=MUTED).pack(anchor='w', padx=24)

    def choose_compress(self):
        path = filedialog.askopenfilename()
        if path: self.compress_source.delete(0, 'end'); self.compress_source.insert(0, path)

    def compression_changed(self, kind):
        if kind == 'Arquivo ZIP': self.compress_quality.set('Sem perda')
        self.compress_quality.configure(state='disabled' if kind == 'Arquivo ZIP' else 'normal')

    def compress_file(self):
        source = self.compress_source.get().strip()
        kind, lossy = self.compress_kind.get(), self.compress_quality.get() == 'Com perda'
        if not os.path.isfile(source): self.set_status('Escolha um arquivo existente.'); return
        fmt = {'Arquivo ZIP':'zip', 'Imagem':'jpg' if lossy else 'png', 'Vídeo':'mp4' if lossy else 'mkv', 'Áudio':'mp3' if lossy else 'flac'}[kind]
        exe = None if kind == 'Arquivo ZIP' else (shutil.which('magick') or (shutil.which('convert') if os.name != 'nt' else None) if kind == 'Imagem' else shutil.which('ffmpeg'))
        if kind != 'Arquivo ZIP' and not exe: self.set_status('Ferramenta necessária não encontrada.'); return
        output = filedialog.asksaveasfilename(initialdir=str(Path(source).parent), initialfile=Path(source).stem + '_comprimido.' + fmt, defaultextension='.'+fmt, filetypes=[(fmt.upper(), '*.'+fmt)])
        if not output: return
        if not output.lower().endswith('.'+fmt): self.set_status('Use a extensão .'+fmt); return
        if os.path.exists(output): self.set_status('Escolha um arquivo de destino novo.'); return
        def task():
            if kind == 'Arquivo ZIP':
                size = os.path.getsize(source); total = 0
                with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive, open(source, 'rb') as inp, archive.open(Path(source).name, 'w', force_zip64=True) as dest:
                    while True:
                        chunk = inp.read(1024*1024)
                        if not chunk: break
                        dest.write(chunk); total += len(chunk)
                        if size: self.report_progress(min(99, total / size * 100))
            elif kind == 'Imagem':
                with Image.open(source) as img:
                    if getattr(img, 'n_frames', 1) > 1:
                        raise ValueError('Para preservar imagens animadas ou com várias páginas, use ZIP.')
                cmd = [exe, source] + (['-quality','75'] if lossy else ['-define','png:compression-level=9']) + [output]
                self.run_process(cmd)
            else:
                probe = subprocess.run([exe, '-hide_banner', '-i', source], capture_output=True, text=True, errors='replace', creationflags=hidden_flags())
                self.run_process(compression_command(exe, source, output, kind, lossy), duration=self.parse_duration(probe.stderr))
            return 'Salvo em ' + output
        self.run_background(task, self.set_status)

    def image_source(self, card):
        self.label(card, 'IMAGEM LOCAL OU LINK')
        row = ctk.CTkFrame(card, fg_color='transparent'); row.pack(fill='x', padx=24)
        self.source = ctk.CTkEntry(row, placeholder_text='Cole um link ou escolha um arquivo', height=42, fg_color='#0f1722', border_color='#344255'); self.source.pack(side='left', fill='x', expand=True)
        if self.image_path: self.source.insert(0, self.image_path)
        ctk.CTkButton(row, text='Abrir arquivo', width=120, height=42, fg_color='#29384e', command=self.choose_image).pack(side='left', padx=(8, 0))
        tools_row = ctk.CTkFrame(card, fg_color='transparent'); tools_row.pack(anchor='w', padx=24, pady=(8, 0))
        ctk.CTkButton(tools_row, text='Colar imagem', width=120, height=32, fg_color='#29384e', command=self.paste_image).pack(side='left')
        ctk.CTkButton(tools_row, text='Copiar imagem', width=120, height=32, fg_color='#29384e', command=self.copy_current_image).pack(side='left', padx=(8, 0))

    def paste_to_entry(self, entry):
        try:
            from PIL import ImageGrab
            try: content = ImageGrab.grabclipboard()
            except Exception: content = None
            if isinstance(content, list) and content:
                value = str(content[0])
            else:
                value = self.clipboard_get().strip()
            if not value: raise ValueError('Área de transferência vazia.')
            entry.delete(0, 'end'); entry.insert(0, value)
        except Exception as exc:
            self.set_status('Não foi possível colar: ' + str(exc))

    def text_has_focus(self):
        widget = self.focus_get()
        return widget is not None and widget.winfo_class() in ('Entry', 'Text', 'TEntry', 'Spinbox')

    def paste_shortcut(self, event):
        if self.current_page in ('Editar imagem', 'Seletor de cores', 'Upscale IA') and not self.text_has_focus():
            self.paste_image()
            return 'break'

    def copy_shortcut(self, event):
        if self.current_page in ('Editar imagem', 'Seletor de cores', 'Upscale IA') and not self.text_has_focus():
            self.copy_current_image()
            return 'break'

    def paste_image(self):
        try:
            image = image_clipboard.read_image()
            path = os.path.join(self.temp.name, 'clipboard.png')
            image.save(path, 'PNG')
            self.image, self.image_path = image, path
            self.source.delete(0, 'end'); self.source.insert(0, path)
            self.set_status('Imagem colada')
            self.palette_colors = image_palette(image)
            if self.current_page == 'Seletor de cores':
                self.show('Seletor de cores'); self.set_status('Imagem colada')
        except Exception as exc:
            try:
                value = self.clipboard_get().strip()
                if urllib.parse.urlparse(value).scheme in ('http', 'https') or os.path.isfile(value):
                    self.source.delete(0, 'end'); self.source.insert(0, value)
                    if self.current_page == 'Seletor de cores': self.load_image()
                    else: self.set_status('Origem colada')
                    return
            except Exception:
                pass
            self.set_status('Não foi possível colar: ' + str(exc))

    def copy_current_image(self):
        source = self.source.get().strip()
        self.set_status('Preparando imagem para copiar...')
        def task():
            path = self.resolve_source(source)
            with Image.open(path) as img:
                img = ImageOps.exif_transpose(img).convert('RGBA')
                img.load()
            image_clipboard.copy_image(img)
            return 'Imagem copiada para a área de transferência.'
        self.run_background(task, self.set_status)

    def choose_image(self):
        path = filedialog.askopenfilename(filetypes=[('Imagens', '*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tif *.tiff'), ('Todos os arquivos', '*.*')])
        if path:
            self.source.delete(0, 'end'); self.source.insert(0, path)
            if self.current_page == 'Seletor de cores': self.load_image()

    def resolve_source(self, value):
        parsed = urllib.parse.urlparse(value)
        if parsed.scheme in ('http', 'https'):
            req = urllib.request.Request(value, headers={'User-Agent': 'LumaStudio/1.0'})
            target = os.path.join(self.temp.name, 'remote-image')
            with urllib.request.urlopen(req, timeout=30) as response, open(target, 'wb') as out:
                total = 0
                while True:
                    chunk = response.read(65536)
                    if not chunk: break
                    total += len(chunk)
                    if total > 50 * 1024 * 1024: raise ValueError('A imagem excede o limite de 50 MB.')
                    out.write(chunk)
            return target
        if not os.path.isfile(value): raise ValueError('Escolha um arquivo ou informe um link válido.')
        return value

    def edit_page(self):
        self.header('ImageMagick', 'Editar imagem', 'Converta e redimensione suas imagens em poucos passos.')
        card = self.card(); self.image_source(card)
        self.label(card, 'FORMATO DE SAÍDA')
        self.image_format = ctk.CTkOptionMenu(card, values=['PNG', 'JPEG', 'AVIF', 'WEBP', 'GIF', 'ICO', 'BMP', 'TIFF'], height=40, fg_color='#29384e')
        self.image_format.pack(fill='x', padx=24)
        self.label(card, 'REDIMENSIONAR · OPCIONAL')
        row = ctk.CTkFrame(card, fg_color='transparent'); row.pack(fill='x', padx=24)
        self.width = ctk.CTkEntry(row, placeholder_text='Largura em px', height=42, fg_color='#0f1722', border_color='#344255'); self.width.pack(side='left', fill='x', expand=True)
        self.height = ctk.CTkEntry(row, placeholder_text='Altura em px', height=42, fg_color='#0f1722', border_color='#344255'); self.height.pack(side='left', fill='x', expand=True, padx=(10, 0))
        self.button(card, 'Escolher destino e converter', self.convert)
        self.status(card, 'A disponibilidade de AVIF e outros formatos depende da instalação do ImageMagick.')

    def convert(self):
        source = self.source.get().strip()
        exe = shutil.which('magick') or (shutil.which('convert') if os.name != 'nt' else None)
        if not exe: self.set_status('ImageMagick não encontrado. Instale-o e confira se está no PATH.'); return
        try:
            w = int(self.width.get()) if self.width.get().strip() else None
            h = int(self.height.get()) if self.height.get().strip() else None
            if (w is not None and w <= 0) or (h is not None and h <= 0): raise ValueError()
        except ValueError: self.set_status('As dimensões devem ser números inteiros positivos.'); return
        fmt = self.image_format.get().lower()
        output = filedialog.asksaveasfilename(defaultextension='.' + fmt, filetypes=[(fmt.upper(), '*.' + fmt)])
        if not output: return
        if not output.lower().endswith('.' + fmt): self.set_status('Use a extensão .' + fmt); return
        self.set_status('Convertendo imagem...')
        def task():
            path = self.resolve_source(source)
            if os.path.abspath(path) == os.path.abspath(output): raise ValueError('Escolha um destino diferente da imagem original.')
            self.run_process(image_command(exe, path, output, w, h))
            return 'Imagem salva em ' + output
        self.run_background(task, self.set_status)

    def upscale_page(self):
        self.header('', 'Upscale com IA', '')
        card = self.card(); self.image_source(card)
        self.label(card, 'MODELO DE IA')
        self.up_model = ctk.CTkComboBox(card, values=[''], height=40)
        self.up_model.pack(fill='x', padx=24); self.up_model.set('')
        ctk.CTkLabel(card, text='Remacri, Ultramix e Ultrasharp: uso não comercial.', text_color=MUTED).pack(anchor='w', padx=24)
        row = ctk.CTkFrame(card, fg_color='transparent'); row.pack(fill='x', padx=24, pady=(12,0))
        left = ctk.CTkFrame(row, fg_color='transparent'); left.pack(side='left', fill='x', expand=True)
        right = ctk.CTkFrame(row, fg_color='transparent'); right.pack(side='left', fill='x', expand=True, padx=(12,0))
        ctk.CTkLabel(left, text='Escala', text_color=MUTED, anchor='w').pack(fill='x')
        self.up_scale = ctk.CTkOptionMenu(left, values=[f'{i}×' for i in range(2,17)], height=40)
        self.up_scale.pack(fill='x'); self.up_scale.set('4×')
        ctk.CTkLabel(right, text='Formato', text_color=MUTED, anchor='w').pack(fill='x')
        self.up_format = ctk.CTkOptionMenu(right, values=['PNG', 'WEBP', 'JPG'], height=40)
        self.up_format.pack(fill='x')
        self.up_double = ctk.BooleanVar(value=False)
        self.up_tta = ctk.BooleanVar(value=False)
        self.up_batch = ctk.BooleanVar(value=False)
        options = ctk.CTkFrame(card, fg_color='transparent'); options.pack(fill='x', padx=24, pady=(18,0))
        ctk.CTkCheckBox(options, text='Upscale duplo', variable=self.up_double).pack(side='left', padx=(0,20))
        ctk.CTkCheckBox(options, text='Modo detalhado', variable=self.up_tta).pack(side='left', padx=(0,20))
        ctk.CTkCheckBox(options, text='Lote', variable=self.up_batch).pack(side='left')
        ctk.CTkButton(card, text='Escolher pasta para lote', fg_color='#29384e', command=self.choose_upscale_input_folder).pack(anchor='w', padx=24, pady=(12,0))
        self.button(card, 'Ampliar imagem', self.run_upscale)
        ctk.CTkButton(card, text='Configurações do Upscayl  ▾', fg_color='transparent', hover_color='#25334a', anchor='w', command=self.toggle_up_settings).pack(fill='x', padx=24, pady=(0, 4))
        self.up_advanced = ctk.CTkFrame(card, fg_color='#101a28', corner_radius=10)
        tools = ctk.CTkFrame(self.up_advanced, fg_color='transparent'); tools.pack(anchor='w', padx=18, pady=(14,0))
        ctk.CTkButton(tools, text='Detectar Upscayl', width=140, command=self.detect_upscayl).pack(side='left')
        ctk.CTkButton(tools, text='Pasta do Upscayl', width=140, fg_color='#29384e', command=self.select_upscayl_folder).pack(side='left', padx=(8,0))
        self.label(self.up_advanced, 'EXECUTÁVEL')
        ex = ctk.CTkFrame(self.up_advanced, fg_color='transparent'); ex.pack(fill='x', padx=24)
        self.up_exe = ctk.CTkEntry(ex, height=38, placeholder_text='upscayl-bin'); self.up_exe.pack(side='left', fill='x', expand=True)
        ctk.CTkButton(ex, text='Escolher', width=90, command=lambda: self.choose_up_path(self.up_exe, False)).pack(side='left', padx=(8,0))
        self.label(self.up_advanced, 'PASTA DOS MODELOS')
        model = ctk.CTkFrame(self.up_advanced, fg_color='transparent'); model.pack(fill='x', padx=24)
        self.up_models = ctk.CTkEntry(model, height=38, placeholder_text='Modelos'); self.up_models.pack(side='left', fill='x', expand=True)
        ctk.CTkButton(model, text='Escolher', width=90, command=lambda: self.choose_up_path(self.up_models, True)).pack(side='left', padx=(8,0))
        self.label(self.up_advanced, 'GPU · OPCIONAL')
        self.up_gpu = self.entry(self.up_advanced, 'Automática')
        self.label(self.up_advanced, 'TAMANHO DE BLOCO · OPCIONAL')
        self.up_tile = self.entry(self.up_advanced, 'Automático')
        ctk.CTkFrame(self.up_advanced, height=10, fg_color='transparent').pack()
        self.status(card)
        if self.up_config:
            exe, models_dir, model_names, selected = self.up_config
            self.up_exe.insert(0, exe); self.up_models.insert(0, models_dir)
            self.up_model.configure(values=model_names); self.up_model.set(selected)
        else:
            self.detect_upscayl()

    def toggle_up_settings(self):
        if self.up_advanced.winfo_manager():
            self.up_advanced.pack_forget()
        else:
            self.up_advanced.pack(fill='x', padx=24, pady=(0,12), before=self.status_label)

    def detect_upscayl(self):
        candidates = []
        for base in (os.environ.get('LOCALAPPDATA'), os.environ.get('PROGRAMFILES'), '/opt', '/usr/lib', '/usr/local/lib'):
            if base:
                for name in ('Upscayl', 'upscayl', 'Programs/Upscayl'):
                    folder = Path(base) / name
                    if folder.is_dir(): candidates.append(folder)
        for folder in candidates:
            if self.configure_upscayl(folder): return
        self.set_status('Upscayl não encontrado. Escolha a pasta de instalação.')

    def select_upscayl_folder(self):
        folder = filedialog.askdirectory()
        if folder and not self.configure_upscayl(Path(folder)):
            self.set_status('Motor e modelos não encontrados nessa pasta.')

    def configure_upscayl(self, folder):
        binaries, model_dirs = [], []
        for root, dirs, files in os.walk(folder):
            depth = len(Path(root).relative_to(folder).parts)
            if depth >= 6: dirs[:] = []
            for name in files:
                if name.lower() in ('upscayl-bin.exe', 'upscayl-bin', 'upscayl-ncnn.exe', 'upscayl-ncnn'):
                    binaries.append(Path(root) / name)
            models = sorted(Path(name).stem for name in files if name.endswith('.param') and (Path(root) / (Path(name).stem + '.bin')).is_file())
            if models: model_dirs.append((Path(root), models))
        if not binaries or not model_dirs: return False
        models_dir, models = model_dirs[0]
        self.up_exe.delete(0, 'end'); self.up_exe.insert(0, str(binaries[0]))
        self.up_models.delete(0, 'end'); self.up_models.insert(0, str(models_dir))
        self.up_model.configure(values=models); self.up_model.set(models[0])
        self.up_config = (str(binaries[0]), str(models_dir), models, models[0])
        self.set_status('Upscayl pronto. Escolha uma imagem e um modelo.')
        return True

    def choose_up_path(self, entry, directory):
        path = filedialog.askdirectory() if directory else filedialog.askopenfilename()
        if path:
            entry.delete(0, 'end'); entry.insert(0, path)
            if directory:
                models = sorted(p.stem for p in Path(path).glob('*.param') if p.with_suffix('.bin').is_file())
                self.up_model.configure(values=models or ['']); self.up_model.set(models[0] if models else '')

    def choose_upscale_input_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.source.delete(0, 'end'); self.source.insert(0, folder); self.up_batch.set(True)

    def run_upscale(self):
        exe, models, model, source = self.up_exe.get().strip(), self.up_models.get().strip(), self.up_model.get().strip(), self.source.get().strip()
        if not os.path.isfile(exe) or not os.path.isdir(models) or not model:
            self.set_status('Informe o executável e o modelo do Upscayl.'); return
        if not all(os.path.isfile(os.path.join(models, model + ext)) for ext in ('.bin', '.param')):
            self.set_status('Modelo não encontrado.'); return
        scale, double, batch, tta = int(self.up_scale.get().rstrip('×')), self.up_double.get(), self.up_batch.get(), self.up_tta.get()
        fmt, gpu, tile = self.up_format.get().lower(), self.up_gpu.get().strip(), self.up_tile.get().strip()
        if (gpu and not gpu.isdigit()) or (tile and (not tile.isdigit() or int(tile) < 32)):
            self.set_status('GPU deve ser um número e o bloco deve ser pelo menos 32.'); return
        match = re.search(r'(?:^|[-_])([234])x(?:$|[-_])', model, re.I)
        native = int(match.group(1)) if match else 4
        passes, _ = upscale_plan(scale, native, double)
        self.up_config = (exe, models, list(self.up_model.cget('values')), model)
        if batch:
            folder = Path(source)
            if not folder.is_dir(): self.set_status('Escolha uma pasta de imagens.'); return
            sources = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp'))
            if not sources: self.set_status('Nenhuma imagem encontrada na pasta.'); return
            output_dir = filedialog.askdirectory(title='Pasta de saída')
            if not output_dir: return
            outputs = [Path(output_dir) / (p.stem + f'_{scale}x.' + fmt) for p in sources]
            if len({str(p).casefold() for p in outputs}) != len(outputs) or any(p.exists() for p in outputs):
                self.set_status('Há nomes de saída duplicados ou já existentes.'); return
        else:
            if not source: self.set_status('Escolha uma imagem.'); return
            sources = [source]
            name = Path(urllib.parse.urlparse(source).path).stem or 'imagem'
            output = filedialog.asksaveasfilename(initialfile=name + f'_{scale}x.' + fmt, defaultextension='.'+fmt, filetypes=[(fmt.upper(), '*.'+fmt)])
            if not output: return
            if not output.lower().endswith('.'+fmt): self.set_status('Use a extensão .'+fmt); return
            if os.path.exists(output): self.set_status('Escolha um nome que ainda não exista.'); return
            outputs = [Path(output)]
        def task():
            with tempfile.TemporaryDirectory(prefix='luma-upscale-') as scratch:
                for index, (item, dest) in enumerate(zip(sources, outputs)):
                    self.report_progress(None, f'Imagem {index+1}/{len(sources)}')
                    path = self.resolve_source(str(item))
                    with Image.open(path) as original:
                        original = ImageOps.exif_transpose(original)
                        size = (original.width * scale, original.height * scale)
                        current = str(Path(scratch) / 'input.png')
                        original.save(current, 'PNG')
                    for step, factor in enumerate(passes):
                        intermediate = str(Path(scratch) / f'pass-{index}-{step}.png')
                        cmd = [exe, '-i', current, '-o', intermediate, '-m', models, '-n', model, '-z', str(native), '-s', str(factor)]
                        if tta: cmd += ['-x']
                        if gpu: cmd += ['-g', gpu]
                        if tile: cmd += ['-t', tile]
                        self.run_process(cmd)
                        if not os.path.isfile(intermediate): raise RuntimeError('O Upscayl não produziu uma imagem.')
                        current = intermediate
                    with Image.open(current) as result:
                        if result.size != size: result = result.resize(size, Image.Resampling.LANCZOS)
                        if fmt == 'jpg': result = result.convert('RGB')
                        with open(dest, 'xb') as out: result.save(out, format={'png':'PNG','jpg':'JPEG','webp':'WEBP'}[fmt])
            return f'{len(outputs)} imagem(ns) salva(s).'
        self.run_background(task, self.set_status)

    def color_page(self):
        self.header('', 'Seletor de cores', '')
        card = self.card()
        if self.image is None:
            self.source = ctk.CTkEntry(card)
            self.color_empty = ctk.CTkFrame(card, fg_color='#101a28', corner_radius=14, border_width=1, border_color='#344255', height=300)
            self.color_empty.pack(fill='x', padx=20, pady=20)
            self.color_empty.pack_propagate(False)
            ctk.CTkLabel(self.color_empty, text='Abra ou cole uma imagem', font=ctk.CTkFont(size=20, weight='bold'), text_color='#f3f6ff').pack(pady=(58, 6))
            ctk.CTkLabel(self.color_empty, text='Ctrl + V para colar', text_color=MUTED).pack()
            actions = ctk.CTkFrame(self.color_empty, fg_color='transparent'); actions.pack(pady=24)
            ctk.CTkButton(actions, text='Escolher arquivo', width=150, height=42, fg_color=ACCENT, hover_color='#6686e3', text_color='#101725', font=ctk.CTkFont(weight='bold'), command=self.choose_image).pack(side='left', padx=4)
            ctk.CTkButton(actions, text='Colar', width=110, height=42, fg_color='#29384e', hover_color='#405675', command=self.paste_image).pack(side='left', padx=4)
            self.status(card)
            return
        top = ctk.CTkFrame(card, fg_color='transparent'); top.pack(fill='x', padx=12, pady=(12, 8))
        self.source = ctk.CTkEntry(top, placeholder_text='Link ou arquivo de imagem', height=40, fg_color='#0f1722', border_color='#344255')
        self.source.pack(side='left', fill='x', expand=True)
        if self.image_path: self.source.insert(0, self.image_path)
        self.source.bind('<Return>', lambda event: self.load_image())
        for text, action, width in [('Abrir', self.choose_image, 72), ('Carregar', self.load_image, 84), ('Colar', self.paste_image, 65), ('Copiar', self.copy_current_image, 70)]:
            ctk.CTkButton(top, text=text, width=width, height=40, fg_color='#29384e', hover_color='#405675', command=action).pack(side='left', padx=(6, 0))
        body = ctk.CTkFrame(card, fg_color='transparent'); body.pack(fill='x', padx=12, pady=(0, 8))
        body.grid_columnconfigure(0, weight=1)
        import tkinter as tk
        self.canvas = tk.Canvas(body, bg='#0c131d', highlightthickness=0, cursor='crosshair', height=max(300, self.winfo_height()-220))
        self.canvas.grid(row=0, column=0, sticky='nsew')
        details = ctk.CTkFrame(body, fg_color='#1d2a3b', corner_radius=10, width=190)
        details.grid(row=0, column=1, sticky='ns', padx=(10, 0)); details.grid_propagate(False)
        self.swatch = ctk.CTkFrame(details, fg_color='#53647d', height=76, corner_radius=8); self.swatch.pack(fill='x', padx=14, pady=(14, 8))
        self.color_result = ctk.CTkLabel(details, text='Selecione uma cor', text_color='#f0f3ff', font=ctk.CTkFont(size=13, weight='bold'), anchor='w')
        self.color_result.pack(fill='x', padx=14, pady=(0, 6))
        self.color_values = {}
        for label in ('HEX', 'RGB', 'HSL'):
            row = ctk.CTkFrame(details, fg_color='#101a28', corner_radius=7)
            row.pack(fill='x', padx=12, pady=3)
            ctk.CTkLabel(row, text=label, width=36, text_color=MUTED, font=ctk.CTkFont(size=11)).pack(side='left', padx=(5, 0))
            value = ctk.CTkButton(row, text='—', anchor='w', height=34, fg_color='transparent', hover_color='#30425a', font=ctk.CTkFont(size=11), command=lambda key=label: self.copy_color(self.color_values[key].cget('text')))
            value.pack(side='left', fill='x', expand=True)
            self.color_values[label] = value
        self.magnifier = ctk.CTkLabel(details, text='', width=88, height=88, text_color=MUTED); self.magnifier.pack(anchor='center', padx=14, pady=12)
        palette = ctk.CTkFrame(card, fg_color='transparent'); palette.pack(fill='x', padx=12, pady=(2, 8))
        ctk.CTkLabel(palette, text='Paleta da imagem', text_color=MUTED, anchor='w', font=ctk.CTkFont(size=12, weight='bold')).pack(anchor='w')
        self.palette_frame = ctk.CTkFrame(palette, fg_color='transparent'); self.palette_frame.pack(fill='x')
        ctk.CTkLabel(palette, text='Histórico', text_color=MUTED, anchor='w', font=ctk.CTkFont(size=12, weight='bold')).pack(anchor='w', pady=(8, 0))
        self.history_frame = ctk.CTkFrame(palette, fg_color='transparent'); self.history_frame.pack(fill='x')
        self.render_colors(self.palette_frame, self.palette_colors)
        self.render_colors(self.history_frame, self.color_history)
        self.status(card)
        self.canvas.bind('<Button-1>', self.pick_color)
        self.canvas.bind('<B1-Motion>', self.pick_color)
        self.canvas.bind('<Motion>', self.color_hover)
        self.canvas.bind('<Configure>', lambda event: self.draw_image())
        if self.image: self.after(100, self.draw_image)

    def load_image(self):
        source = self.source.get().strip(); self.set_status('Carregando imagem...')
        def task():
            path = self.resolve_source(source)
            with Image.open(path) as img:
                img = ImageOps.exif_transpose(img).convert('RGBA')
                img.load()
                return img
        def done(img):
            self.image = img; self.image_path = source
            self.palette_colors = image_palette(img)
            if self.current_page == 'Seletor de cores':
                self.show('Seletor de cores')
                self.set_status(f'{img.width} × {img.height} px')
                self.draw_image()
        self.run_background(task, done)

    def draw_image(self):
        if not self.image or not hasattr(self, 'canvas') or not self.canvas.winfo_exists(): return
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if cw < 2 or ch < 2: return
        scale = min(cw/self.image.width, ch/self.image.height)
        preview = self.image.resize((max(1, round(self.image.width*scale)), max(1, round(self.image.height*scale))), Image.Resampling.LANCZOS)
        self.preview_size = preview.size
        self.offset = ((cw-preview.width)//2, (ch-preview.height)//2)
        self.preview_photo = ImageTk.PhotoImage(preview)
        self.canvas.delete('all'); self.canvas.create_image(*self.offset, image=self.preview_photo, anchor='nw')

    def image_position(self, event):
        if not self.image or not hasattr(self, 'offset'): return None
        x, y = event.x-self.offset[0], event.y-self.offset[1]
        w, h = self.preview_size
        if not (0 <= x < w and 0 <= y < h): return None
        return (min(self.image.width-1, int(x*self.image.width/w)), min(self.image.height-1, int(y*self.image.height/h)))

    def color_hover(self, event):
        pos = self.image_position(event)
        if pos is None: return
        crop = magnified_pixel(self.image, pos)
        self.canvas.delete('pixel-marker')
        self.canvas.create_oval(event.x-6, event.y-6, event.x+6, event.y+6, outline='white', width=2, tags='pixel-marker')
        self.magnifier_photo = ctk.CTkImage(light_image=crop, dark_image=crop, size=(88, 88))
        self.magnifier.configure(image=self.magnifier_photo, text='')

    def copy_color(self, value):
        self.clipboard_clear(); self.clipboard_append(value)
        self.set_status(value + ' copiado.')

    def pick_color(self, event):
        pos = self.image_position(event)
        if pos is None: return
        pixel = self.image.getpixel(pos)
        hex_value = pixel_hex(pixel)
        h, l, sat = colorsys.rgb_to_hls(*(c/255 for c in pixel[:3]))
        self.swatch.configure(fg_color=hex_value)
        self.color_result.configure(text=hex_value)
        self.color_values['HEX'].configure(text=hex_value)
        self.color_values['RGB'].configure(text=f'{pixel[0]}, {pixel[1]}, {pixel[2]}')
        self.color_values['HSL'].configure(text=f'{round(h*360)}°, {round(sat*100)}%, {round(l*100)}%')
        if not self.color_history or self.color_history[0] != hex_value:
            self.color_history = [hex_value] + [c for c in self.color_history if c != hex_value][:7]
            self.render_colors(self.history_frame, self.color_history)

    def render_colors(self, frame, colors):
        for child in frame.winfo_children(): child.destroy()
        for column in range(4): frame.grid_columnconfigure(column, weight=1, uniform='colors')
        for index, color in enumerate(colors):
            text_color = swatch_text_color(color)
            ctk.CTkButton(frame, text=color, width=72, height=42, fg_color=color, hover_color=color,
                          text_color=text_color, font=ctk.CTkFont(size=10),
                          command=lambda c=color: self.copy_color(c)).grid(row=index//4, column=index%4, sticky='ew', padx=(0, 4), pady=(0, 4))

if __name__ == '__main__':
    App().mainloop()
