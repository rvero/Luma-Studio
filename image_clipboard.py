"""Image clipboard support for Windows, X11 and Wayland."""
import io
import os
import shutil
import subprocess
import sys

from PIL import Image, ImageGrab


def read_image():
    result = ImageGrab.grabclipboard()
    if isinstance(result, Image.Image):
        return result.convert('RGBA')
    if isinstance(result, list):
        for path in result:
            try:
                with Image.open(path) as image:
                    return image.convert('RGBA')
            except (OSError, ValueError):
                continue
    raise ValueError('A área de transferência não contém uma imagem ou arquivo de imagem.')


def copy_image(image):
    if sys.platform == 'win32':
        _copy_windows(image)
        return
    data = io.BytesIO()
    image.save(data, format='PNG')
    if os.environ.get('WAYLAND_DISPLAY') and shutil.which('wl-copy'):
        command = ['wl-copy', '--type', 'image/png']
    elif shutil.which('xclip'):
        command = ['xclip', '-selection', 'clipboard', '-t', 'image/png', '-i']
    else:
        raise RuntimeError('Instale wl-clipboard (Wayland) ou xclip (X11) para copiar imagens.')
    subprocess.run(command, input=data.getvalue(), check=True, timeout=15)


def _copy_windows(image):
    import ctypes
    from ctypes import wintypes
    user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    buffer = io.BytesIO()
    image.convert('RGB').save(buffer, 'BMP')
    dib = buffer.getvalue()[14:]
    handle = kernel32.GlobalAlloc(0x0002, len(dib))
    if not handle: raise OSError('Não foi possível reservar memória para a imagem.')
    transferred = False
    try:
        ptr = kernel32.GlobalLock(handle)
        if not ptr: raise OSError('Não foi possível acessar a memória da imagem.')
        ctypes.memmove(ptr, dib, len(dib))
        kernel32.GlobalUnlock(handle)
        if not user32.OpenClipboard(None): raise OSError('Não foi possível abrir a área de transferência.')
        try:
            if not user32.EmptyClipboard(): raise OSError('Não foi possível limpar a área de transferência.')
            if not user32.SetClipboardData(8, handle): raise OSError('Não foi possível copiar a imagem.')
            transferred = True
        finally:
            user32.CloseClipboard()
    finally:
        if not transferred: kernel32.GlobalFree(handle)
