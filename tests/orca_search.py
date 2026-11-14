"""Check actual Orca utterances on the fictional portfolio, using desktop key events."""

import os
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


log = Path(os.environ['ORCA_LOG'])


def cursor():
    return log.stat().st_size if log.exists() else 0


def heard(offset, phrase):
    deadline = time.monotonic() + 18
    spoken = []
    while time.monotonic() < deadline:
        if log.exists():
            with log.open('rb') as stream:
                stream.seek(offset)
                lines = stream.read().decode(errors='replace').splitlines()
            spoken = [s.split('SPEECH OUTPUT:', 1)[1].strip() for s in lines
                      if 'SPEECH OUTPUT:' in s]
            if phrase.casefold() in ' '.join(spoken).casefold():
                print(f'Orca announced {phrase!r}', flush=True)
                return
        time.sleep(0.2)
    raise AssertionError(f'Expected {phrase!r} in Orca speech. Heard {spoken[-20:]!r}')


def keys(*names):
    subprocess.run(['xdotool', 'key', '--clearmodifiers', *names], check=True)


def check():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False, args=['--force-renderer-accessibility'])
        print(f'Chromium {browser.version}', flush=True)
        page = browser.new_page()
        page.goto('http://127.0.0.1:3000')
        search = page.get_by_role('textbox', name='Search facilities')
        expect(search).to_be_visible(timeout=30000)
        explorer = page.locator('#exposures')
        status = explorer.get_by_role('status').filter(has_text='Showing')
        expect(status).to_contain_text('Showing 40 of 40')
        page.bring_to_front()
        page.get_by_role('link', name='Skip to dashboard').focus()
        start = cursor()
        for _ in range(40):
            keys('Tab')
            if search.evaluate('(element) => element === document.activeElement'):
                break
        expect(search).to_be_focused()
        heard(start, 'Search facilities')
        heard(start, 'Focus mode')

        start = cursor()
        subprocess.run(['xdotool', 'type', '--clearmodifiers', '--delay', '75', 'SYN-001'], check=True)
        expect(search).to_have_value('SYN-001')
        expect(status).to_contain_text('Showing 1 of 40 facilities')
        heard(start, 'Showing 1 of 40 facilities')

        choice = explorer.get_by_role('combobox', name='Inspect a facility')
        for _ in range(8):
            if choice.evaluate('(element) => element === document.activeElement'):
                break
            keys('Tab')
        expect(choice).to_be_focused()
        keys('Down', 'Return')
        expect(explorer.get_by_role('heading', name='SYN-001', exact=False)).to_be_visible()
        for _ in range(8):
            if search.evaluate('(element) => element === document.activeElement'):
                break
            keys('shift+Tab')
        expect(search).to_be_focused()
        start = cursor()
        keys('ctrl+a', 'BackSpace')
        expect(status).to_contain_text('Showing 40 of 40 facilities')
        heard(start, 'Showing 40 of 40 facilities')
        expect(search).to_be_focused()
        print('Opened SYN-001 using the keyboard. After clearing, focus stayed on Search facilities.')
        browser.close()


if __name__ == '__main__':
    try:
        check()
    except Exception:
        if log.exists():
            output = [line for line in log.read_text(errors='replace').splitlines()
                      if 'SPEECH OUTPUT:' in line]
            print('Recent synthetic-session speech:', *output[-25:], sep='\n', file=sys.stderr)
        raise
