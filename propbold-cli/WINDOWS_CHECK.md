# Re-verify propbold 0.2.0 on Windows 11 (PowerShell)

    py -3.12 -m venv "$env:USERPROFILE\pb"; & "$env:USERPROFILE\pb\Scripts\Activate.ps1"
    pip install "git+https://github.com/fanzhixiang777/ProportionalBold.git#subdirectory=propbold-cli" opentype-sanitizer
    propbold --help                                                    # shows --ratio, default 1.45
    curl.exe -L -o NotoSansCJKtc-Regular.otf https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/TraditionalChinese/NotoSansCJKtc-Regular.otf
    propbold .\NotoSansCJKtc-Regular.otf --ratio 1.45                  # expect: 65535 glyphs (… measured, … with fallback stem, 0 failed); 541 s on 2026-09-20 (mac/results/windows-0.2.0.md)
    python -m ots .\NotoSansCJKtc-Regular-propbold145.ttf              # expect: File sanitized successfully!
    Start-Process .\NotoSansCJKtc-Regular-propbold145.ttf              # font viewer opens: family "Noto Sans CJK TC PropBold145" → click Install
    Get-ItemProperty 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts' | Select-String PropBold   # registered for this user
    # Word → font list contains "Noto Sans CJK TC PropBold145"; type 臺灣鬱鑿籲龜體 — renders bold at 12 pt and 72 pt
    # record the propbold summary line, the ots line and "installs: yes/no" in mac/results/windows-0.2.0.md
