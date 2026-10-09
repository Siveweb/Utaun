# パソコンが使えないため一時的にこのpyファイルなどを置かせてください！
# 発案者が規約違反をしてごめんなさい！
# 【Sive】らららより！​
import re

with open("utaun.py", "r", encoding="utf-8") as f:
    code = f.read()

# Windows用のバッチファイル生成部分を、Mac/Linux用のシェルスクリプト生成に安全に置き換える
old_target = """    batch_file = os.path.join(current_dir, 'update.bat')

    batch_content = f\"\"\"
@echo off
timeout /t 2 /nobreak > nul
set "DEST_DOC=%USERPROFILE%\\\\Documents\"
if exist "%USERPROFILE%\\\\OneDrive\\\\Documents\" (
    set "DEST_DOC=%USERPROFILE%\\\\OneDrive\\\\Documents\"
) else if exist "%USERPROFILE%\\\\OneDrive\\\\ドキュメント\" (
    set "DEST_DOC=%USERPROFILE%\\\\OneDrive\\\\ドキュメント\"
)

if exist "%DEST_DOC%\\\\子音部・濁音部フォルダ\" (
    rmdir /s /q "%DEST_DOC%\\\\子音部・濁音部フォルダ\"
)
if exist "{source_content_dir}\\\\子音部・濁音部フォルダ\" (
    mkdir "%DEST_DOC%\\\\子音部・濁音部フォルダ\"
    xcopy /s /y /e "{source_content_dir}\\\\子音部・濁音部フォルダ\\\\*" "%DEST_DOC%\\\\子音部・濁音部フォルダ\\\\\\\\"
)

if exist "%DEST_DOC%\\\\oto.ini\" (
    del /q "%DEST_DOC%\\\\oto.ini\"
)
if exist "{source_content_dir}\\\\oto.ini\" (
    copy /y "{source_content_dir}\\\\oto.ini\" "%DEST_DOC%\\\\oto.ini\"
)

cd /d "{current_dir}\"

set "NEW_EXE=\"
for %%f in ("{source_content_dir}\\\\*utaun*.exe\" "{source_content_dir}\\\\*Utaun*.exe\") do (
    if exist "%%f\" (
        copy /y "%%f\" "{current_dir}\\\\"
        set "NEW_EXE={current_dir}\\\\%%~nxf\"
    )
)

for %%f in (*utaun*.exe *Utaun*.exe) do (
    if /i not "%%~ff"=="%NEW_EXE%\" (
        del /q "%%f\"
    )
)

if not "%NEW_EXE%"=="" (
    set "PYINSTALLER_RESET_ENVIRONMENT=1"
    start "" "%NEW_EXE%"
)

rmdir /s /q "{temp_dir}\"
del "%~f0\"
\"\"\"
    with open(batch_file, 'w', encoding='shift_jis') as f:
      f.write(batch_content)

    subprocess.Popen(batch_file, shell=True)
    sys.exit(0)"""

new_replacement = """    sh_file = os.path.join(current_dir, 'update.sh')
    sh_content = f\"\"\"#!/bin/bash
sleep 2
DEST_DOC="$HOME/Documents"
rm -rf "$DEST_DOC/子音部・濁音部フォルダ"
if [ -d "{source_content_dir}/子音部・濁音部フォルダ" ]; then
    mkdir -p "$DEST_DOC/子音部・濁音部フォルダ"
    cp -r "{source_content_dir}/子音部・濁音部フォルダ/"* "$DEST_DOC/子音部・濁音部フォルダ/"
fi
rm -f "$DEST_DOC/oto.ini"
if [ -f "{source_content_dir}/oto.ini" ]; then
    cp "{source_content_dir}/oto.ini" "$DEST_DOC/oto.ini"
fi

cd "{current_dir}"
NEW_APP=\\$(find "{source_content_dir}" -maxdepth 1 -name "*utaun*" -o -name "*Utaun*" | head -n 1)
if [ ! -z "$NEW_APP" ]; then
    cp "$NEW_APP" "{current_dir}/"
    find . -maxdepth 1 -name "*utaun*" -o -name "*Utaun*" ! -name "$(basename "$NEW_APP")" -delete
    chmod +x "$(basename "$NEW_APP")"
    
    if [ "$(uname)" = "Darwin" ]; then
        open "$(basename "$NEW_APP")" &
    else
        xdg-open "$(basename "$NEW_APP")" &
    fi
fi
rm -rf "{temp_dir}"
\"\"\"
    with open(sh_file, 'w', encoding='utf-8') as f:
      f.write(sh_content)
    os.chmod(sh_file, 0o755)
    subprocess.Popen(['/bin/bash', sh_file])
    sys.exit(0)"""

if old_target in code:
    code = code.replace(old_target, new_replacement)
    with open("utaun.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("Successfully patched update logic!")
else:
    print("Warning: Target pattern not found, trying regex fallback...")
    # 見つからない場合のフォールバック（関数全体をごっそり置き換え）
    old_func_pattern = r'def perform_update\(download_url\):.*?(?=\ndef [a-zA-Z_]|\Z)'
    if re.search(old_func_pattern, code, re.DOTALL):
        code = re.sub(old_func_pattern, new_replacement.strip(), code, flags=re.DOTALL)
        with open("utaun.py", "w", encoding="utf-8") as f:
            f.write(code)
        print("Patched via regex fallback successfully!")
    else:
        raise Exception("Could not find perform_update function to patch.")
