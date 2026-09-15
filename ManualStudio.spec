# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['manual_capture_studio.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('fonts', 'fonts'), ('config.json', '.'), ('version.json', '.'), ('AGENTS.md', '.'), ('RELEASE_NOTES.md', '.'), ('각 기능(키)설명.MD', '.')],
    hiddenimports=['i18n_manager', 'manual_cli', 'mcp_server', 'license_engine', 'updater_engine', 'markitdown', 'markdownify', 'magika', 'beautifulsoup4', 'soupsieve', 'docx', 'lxml'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch', 'torchvision', 'torchaudio', 'torchsde', 'torch_complex',
        'nvidia', 'cuda', 'cudnn', 'cublas',
        'numba', 'bitsandbytes', 'scipy', 'pandas', 'matplotlib', 'pyarrow',
        'transformers', 'tokenizers', 'sentencepiece', 'safetensors', 'peft', 'trl', 'modelscope', 'TTS',
        'spacy', 'nltk', 'scikit_learn', 'sklearn',
        'yt_dlp', 'cv2', 'IPython', 'jupyter', 'zmq', 'tensorboard', 'tensorboardX',
        'soundfile', 'pydub', 'sox', 'soxr', 'SoundCard', 'qwen_tts',
        'pykakasi', 'pypinyin', 'sudachipy', 'unidic', 'unidic_lite',
        'weasel', 'srsly', 'thinc', 'preshed', 'cymem', 'blis', 'murmurhash',
        'resampy', 'umap', 'nuitka', 'pytest', 'unittest'
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ManualStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/manual_studio.ico'],
)
