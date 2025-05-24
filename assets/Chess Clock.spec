# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules

a = Analysis(
    ['__init__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('iconset.atlas', 'assets/'),
        ('iconset.png', 'assets/'),
        ('icon.ico', 'assets/'),
        ('settings.json', 'assets/'),
        ('main.kv', 'assets/'),
        ('tick.wav', 'assets/')
    ],
    hiddenimports=[
        'kivy',
        'kivy.app',
        'kivy.lang',
        'kivy.clock',
        'kivy.config',
        'kivy.core.window',
        'kivy.logger',
        'kivy.metrics',
        'kivy.properties',
        'kivy.uix.behaviors',
        'kivy.uix.boxlayout',
        'kivy.uix.button',
        'kivy.uix.dropdown',
        'kivy.uix.floatlayout',
        'kivy.uix.image',
        'kivy.uix.popup',
        'kivy.uix.settings',
        'kivy.uix.togglebutton',
        'kivy.uix.widget',
        'pydub.AudioSegment',
        'pydub.playback',
        'os',
        'threading'
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Chess Clock',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Chess Clock',
)
