# パソコンが使えないため一時的にこのpyファイルなどを置かせてください！
# 発案者が規約違反をしてごめんなさい！
# 【Sive】らららより！
import re

with open("utaun.py", "r", encoding="utf-8") as f:
    code = f.read()

# Documentsパスを取得する関数だけを安全にMac/Linux用に置換
old_get_doc = r'def get_documents_path\(\):\s+.*?return os\.path\.join\(home, [\'"]Documents[\'"]\)'
new_get_doc = """def get_documents_path():
  home = os.path.expanduser('~')
  path = os.path.join(home, 'Documents')
  if not os.path.exists(path):
    os.makedirs(path, exist_ok=True)
  return path"""

code = re.sub(old_get_doc, new_get_doc, code, flags=re.DOTALL)

with open("utaun.py", "w", encoding="utf-8") as f:
    f.write(code)
