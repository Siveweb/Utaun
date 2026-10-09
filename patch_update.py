# パソコンが使えないため一時的にこのpyファイルなどを置かせてください！
# 発案者が規約違反をしてごめんなさい！
# 【Sive】らららより！
import re

with open("utaun.py", "r", encoding="utf-8") as f:
    code = f.read()

old_update_func = r'def perform_update\(download_url\):.*?^(?=\s*def |\s*class )'

new_update_func = """def perform_update(download_url):
  try:
    if getattr(sys, 'frozen', False):
      current_exe = sys.executable
      current_dir = os.path.dirname(current_exe)
    else:
      messagebox.showwarning('注意', '開発環境のためシミュレーションのみ行います。')
      return

    temp_dir = tempfile.mkdtemp(prefix='utaun_update_')
    zip_path = os.path.join(temp_dir, 'update.zip')
    extract_dir = os.path.join(temp_dir, 'extracted')

    messagebox.showinfo('ダウンロード中', 'アップデートファイルをダウンロードしています...')
    urllib.request.urlretrieve(download_url, zip_path)

    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
      zip_ref.extractall(extract_dir)

    extracted_items = os.listdir(extract_dir)
    if len(extracted_items) == 1 and os.path.isdir(os.path.join(extract_dir, extracted_items[0])):
      source_content_dir = os.path.join(extract_dir, extracted_items[0])
    else:
      source_content_dir = extract_dir

    sh_file = os.path.join(current_dir, 'update.sh')
    sh_content = f'''#!/bin/bash
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
NEW_APP=$(find "{source_content_dir}" -maxdepth 1 -name "*utaun*" -o -name "*Utaun*" | head -n 1)
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
'''
    with open(sh_file, 'w', encoding='utf-8') as f:
      f.write(sh_content)
    os.chmod(sh_file, 0o755)
    subprocess.Popen(['/bin/bash', sh_file])
    sys.exit(0)

  except Exception as e:
    messagebox.showerror('アップデートエラー', f'アップデートの適用中にエラーが発生しました:\\n{e}')
"""

code_patched = re.sub(old_update_func, new_update_func, code, flags=re.DOTALL | re.MULTILINE)
with open("utaun.py", "w", encoding="utf-8") as f:
    f.write(code_patched)
