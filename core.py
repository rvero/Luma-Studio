from pathlib import Path


def image_command(executable, source, output, width=None, height=None, quality=90):
    cmd = [executable, str(source)]
    if width or height:
        cmd += ['-resize', f'{width or ""}x{height or ""}']
    return cmd + ['-quality', str(quality), str(output)]


def download_command(executable, url, destination, audio=False, browser=None, format_name=None):
    cmd = [executable, '--newline', '--no-playlist', '-P', str(destination)]
    if browser:
        cmd += ['--cookies-from-browser', browser]
    if audio or format_name in ('mp3', 'm4a', 'opus', 'wav', 'flac', 'vorbis'):
        cmd += ['--extract-audio', '--audio-format', format_name or 'mp3']
    elif format_name in ('mp4', 'mkv', 'webm', 'mov'):
        cmd += ['--recode-video', format_name]
    elif format_name not in (None, 'original'):
        raise ValueError('Formato de download desconhecido.')
    return cmd + ['--', url]


def pixel_hex(pixel):
    return '#{:02X}{:02X}{:02X}'.format(*pixel[:3])


def media_command(executable, source, output, format_name, quality, audio_only=False):
    video_formats = {
        'mp4': ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-movflags', '+faststart'],
        'mkv': ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac'],
        'webm': ['-c:v', 'libvpx-vp9', '-c:a', 'libopus'],
        'mov': ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac'],
    }
    audio_formats = {
        'mp3': ['-c:a', 'libmp3lame'], 'm4a': ['-c:a', 'aac'],
        'ogg': ['-c:a', 'libvorbis'], 'opus': ['-c:a', 'libopus'],
        'wav': ['-c:a', 'pcm_s16le'], 'flac': ['-c:a', 'flac'],
    }
    if quality not in ('Alta', 'Equilibrada', 'Menor arquivo'):
        raise ValueError('Qualidade desconhecida.')
    cmd = [executable, '-hide_banner', '-nostdin', '-n', '-i', str(source)]
    if audio_only and format_name in video_formats:
        cmd += ['-f', 'lavfi', '-i', 'color=c=black:s=1280x720:r=25', '-map', '1:v:0', '-map', '0:a:0', '-shortest']
    if format_name == 'gif':
        cmd += ['-an', '-vf', 'fps=15,scale=800:-2:flags=lanczos', '-f', 'gif']
    elif format_name in video_formats:
        crf = {'Alta': '18', 'Equilibrada': '23', 'Menor arquivo': '30'}[quality]
        cmd += video_formats[format_name] + ['-crf', crf]
        if format_name == 'webm': cmd += ['-b:v', '0']
    elif format_name in audio_formats:
        cmd += ['-vn'] + audio_formats[format_name]
        if format_name in ('mp3', 'm4a', 'ogg', 'opus'):
            cmd += ['-b:a', {'Alta': '256k', 'Equilibrada': '192k', 'Menor arquivo': '128k'}[quality]]
    else:
        raise ValueError('Formato desconhecido.')
    return cmd + [str(output)]
