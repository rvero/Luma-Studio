"""Find installed browsers that yt-dlp supports for cookie extraction."""
import os
import shutil
import sys
from pathlib import Path

BROWSERS = {
    'Brave': (('brave', 'brave-browser'), 'BraveSoftware/Brave-Browser/Application/brave.exe', ('brave-browser.desktop',)),
    'Chrome': (('google-chrome', 'google-chrome-stable', 'chrome'), 'Google/Chrome/Application/chrome.exe', ('google-chrome.desktop',)),
    'Chromium': (('chromium', 'chromium-browser'), 'Chromium/Application/chrome.exe', ('chromium.desktop', 'org.chromium.Chromium.desktop')),
    'Edge': (('microsoft-edge', 'microsoft-edge-stable', 'msedge'), 'Microsoft/Edge/Application/msedge.exe', ('microsoft-edge.desktop',)),
    'Firefox': (('firefox',), 'Mozilla Firefox/firefox.exe', ('firefox.desktop', 'org.mozilla.firefox.desktop')),
    'Opera': (('opera',), 'Opera/launcher.exe', ('opera.desktop',)),
    'Vivaldi': (('vivaldi', 'vivaldi-stable'), 'Vivaldi/Application/vivaldi.exe', ('vivaldi-stable.desktop',)),
    'Whale': (('whale',), 'Naver/Naver Whale/Application/whale.exe', ('naver-whale.desktop',)),
}


def detect_browsers(platform=None, which=None, exists=None, environ=None):
    platform = platform or sys.platform
    which = which or shutil.which
    exists = exists or os.path.isfile
    env = os.environ if environ is None else environ
    found = []
    for label, (commands, windows_path, desktop_files) in BROWSERS.items():
        installed = any(which(cmd) for cmd in commands)
        if platform.startswith('win') and not installed:
            roots = [env.get('PROGRAMFILES'), env.get('PROGRAMFILES(X86)'), env.get('LOCALAPPDATA')]
            installed = any(exists(Path(root) / windows_path) for root in roots if root)
        elif platform.startswith('linux') and not installed:
            roots = ['/usr/share/applications', '/usr/local/share/applications', '/var/lib/flatpak/exports/share/applications']
            if env.get('HOME'):
                roots += [str(Path(env['HOME']) / '.local/share/applications'), str(Path(env['HOME']) / '.local/share/flatpak/exports/share/applications')]
            installed = any(exists(Path(root) / desktop) for root in roots for desktop in desktop_files)
        if installed: found.append(label)
    return found
