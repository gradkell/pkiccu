# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['../src/scripts/run_dbsign_crl_updater.py'],
             pathex=['.'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='run_dbsign_crl_updater',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,  # strip=False makes it work on Windows.  Dunno why.
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
