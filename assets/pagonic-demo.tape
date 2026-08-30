# Pagonic README demo: inspect before you extract.
# Regenerate with VHS from the repository root:
#   vhs assets/pagonic-demo.tape

Output assets/pagonic-demo.gif
Require python

Set Shell "pwsh"
Set FontFamily "Cascadia Mono"
Set FontSize 18
Set Width 1180
Set Height 620
Set Padding 24
Set Margin 12
Set MarginFill "#0f172a"
Set BorderRadius 10
Set WindowBar "Colorful"
Set WindowBarSize 36
Set Theme "Catppuccin Mocha"
Set Framerate 16
Set PlaybackSpeed 0.8
Set TypingSpeed 85ms
Set CursorBlink false

Hide
Type "function pagonic { python -m Pagonic.cli.main @args }" Enter
Type "$env:PAGONIC_DEMO_ROOT = (Get-Location).Path" Enter
Type "$env:PAGONIC_DEMO_DIR = Join-Path ([System.IO.Path]::GetTempPath()) ('pagonic-demo-' + [guid]::NewGuid().ToString('N'))" Enter
Type "New-Item -ItemType Directory -Path $env:PAGONIC_DEMO_DIR | Out-Null" Enter
Type "$env:PYTHONPATH = $env:PAGONIC_DEMO_ROOT" Enter
Type "Set-Location -LiteralPath $env:PAGONIC_DEMO_DIR" Enter
Type `python -c "import zipfile; z=zipfile.ZipFile('pagonic-demo.zip','w',zipfile.ZIP_DEFLATED); z.writestr('../payload.exe','demo payload'); z.writestr('docs/readme.txt','review me'); z.close()"` Enter
Type "Clear-Host" Enter
Sleep 800ms
Show

Sleep 1200ms
Type "pagonic --version" Enter
Sleep 1500ms
Type "pagonic inspect pagonic-demo.zip" Enter
Sleep 3s
Type "pagonic verify pagonic-demo.zip" Enter
Sleep 2200ms
Type "pagonic safe-extract pagonic-demo.zip extracted" Enter
Sleep 3s

Hide
Type "Set-Location -LiteralPath $env:PAGONIC_DEMO_ROOT" Enter
Type "Remove-Item -LiteralPath $env:PAGONIC_DEMO_DIR -Recurse -Force" Enter
Sleep 300ms
Show
Sleep 500ms
