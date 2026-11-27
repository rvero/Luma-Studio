import os
import re
from pathlib import Path


def progress_from_line(line):
    match = re.search(r'\[download\]\s+([\d.]+)%', line)
    return min(100.0, float(match.group(1))) if match else None


def suggested_name(source, extension):
    path = Path(source)
    suffix = '_convertido' if path.suffix.lower() == '.' + extension.lower() else ''
    return path.stem + suffix + '.' + extension


def compression_command(executable, source, output, kind, lossy):
    cmd = [executable, '-hide_banner', '-nostdin', '-n', '-i', source]
    if kind == 'Vídeo':
        cmd += ['-map', '0:v:0', '-map', '0:a:0?']
        cmd += ['-c:v', 'libx264', '-crf', '30', '-c:a', 'aac'] if lossy else ['-c:v', 'ffv1', '-c:a', 'copy']
    elif kind == 'Áudio':
        cmd += ['-vn', '-c:a', 'libmp3lame' if lossy else 'flac']
        if lossy: cmd += ['-b:a', '128k']
    else:
        raise ValueError('Tipo de mídia inválido.')
    return cmd + [output]


def hidden_flags():
    return 0x08000000 if os.name == 'nt' else 0


def upscale_plan(scale, native_scale, double):
    if scale not in range(2, 17) or native_scale not in (2, 3, 4):
        raise ValueError('Escala inválida.')
    passes = []
    factor = 1
    while factor < scale or (double and len(passes) < 2):
        passes.append(native_scale)
        factor *= native_scale
    return passes, scale
