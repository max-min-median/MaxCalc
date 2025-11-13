import webbrowser
import sys
import os

def display():
    url = 'https://github.com/max-min-median/Calculator/blob/main/README.md'
    if 'termux' in sys.prefix.lower() or 'com.termux' in sys.executable.lower():
        os.system(f"termux-open-url {url}")
    else:
        webbrowser.open(url)