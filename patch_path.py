# パソコンが使えないため一時的にこのymlファイルなどを置かせてください！
# 発案者が規約違反をしてごめんなさい！
# 【Sive】らららより！
import re

with open("utaun.py", "r", encoding="utf-8") as f:
    code = f.read()

old_get_doc = r'def get_documents_path\(\):\s+.*?return os\.path\.join\(home, [\'"]Documents[\'"]\)'
new_get_doc = """def get_documents_path():
  home = os.path.expanduser('~')
  path = os.path.join(home, 'Documents')
  if not os.path.exists(path):
    os.makedirs(path, exist_ok=True)
  return path"""

code = re.sub(old_get_doc, new_get_doc, code, flags=re.DOTALL)

old_copy_admin = r'def copy_with_admin_if_needed\(src, target_dir, char_name\):\s+.*?return True, [\'"][\'"]'
new_copy_admin = """def copy_with_admin_if_needed(src, target_dir, char_name):
  dest_folder = os.path.join(target_dir, char_name)
  try:
    if os.path.exists(dest_folder):
      shutil.rmtree(dest_folder)
    shutil.copytree(src, dest_folder)
    return True, ''
  except Exception as e:
    return False, str(e)"""

code = re.sub(old_copy_admin, new_copy_admin, code, flags=re.DOTALL)
with open("utaun.py", "w", encoding="utf-8") as f:
    f.write(code)
