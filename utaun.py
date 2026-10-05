import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import unicodedata
import urllib.request
import wave
import winsound
import numpy as np
import zipfile
from PIL import Image
from pathlib import Path

CURRENT_VERSION = 'ver-1.0.9'
GITHUB_REPO = 'Siveweb/Utaun'
TARGET_ZIP_NAME = 'utaun.zip'


def update_documents_folder():
  documents_dir = Path(os.path.expanduser("~")) / "Documents"
  dest_dir = documents_dir / "子音部・濁音部フォルダ"

  try:
    base_path = sys._MEIPASS
  except Exception:
    base_path = os.path.abspath(".")

  src_dir = Path(base_path) / "子音部・濁音部フォルダ"

  if not src_dir.exists():
    src_dir_local = Path("./子音部・濁音部フォルダ")
    if src_dir_local.exists():
      src_dir = src_dir_local
    else:
      return

  dest_dir.mkdir(parents=True, exist_ok=True)

  for item in src_dir.iterdir():
    target_path = dest_dir / item.name
    if item.is_dir():
      if target_path.exists():
        shutil.rmtree(target_path)
      shutil.copytree(item, target_path)
    else:
      shutil.copy2(item, target_path)


def parse_version(v_str):
  v_str_normalized = unicodedata.normalize('NFKC', str(v_str))
  match = re.search(r'(\d+)\.(\d+)\.(\d+)', v_str_normalized)
  if match:
    return [int(match.group(1)), int(match.group(2)), int(match.group(3))]
  return [0, 0, 0]


def get_current_lang_dict():
  lang = '🇯🇵 日本語'
  if os.path.exists(CONFIG_PATH):
    try:
      with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        lang = data.get('lang', '🇯🇵 日本語')
    except:
      pass
  return LANG_DATA.get(lang, LANG_DATA['🇯🇵 日本語'])


def check_for_updates(silent=True):
  api_url = f'https://api.github.com/repos/{GITHUB_REPO}/releases/latest'
  l = get_current_lang_dict()
  try:
    req = urllib.request.Request(api_url, headers={'User-Agent': 'Utaun-App'})
    with urllib.request.urlopen(req) as response:
      data = json.loads(response.read().decode())
      latest_tag = data.get('tag_name', '')

      current_v = parse_version(CURRENT_VERSION)
      latest_v = parse_version(latest_tag)

      if latest_v > current_v:
        download_url = None

        for asset in data.get('assets', []):
          if asset['name'] == TARGET_ZIP_NAME:
            download_url = asset['browser_download_url']
            break

        if download_url and messagebox.askyesno(
            l.get('update_check', 'アップデート確認'),
            l.get(
                'ask_update',
                f'新しいバージョン ({latest_tag})'
                ' が見つかりました。\n今すぐアップデートしますか？',
            ).format(version=latest_tag),
        ):
          perform_update(download_url)
        elif not download_url and not silent:
          messagebox.showwarning(
              l.get('warning', '警告'),
              l.get(
                  'not_found_zip',
                  f'新しいバージョン ({latest_tag}) が見つかりましたが、'
                  f'指定のアップデートファイル ({TARGET_ZIP_NAME})'
                  'が見つかりませんでした。',
              ).format(version=latest_tag),
          )
      elif not silent:
        messagebox.showinfo(
            l.get('update_check', 'アップデート確認'),
            l.get('uptodate', 'お使いのバージョンは最新です！'),
        )
  except Exception as e:
    if not silent:
      messagebox.showerror(
          'エラー', f'アップデートの確認に失敗しました。\n{e}'
      )


def show_update_notes_window(parent_root):
  win = tk.Toplevel(parent_root)
  win.title('Utaun - 各言語のアップデート内容')
  win.geometry('1280x450')

  languages = {
      '🇯🇵 日本語': '🇯🇵',
      '🇬🇧 English': '🇬🇧',
      '🇺🇸 English': '🇺🇸',
      '🇰🇷 한국어': '🇰🇷',
      '🇨🇳 简体中文': '🇨🇳',
      '🇹🇼 繁體中文': '🇹🇼',
      '🇭🇰 廣東話': '🇭🇰',
      '🇷🇺 Русский': '🇷🇺',
      '🇵🇹 Português': '🇵🇹',
      '🇪🇸 Español': '🇪🇸',
      '🇫🇷 Français': '🇫🇷',
      '🇮🇹 Italiano': '🇮🇹',
      '🇩🇪 Deutsch': '🇩🇪',
      '🇵🇱 Polski': '🇵🇱',
      '🇹🇷 Türkçe': '🇹🇷',
      '🇻🇳 Tiếng Việt': '🇻🇳',
      '🇵🇭 Filipino': '🇵🇭',
      '🇹🇭 ไทย': '🇹🇭',
  }

  releases_cache = {}

  btn_frame = tk.Frame(win)
  btn_frame.pack(fill=tk.X, padx=10, pady=5)

  text_area = scrolledtext.ScrolledText(win, wrap=tk.WORD, width=70, height=22)
  text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

  def fetch_and_parse_releases():
    url = f'https://api.github.com/repos/{GITHUB_REPO}/releases'
    req = urllib.request.Request(url, headers={'User-Agent': 'Utaun-Updater'})

    try:
      with urllib.request.urlopen(req) as response:
        releases = json.loads(response.read().decode('utf-8'))

        for lang_label, code in languages.items():
          target_release = None
          code_lower = code.lower()

          for release in releases:
            tag = release.get('tag_name', '').lower()
            name = release.get('name', '').lower()
            body = release.get('body', '').lower()

            if code_lower in tag or code_lower in name:
              if code_lower == 'en-gb' and 'en-us' in tag:
                continue
              if code_lower == 'en-us' and 'en-gb' in tag:
                continue
              target_release = release
              break

          if target_release:
            tag = target_release.get('tag_name', '')
            body = target_release.get('body', 'リリースノートがありません。')
            releases_cache[lang_label] = f'【バージョン/タグ: {tag}】\n\n{body}'
          else:
            releases_cache[lang_label] = (
                'この言語のアップデート内容はまだ読み込まれていないか、存在しません。'
            )

    except Exception as e:
      error_msg = f'GitHubからのリリース情報取得に失敗しました:\n{e}'
      for lang_label in languages.keys():
        releases_cache[lang_label] = error_msg

    display_content('🇯🇵 日本語')

  def display_content(lang_label):
    text_area.delete('1.0', tk.END)
    content = releases_cache.get(
        lang_label,
        'この言語のアップデート内容はまだ読み込まれていないか、存在しません。',
    )
    text_area.insert(tk.END, content)

  for lang_label in languages.keys():
    btn = tk.Button(
        btn_frame,
        text=lang_label,
        command=lambda l=lang_label: display_content(l),
    )
    btn.pack(side=tk.LEFT, padx=2, pady=2)

  fetch_and_parse_releases()


def perform_update(download_url):
  try:
    if getattr(sys, 'frozen', False):
      current_exe = sys.executable
      current_dir = os.path.dirname(current_exe)
    else:
      messagebox.showwarning(
          '注意',
          '開発環境（スクリプト実行中）のため、自動アップデートのファイル置換はシミュレーションのみ行います。',
      )
      return

    temp_dir = tempfile.mkdtemp(prefix='utaun_update_')
    zip_path = os.path.join(temp_dir, 'update.zip')
    extract_dir = os.path.join(temp_dir, 'extracted')

    messagebox.showinfo(
        'ダウンロード中',
        'アップデートファイルをダウンロードしています...\n完了するまでしばらくお待ちください。',
    )
    urllib.request.urlretrieve(download_url, zip_path)

    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
      zip_ref.extractall(extract_dir)

    extracted_items = os.listdir(extract_dir)
    if len(extracted_items) == 1 and os.path.isdir(
        os.path.join(extract_dir, extracted_items[0])
    ):
      source_content_dir = os.path.join(extract_dir, extracted_items[0])
    else:
      source_content_dir = extract_dir

    batch_file = os.path.join(current_dir, 'update.bat')

    batch_content = f"""
@echo off
timeout /t 2 /nobreak > nul
set "DEST_DOC=%USERPROFILE%\\Documents"
if exist "%USERPROFILE%\\OneDrive\\Documents" (
    set "DEST_DOC=%USERPROFILE%\\OneDrive\\Documents"
) else if exist "%USERPROFILE%\\OneDrive\\ドキュメント" (
    set "DEST_DOC=%USERPROFILE%\\OneDrive\\ドキュメント"
)

if exist "%DEST_DOC%\\子音部・濁音部フォルダ" (
    rmdir /s /q "%DEST_DOC%\\子音部・濁音部フォルダ"
)
if exist "{source_content_dir}\\子音部・濁音部フォルダ" (
    mkdir "%DEST_DOC%\\子音部・濁音部フォルダ"
    xcopy /s /y /e "{source_content_dir}\\子音部・濁音部フォルダ\\*" "%DEST_DOC%\\子音部・濁音部フォルダ\\\\"
)

if exist "%DEST_DOC%\\oto.ini" (
    del /q "%DEST_DOC%\\oto.ini"
)
if exist "{source_content_dir}\\oto.ini" (
    copy /y "{source_content_dir}\\oto.ini" "%DEST_DOC%\\oto.ini"
)

cd /d "{current_dir}"

set "NEW_EXE="
for %%f in ("{source_content_dir}\\*utaun*.exe" "{source_content_dir}\\*Utaun*.exe") do (
    if exist "%%f" (
        copy /y "%%f" "{current_dir}\\"
        set "NEW_EXE={current_dir}\\%%~nxf"
    )
)

for %%f in (*utaun*.exe *Utaun*.exe) do (
    if /i not "%%~ff"=="%NEW_EXE%" (
        del /q "%%f"
    )
)

if not "%NEW_EXE%"=="" (
    set "PYINSTALLER_RESET_ENVIRONMENT=1"
    start "" "%NEW_EXE%"
)

rmdir /s /q "{temp_dir}"
del "%~f0"
"""
    with open(batch_file, 'w', encoding='shift_jis') as f:
      f.write(batch_content)

    subprocess.Popen(batch_file, shell=True)
    sys.exit(0)

  except Exception as e:
    messagebox.showerror(
        'アップデートエラー',
        f'アップデートの適用中にエラーが発生しました。\n{e}',
    )


def resource_path(relative_path):
  try:
    base_path = sys._MEIPASS
  except Exception:
    base_path = os.path.abspath('.')
  return os.path.join(base_path, relative_path)


def get_documents_path():
  home = os.path.expanduser('~')
  candidates = [
      os.path.join(home, 'OneDrive', 'ドキュメント'),
      os.path.join(home, 'OneDrive', 'Documents'),
      os.path.join(home, 'Documents'),
  ]
  for path in candidates:
    if os.path.exists(path):
      return path
  return os.path.join(home, 'Documents')


BASE_PATH = get_documents_path()
CONFIG_PATH = os.path.join(BASE_PATH, 'utaun_settings.json')

LANG_DATA = {
    '🇯🇵 日本語': {
        'name': '名前',
        'auth': '作者',
        'desc': '説明',
        'height': '高さ',
        'gen': '音源を作る！',
        'listen': '試聴',
        'lang_set': '言語設定',
        'enc_set': '文字コード',
        'theme_set': 'テーマ設定',
        'light': 'ライト',
        'dark': 'ダーク',
        'sc_set': 'ショートカット有効',
        'sc_list': (
            '【 ショートカット一覧 】\n---------------------------\n Ctrl +'
            ' Enter | 音源生成\n Ctrl + P      | 試聴\n Ctrl + A      | 全選択\n'
            ' Ctrl + C / V | ｺﾋﾟｰ / 貼付\n Enter          | 保存して閉じる'
        ),
        'msg_success': '「{}」のzipエクスポートが完了しました！',
        'err_no_folder': (
            '「子音部・濁音部フォルダ」と「oto.ini」がドキュメントに無いよ！'
        ),
        'err_admin_cancel': (
            '管理者権限の許可がキャンセルされたか、コピーに失敗しました。'
        ),
        'err_ou': 'OpenUTAUフォルダへの書き込みが拒否されました:\n{}',
        'err_utau': '従来UTAUフォルダへの書き込みに失敗しました:\n{}',
        'err_export': 'zipファイルの出力に失敗しました:\n{}',
        'decide': '決定',
        'settings_title': '設定 ＆ エクスポート先管理',
        'target_set': '【 エクスポート先設定 】',
        'ou_label': 'OpenUTAU用 (フォルダ自動出力)',
        'utau_label': '従来UTAU用 (フォルダ自動出力)',
        'export_label': 'デフォルトエクスポート先 (zip)',
        'update_btn': 'アップデート確認',
        'update_notes_btn': '各言語のアップデート内容を確認',
        'update_check': 'アップデート確認',
        'warning': '警告',
        'uptodate': 'お使いのバージョンは最新です！',
        'not_found_zip': (
            '新しいバージョン ({version}) が見つかりましたが、'
            '指定のアップデートファイル (utaun.zip) が見つかりませんでした。'
        ),
        'ask_update': (
            '新しいバージョン ({version}) が見つかりました。\n'
            'アップデートしますか？'
        ),
    },
    '🇬🇧 English': {
        'name': 'Name',
        'auth': 'Author',
        'desc': 'Readme',
        'height': 'Height',
        'gen': 'GENERATE!',
        'listen': 'Listen',
        'lang_set': 'Language',
        'enc_set': 'Encoding',
        'theme_set': 'Theme',
        'light': 'Light',
        'dark': 'Dark',
        'sc_set': 'Enable Shortcuts',
        'sc_list': (
            '[ Shortcut Keys ]\n---------------------------\n Ctrl + Enter |'
            ' Generate\n Ctrl + P      | Listen\n Ctrl + A      | Select All\n'
            ' Ctrl + C / V | Copy / Paste\n Enter          | Save & Close'
        ),
        'msg_success': "Voice bank '{}' exported as zip successfully!",
        'err_no_folder': (
            "'子音部・濁音部フォルダ' and 'oto.ini' were not found in Documents!"
        ),
        'err_admin_cancel': (
            'Administrator permission was cancelled or copy failed.'
        ),
        'err_ou': 'Failed to write to OpenUTAU folder:\n{}',
        'err_utau': 'Failed to write to UTAU folder:\n{}',
        'err_export': 'Failed to create zip file:\n{}',
        'decide': 'Apply',
        'settings_title': 'Settings & Export Targets',
        'target_set': '[ Export Target Settings ]',
        'ou_label': 'For OpenUTAU (Auto export folder)',
        'utau_label': 'For classic UTAU (Auto export folder)',
        'export_label': 'Default Export Directory (zip)',
        'update_btn': 'Check for Updates',
        'update_notes_btn': 'Check Release Notes by Language',
        'update_check': 'Check for Updates',
        'warning': 'Warning',
        'uptodate': 'You are on the latest version!',
        'not_found_zip': (
            'A new version ({version}) was found, but the specified'
            ' update file (utaun.zip) could not be found.'
        ),
        'ask_update': (
            'A new version ({version}) has been found.\nWould you like'
            ' to update?'
        ),
    },
    '🇺🇸 English': {
        'name': 'Name',
        'auth': 'Author',
        'desc': 'Readme',
        'height': 'Height',
        'gen': 'GENERATE!',
        'listen': 'Listen',
        'lang_set': 'Language',
        'enc_set': 'Encoding',
        'theme_set': 'Theme',
        'light': 'Light',
        'dark': 'Dark',
        'sc_set': 'Enable Shortcuts',
        'sc_list': (
            '[ Shortcut Keys ]\n---------------------------\n Ctrl + Enter |'
            ' Generate\n Ctrl + P      | Listen\n Ctrl + A      | Select All\n'
            ' Ctrl + C / V | Copy / Paste\n Enter          | Save & Close'
        ),
        'msg_success': "Voice bank '{}' exported as zip successfully!",
        'err_no_folder': (
            "'子音部・濁音部フォルダ' and 'oto.ini' were not found in Documents!"
        ),
        'err_admin_cancel': (
            'Administrator permission was cancelled or copy failed.'
        ),
        'err_ou': 'Failed to write to OpenUTAU folder:\n{}',
        'err_utau': 'Failed to write to UTAU folder:\n{}',
        'err_export': 'Failed to create zip file:\n{}',
        'decide': 'Apply',
        'settings_title': 'Settings & Export Targets',
        'target_set': '[ Export Target Settings ]',
        'ou_label': 'For OpenUTAU (Auto export folder)',
        'utau_label': 'For classic UTAU (Auto export folder)',
        'export_label': 'Default Export Directory (zip)',
        'update_btn': 'Check for Updates',
        'update_notes_btn': 'Check Release Notes by Language',
        'update_check': 'Check for Updates',
        'warning': 'Warning',
        'uptodate': 'You are on the latest version!',
        'not_found_zip': (
            'A new version ({version}) was found, but the specified'
            ' update file (utaun.zip) could not be found.'
        ),
        'ask_update': (
            'A new version ({version}) has been found.\nWould you like'
            ' to update?'
        ),
    },
    '🇰🇷 한국어': {
        'name': '이름',
        'auth': '작성자',
        'desc': '설명',
        'height': '높이',
        'gen': '음원 만들기!',
        'listen': '미리듣기',
        'lang_set': '언어 설정',
        'enc_set': '인코딩',
        'theme_set': '테마 설정',
        'light': '라이트',
        'dark': '다크',
        'sc_set': '단축키 사용',
        'sc_list': (
            '[ 단축키 목록 ]\n---------------------------\n Ctrl + Enter | 음원'
            ' 생성\n Ctrl + P      | 미리듣기\n Ctrl + A      | 모두 선택\n Ctrl'
            ' + C / V | 복사 / 붙여넣기\n Enter          | 저장 후 닫기'
        ),
        'msg_success': "음원 '{}' zip 내보내기가 완료되었습니다!",
        'err_no_folder': "'子音部・濁音部フォルダ'와 'oto.ini'가 문서 폴더에 없습니다!",
        'err_admin_cancel': (
            '관리자 권한 요청이 취소되었거나 복사에 실패했습니다.'
        ),
        'err_ou': 'OpenUTAU 폴더 쓰기 실패:\n{}',
        'err_utau': '기존 UTAU 폴더 쓰기 실패:\n{}',
        'err_export': 'zip 파일 생성 실패:\n{}',
        'decide': '적용',
        'settings_title': '설정 및 내보내기 관리',
        'target_set': '[ 내보내기 대상 설정 ]',
        'ou_label': 'OpenUTAU용 (자동 폴더 내보내기)',
        'utau_label': '기존 UTAU용 (자동 폴더 내보내기)',
        'export_label': '기본 내보내기 디렉토리 (zip)',
        'update_btn': '업데이트 확인',
        'update_notes_btn': '언어별 업데이트 내용 확인',
        'update_check': '업데이트 확인',
        'warning': '경고',
        'uptodate': '최신 버전을 사용 중입니다!',
        'not_found_zip': (
            '새로운 버전 ({version})을 찾았지만, 지정된 업데이트 파일'
            ' (utaun.zip)을 찾을 수 없습니다.'
        ),
        'ask_update': (
            '새로운 버전 ({version})이 발견되었습니다.\n업데이트하시겠습니까?'
        ),
    },
    '🇨🇳 简体中文': {
        'name': '名称',
        'auth': '作者',
        'desc': '说明',
        'height': '高度',
        'gen': '生成音源！',
        'listen': '试听',
        'lang_set': '语言设置',
        'enc_set': '编码',
        'theme_set': '主题设置',
        'light': '浅色',
        'dark': '深色',
        'sc_set': '启用快捷键',
        'sc_list': (
            '[ 快捷键列表 ]\n---------------------------\n Ctrl + Enter |'
            ' 生成音源\n Ctrl + P      | 试听\n Ctrl + A      | 全选\n Ctrl +'
            ' C / V | 复制 / 粘贴\n Enter          | 保存并关闭'
        ),
        'msg_success': '音源“{}”zip导出成功！',
        'err_no_folder': '文档中未找到“子音部・濁音部フォルダ”和“oto.ini”！',
        'err_admin_cancel': '管理员权限被取消或复制失败。',
        'err_ou': '写入 OpenUTAU 文件夹失败:\n{}',
        'err_utau': '写入传统 UTAU 文件夹失败:\n{}',
        'err_export': '生成 zip 文件失败:\n{}',
        'decide': '应用',
        'settings_title': '设置与导出管理',
        'target_set': '[ 导出目标设置 ]',
        'ou_label': '适用于 OpenUTAU (自动导出)',
        'utau_label': '适用于传统 UTAU (自动导出)',
        'export_label': '默认导出目录 (zip)',
        'update_btn': '检查更新',
        'update_notes_btn': '查看各语言更新日志',
        'update_check': '检查更新',
        'warning': '警告',
        'uptodate': '您当前使用的是最新版本！',
        'not_found_zip': (
            '发现新版本 ({version})，但未找到指定的更新文件 (utaun.zip)。'
        ),
        'ask_update': '发现新版本 ({version})。\n是否要更新？',
    },
    '🇹🇼 繁體中文': {
        'name': '名稱',
        'auth': '作者',
        'desc': '說明',
        'height': '高度',
        'gen': '生成音源！',
        'listen': '試聽',
        'lang_set': '語言設定',
        'enc_set': '編碼',
        'theme_set': '佈景主題',
        'light': '亮色',
        'dark': '暗色',
        'sc_set': '啟用快捷鍵',
        'sc_list': (
            '[ 快捷鍵列表 ]\n---------------------------\n Ctrl + Enter |'
            ' 生成音源\n Ctrl + P      | 試聽\n Ctrl + A      | 全選\n Ctrl +'
            ' C / V | 複製 / 貼上\n Enter          | 儲存並關閉'
        ),
        'msg_success': '音源「{}」zip匯出成功！',
        'err_no_folder': '文件中找不到「子音部・濁音部フォルダ」與「oto.ini」！',
        'err_admin_cancel': '管理員權限遭取消或複製失敗。',
        'err_ou': '寫入 OpenUTAU 資料夾失敗:\n{}',
        'err_utau': '寫入傳統 UTAU 資料夾失敗:\n{}',
        'err_export': '建立 zip 檔案失敗:\n{}',
        'decide': '套用',
        'settings_title': '設定與匯出管理',
        'target_set': '[ 匯出目標設定 ]',
        'ou_label': '適用於 OpenUTAU (自動匯出)',
        'utau_label': '適用於傳統 UTAU (自動匯出)',
        'export_label': '預設匯出目錄 (zip)',
        'update_btn': '檢查更新',
        'update_notes_btn': '查看各語言更新內容',
        'update_check': '檢查更新',
        'warning': '警告',
        'uptodate': '您目前使用的是最新版本！',
        'not_found_zip': (
            '已找到新版本 ({version})，但找不到指定的更新檔案 (utaun.zip)。'
        ),
        'ask_update': '已找到新版本 ({version})。\n要更新嗎？',
    },
    '🇭🇰 廣東話': {
        'name': '名',
        'auth': '作者',
        'desc': '說明',
        'height': '高度',
        'gen': '整音源！',
        'listen': '試聽',
        'lang_set': '語言設定',
        'enc_set': '編碼',
        'theme_set': '主題設定',
        'light': '淺色',
        'dark': '深色',
        'sc_set': '開啓捷徑鍵',
        'sc_list': (
            '[ 捷徑鍵一覽 ]\n---------------------------\n Ctrl + Enter |'
            ' 生成音源\n Ctrl + P      | 試聽\n Ctrl + A      | 全選\n Ctrl +'
            ' C / V | 複製 / 貼上\n Enter          | 儲存並關閉'
        ),
        'msg_success': '音源「{}」zip匯出成功！',
        'err_no_folder': '文件夾搵唔到「子音部・濁音部フォルダ」同「oto.ini」！',
        'err_admin_cancel': '管理員權限被取消或複製失敗。',
        'err_ou': '寫入 OpenUTAU 資料夾失敗:\n{}',
        'err_utau': '寫入傳統 UTAU 資料夾失敗:\n{}',
        'err_export': '建立 zip 檔案失敗:\n{}',
        'decide': '套用',
        'settings_title': '設定同匯出管理',
        'target_set': '[ 匯出目標設定 ]',
        'ou_label': '適用 OpenUTAU (自動匯出)',
        'utau_label': '適用傳統 UTAU (自動匯出)',
        'export_label': '預設匯出路徑 (zip)',
        'update_btn': '檢查更新',
        'update_notes_btn': '查看各語言更新內容',
        'update_check': '檢查更新',
        'warning': '警告',
        'uptodate': '你依家使緊最新版本！',
        'not_found_zip': (
            '搵到新版本 ({version})，但搵唔到指定嘅更新檔案 (utaun.zip)。'
        ),
        'ask_update': '搵到新版本 ({version})。\n想唔想更新？',
    },
    '🇷🇺 Русский': {
        'name': 'Имя',
        'auth': 'Автор',
        'desc': 'Описание',
        'height': 'Высота',
        'gen': 'СОЗДАТЬ!',
        'listen': 'Прослушать',
        'lang_set': 'Язык',
        'enc_set': 'Кодировка',
        'theme_set': 'Тема',
        'light': 'Светлая',
        'dark': 'Темная',
        'sc_set': 'Включить горячие клавиши',
        'sc_list': (
            '[ Горячие клавиши ]\n---------------------------\n Ctrl + Enter'
            ' | Создать\n Ctrl + P      | Прослушать\n Ctrl + A      | Выбрать'
            ' все\n Ctrl + C / V | Копировать / Вставить\n Enter          | Сохранить'
            ' и закрыть'
        ),
        'msg_success': "Гомбанк '{}' успешно экспортирован в zip!",
        'err_no_folder': "Папка '子音部・濁音部フォルダ' и 'oto.ini' не найдены в Документах!",
        'err_admin_cancel': 'Права администратора отменены или ошибка копирования.',
        'err_ou': 'Ошибка записи в папку OpenUTAU:\n{}',
        'err_utau': 'Ошибка записи в папку UTAU:\n{}',
        'err_export': 'Ошибка создания zip-файла:\n{}',
        'decide': 'Применить',
        'settings_title': 'Настройки и экспорт',
        'target_set': '[ Настройки папок экспорта ]',
        'ou_label': 'Для OpenUTAU (Автоэкспорт)',
        'utau_label': 'Для классического UTAU (Автоэкспорт)',
        'export_label': 'Каталог экспорта по умолчанию (zip)',
        'update_btn': 'Проверить обновления',
        'update_notes_btn': 'Посмотреть обновления по языкам',
        'update_check': 'Проверка обновлений',
        'warning': 'Предупреждение',
        'uptodate': 'У вас установлена последняя версия!',
        'not_found_zip': (
            'Найдена новая версия ({version}), но указанный файл обновления'
            ' (utaun.zip) не найден.'
        ),
        'ask_update': (
            'Найдена новая версия ({version}).\nХотите обновить?'
        ),
    },
    '🇵🇹 Português': {
        'name': 'Nome',
        'auth': 'Autor',
        'desc': 'Descrição',
        'height': 'Altura',
        'gen': 'GERAR!',
        'listen': 'Ouvir',
        'lang_set': 'Idioma',
        'enc_set': 'Codificação',
        'theme_set': 'Tema',
        'light': 'Claro',
        'dark': 'Escuro',
        'sc_set': 'Ativar Atalhos',
        'sc_list': (
            '[ Teclas de Atalho ]\n---------------------------\n Ctrl + Enter'
            ' | Gerar\n Ctrl + P      | Ouvir\n Ctrl + A      | Selecionar'
            ' Tudo\n Ctrl + C / V | Copiar / Colar\n Enter          | Salvar e'
            ' Fechar'
        ),
        'msg_success': "Banco de voz '{}' exportado como zip com sucesso!",
        'err_no_folder': "Pasta '子音部・濁音部フォルダ' e 'oto.ini' não encontrados em Documentos!",
        'err_admin_cancel': 'Permissão de administrador cancelada ou falha na cópia.',
        'err_ou': 'Falha ao gravar na pasta OpenUTAU:\n{}',
        'err_utau': 'Falha ao gravar na pasta UTAU:\n{}',
        'err_export': 'Falha ao criar o arquivo zip:\n{}',
        'decide': 'Aplicar',
        'settings_title': 'Configurações e Exportação',
        'target_set': '[ Configurações de Destino ]',
        'ou_label': 'Para OpenUTAU (Exportar auto)',
        'utau_label': 'Para UTAU clássico (Exportar auto)',
        'export_label': 'Diretório de Exportação Padrão (zip)',
        'update_btn': 'Verificar atualizações',
        'update_notes_btn': 'Ver notas de atualização por idioma',
        'update_check': 'Verificar atualizações',
        'warning': 'Aviso',
        'uptodate': 'Você já está na versão mais recente!',
        'not_found_zip': (
            'Uma nova versão ({version}) foi encontrada, mas o arquivo de'
            ' atualização especificado (utaun.zip) não foi encontrado.'
        ),
        'ask_update': (
            'Uma nova versão ({version}) foi encontrada.\nDeseja atualizar?'
        ),
    },
    '🇪🇸 Español': {
        'name': 'Nombre',
        'auth': 'Autor',
        'desc': 'Descripción',
        'height': 'Altura',
        'gen': '¡GENERAR!',
        'listen': 'Escuchar',
        'lang_set': 'Idioma',
        'enc_set': 'Codificación',
        'theme_set': 'Tema',
        'light': 'Claro',
        'dark': 'Oscuro',
        'sc_set': 'Habilitar Atajos',
        'sc_list': (
            '[ Teclas de Atajo ]\n---------------------------\n Ctrl + Enter'
            ' | Generar\n Ctrl + P      | Escuchar\n Ctrl + A      | Seleccionar'
            ' Todo\n Ctrl + C / V | Copiar / Pegar\n Enter          | Guardar y'
            ' Cerrar'
        ),
        'msg_success': '¡Banco de voz "{}" exportado como zip con éxito!',
        'err_no_folder': "¡No se encontró la carpeta '子音部・濁音部フォルダ' y 'oto.ini' en Documentos!",
        'err_admin_cancel': 'Permiso de administrador cancelado o error al copiar.',
        'err_ou': 'Error al escribir en la carpeta OpenUTAU:\n{}',
        'err_utau': 'Error al escribir en la carpeta UTAU:\n{}',
        'err_export': 'Error al crear el archivo zip:\n{}',
        'decide': 'Aplicar',
        'settings_title': 'Ajustes y Exportación',
        'target_set': '[ Destinos de Exportación ]',
        'ou_label': 'Para OpenUTAU (Exportar auto)',
        'utau_label': 'Para UTAU clásico (Exportar auto)',
        'export_label': 'Directorio de exportación predeterminado (zip)',
        'update_btn': 'Buscar actualizaciones',
        'update_notes_btn': 'Ver notas de versión por idioma',
        'update_check': 'Comprobar actualizaciones',
        'warning': 'Advertencia',
        'uptodate': '¡Estás usando la última versión!',
        'not_found_zip': (
            'Se encontró una nueva versión ({version}), pero no se encontró el'
            ' archivo de actualización especificado (utaun.zip).'
        ),
        'ask_update': (
            'Se ha encontrado una nueva versión ({version}).\n¿Quieres'
            ' actualizar?'
        ),
    },
    '🇫🇷 Français': {
        'name': 'Nom',
        'auth': 'Auteur',
        'desc': 'Description',
        'height': 'Hauteur',
        'gen': 'GÉNÉRER !',
        'listen': 'Écouter',
        'lang_set': 'Langue',
        'enc_set': 'Encodage',
        'theme_set': 'Thème',
        'light': 'Clair',
        'dark': 'Sombre',
        'sc_set': 'Activer Raccourcis',
        'sc_list': (
            '[ Raccourcis Clavier ]\n---------------------------\n Ctrl + Enter'
            ' | Générer\n Ctrl + P      | Écouter\n Ctrl + A      | Tout'
            ' sélectionner\n Ctrl + C / V | Copier / Coller\n Enter         '
            ' | Enregistrer et Fermer'
        ),
        'msg_success': "Banque vocale '{}' exportée en zip avec succès !",
        'err_no_folder': "Dossier '子音部・濁音部フォルダ' et 'oto.ini' introuvables dans Documents !",
        'err_admin_cancel': 'Autorisation administrateur annulée ou échec de copie.',
        'err_ou': "Échec d'écriture dans le dossier OpenUTAU :\n{}",
        'err_utau': "Échec d'écriture dans le dossier UTAU :\n{}",
        'err_export': 'Échec de création du fichier zip :\n{}',
        'decide': 'Appliquer',
        'settings_title': 'Paramètres & Exports',
        'target_set': "[ Cibles d'exportation ]",
        'ou_label': 'Pour OpenUTAU (Export auto)',
        'utau_label': 'Pour UTAU classique (Export auto)',
        'export_label': "Dossier d'exportation par défaut (zip)",
        'update_btn': 'Vérifier les mises à jour',
        'update_notes_btn': 'Voir les notes de version par langue',
        'update_check': 'Vérifier les mises à jour',
        'warning': 'Avertissement',
        'uptodate': 'Vous utilisez la dernière version !',
        'not_found_zip': (
            'Une nouvelle version ({version}) a été trouvée, mais le fichier'
            ' de mise à jour spécifié (utaun.zip) est introuvable.'
        ),
        'ask_update': (
            'Une nouvelle version ({version}) a été trouvée.\nVoulez-vous la'
            ' mettre à jour ?'
        ),
    },
    '🇮🇹 Italiano': {
        'name': 'Nome',
        'auth': 'Autore',
        'desc': 'Descrizione',
        'height': 'Altezza',
        'gen': 'GENERA!',
        'listen': 'Ascolta',
        'lang_set': 'Lingua',
        'enc_set': 'Codifica',
        'theme_set': 'Tema',
        'light': 'Chiaro',
        'dark': 'Scuro',
        'sc_set': 'Abilita Scorciatoie',
        'sc_list': (
            '[ Scorciatoie da tastiera ]\n---------------------------\n Ctrl +'
            ' Enter | Genera\n Ctrl + P      | Ascolta\n Ctrl + A      | Seleziona'
            ' Tutto\n Ctrl + C / V | Copia / Incolla\n Enter          | Salva e'
            ' Chiudi'
        ),
        'msg_success': "Banco vocale '{}' esportato in zip con successo!",
        'err_no_folder': "Cartella '子音部・濁音部フォルダ' e 'oto.ini' non trovati in Documenti!",
        'err_admin_cancel': 'Permesso amministratore annullato o copia fallita.',
        'err_ou': 'Scrittura cartella OpenUTAU fallita:\n{}',
        'err_utau': 'Scrittura cartella UTAU fallita:\n{}',
        'err_export': 'Creazione file zip fallita:\n{}',
        'decide': 'Applica',
        'settings_title': 'Impostazioni ed Esportazione',
        'target_set': '[ Impostazioni Destinazione ]',
        'ou_label': 'Per OpenUTAU (Esportazione auto)',
        'utau_label': 'Per UTAU classico (Esportazione auto)',
        'export_label': 'Cartella di esportazione predefinita (zip)',
        'update_btn': 'Controlla aggiornamenti',
        'update_notes_btn': 'Visualizza note di rilascio per lingua',
        'update_check': 'Verifica aggiornamenti',
        'warning': 'Avviso',
        'uptodate': "Stai utilizzando l'ultima versione!",
        'not_found_zip': (
            'È stata trovata una nuova versione ({version}), ma il file di'
            ' aggiornamento specificato (utaun.zip) non è stato trovato.'
        ),
        'ask_update': (
            'È stata trovata una nuova versione ({version}).\nVuoi aggiornare?'
        ),
    },
    '🇩🇪 Deutsch': {
        'name': 'Name',
        'auth': 'Autor',
        'desc': 'Beschreibung',
        'height': 'Tonhöhe',
        'gen': 'GENERIEREN!',
        'listen': 'Anhören',
        'lang_set': 'Sprache',
        'enc_set': 'Kodierung',
        'theme_set': 'Thema',
        'light': 'Hell',
        'dark': 'Dunkel',
        'sc_set': 'Tastenkombinationen',
        'sc_list': (
            '[ Tastenkombinationen ]\n---------------------------\n Ctrl +'
            ' Enter | Generieren\n Ctrl + P      | Anhören\n Ctrl + A      | Alle'
            ' auswählen\n Ctrl + C / V | Kopieren / Einfügen\n Enter         '
            ' | Speichern & Schließen'
        ),
        'msg_success': "Voicebank '{}' erfolgreich as Zip exportiert!",
        'err_no_folder': "Ordner '子音部・濁音部フォルダ' und 'oto.ini' nicht in Dokumenten gefunden!",
        'err_admin_cancel': (
            'Administratorrechte abgebrochen oder Kopieren fehlgeschlagen.'
        ),
        'err_ou': 'Fehler beim Schreiben in den OpenUTAU-Ordner:\n{}',
        'err_utau': 'Fehler beim Schreiben in den UTAU-Ordner:\n{}',
        'err_export': 'Fehler beim Erstellen der Zip-Datei:\n{}',
        'decide': 'Anwenden',
        'settings_title': 'Einstellungen & Export',
        'target_set': '[ Export-Ziel Einstellungen ]',
        'ou_label': 'Für OpenUTAU (Autom. Export)',
        'utau_label': 'Für klassisches UTAU (Autom. Export)',
        'export_label': 'Standard-Exportverzeichnis (zip)',
        'update_btn': 'Nach Updates suchen',
        'update_notes_btn': 'Versionshinweise nach Sprache anzeigen',
        'update_check': 'Nach Updates suchen',
        'warning': 'Warnung',
        'uptodate': 'Sie verwenden die neueste Version!',
        'not_found_zip': (
            'Eine neue Version ({version}) wurde gefunden, aber die'
            ' angegebene Update-Datei (utaun.zip) wurde nicht gefunden.'
        ),
        'ask_update': (
            'Eine neue Version ({version}) wurde gefunden.\nMöchten Sie'
            ' aktualisieren?'
        ),
    },
    '🇵🇱 Polski': {
        'name': 'Nazwa',
        'auth': 'Autor',
        'desc': 'Opis',
        'height': 'Wysokość',
        'gen': 'GENERUJ!',
        'listen': 'Słuchaj',
        'lang_set': 'Język',
        'enc_set': 'Kodowanie',
        'theme_set': 'Motyw',
        'light': 'Jasny',
        'dark': 'Ciemny',
        'sc_set': 'Włącz skróty',
        'sc_list': (
            '[ Lista skrótów ]\n---------------------------\n Ctrl + Enter |'
            ' Generuj\n Ctrl + P      | Słuchaj\n Ctrl + A      | Zaznacz'
            ' wszystko\n Ctrl + C / V | Kopiuj / Wklej\n Enter          | Zapisz'
            ' i zamknij'
        ),
        'msg_success': "Bank głosu '{}' pomyślnie wyeksportowany jako zip!",
        'err_no_folder': "Nie znaleziono folderu '子音部・濁音部フォルダ' oraz 'oto.ini' w Dokumentach!",
        'err_admin_cancel': 'Anulowano uprawnienia administratora lub błąd kopiowania.',
        'err_ou': 'Błąd zapisu do folderu OpenUTAU:\n{}',
        'err_utau': 'Błąd zapisu do folderu UTAU:\n{}',
        'err_export': 'Błąd tworzenia pliku zip:\n{}',
        'decide': 'Zastosuj',
        'settings_title': 'Ustawienia i Eksport',
        'target_set': '[ Ustawienia celów eksportu ]',
        'ou_label': 'Dla OpenUTAU (Autom. eksport)',
        'utau_label': 'Dla klasycznego UTAU (Autom. eksport)',
        'export_label': 'Domyślny katalog eksportu (zip)',
        'update_btn': 'Sprawdź aktualizacje',
        'update_notes_btn': 'Wyświetl informacje o wydaniu według języka',
        'update_check': 'Sprawdź aktualizacje',
        'warning': 'Ostrzeżenie',
        'uptodate': 'Masz najnowszą wersję!',
        'not_found_zip': (
            'Znaleziono nową wersję ({version}), ale nie znaleziono wskazanego'
            ' pliku aktualizacji (utaun.zip).'
        ),
        'ask_update': (
            'Znaleziono nową wersję ({version}).\nCzy chcesz zaktualizować?'
        ),
    },
    '🇹🇷 Türkçe': {
        'name': 'Ad',
        'auth': 'Yazar',
        'desc': 'Açıklama',
        'height': 'Yükseklik',
        'gen': 'OLUŞTUR!',
        'listen': 'Dinle',
        'lang_set': 'Dil',
        'enc_set': 'Kodlama',
        'theme_set': 'Tema',
        'light': 'Açık',
        'dark': 'Koyu',
        'sc_set': 'Kısayolları Etkinleştir',
        'sc_list': (
            '[ Kısayol Tuşları ]\n---------------------------\n Ctrl + Enter |'
            ' Oluştur\n Ctrl + P      | Dinle\n Ctrl + A      | Tümünü Seç\n Ctrl'
            ' + C / V | Kopyala / Yapıştır\n Enter          | Kaydet ve Kapat'
        ),
        'msg_success': "'{}' ses bankası başarıyla zip olarak dışarı aktarıldı!",
        'err_no_folder': "Belgeler'de '子音部・濁音部フォルダ' ve 'oto.ini' bulunamadı!",
        'err_admin_cancel': 'Yönetici izni iptal edildi veya kopyalama başarısız oldu.',
        'err_ou': 'OpenUTAU klasörüne yazılamadı:\n{}',
        'err_utau': 'Klasik UTAU klasörüne yazılamadı:\n{}',
        'err_export': 'Zip dosyası oluşturulamadı:\n{}',
        'decide': 'Uygula',
        'settings_title': 'Ayarlar ve Dışa Aktarım',
        'target_set': '[ Dışa Aktarım Hedefleri ]',
        'ou_label': 'OpenUTAU için (Otomatik dışa aktar)',
        'utau_label': 'Klasik UTAU için (Otomatik dışa aktar)',
        'export_label': 'Varsayılan Dışa Aktarma Dizini (zip)',
        'update_btn': 'Güncellemeleri kontrol et',
        'update_notes_btn': 'Dile göre sürüm notlarını kontrol et',
        'update_check': 'Güncellemeleri Kontrol Et',
        'warning': 'Uyarı',
        'uptodate': 'En son sürümü kullanıyorsunuz!',
        'not_found_zip': (
            'Yeni bir sürüm ({version}) bulundu, ancak belirtilen güncelleme'
            ' dosyası (utaun.zip) bulunamadı.'
        ),
        'ask_update': (
            'Yeni bir sürüm ({version}) bulundu.\nGüncellemek ister misiniz?'
        ),
    },
    '🇻🇳 Tiếng Việt': {
        'name': 'Tên',
        'auth': 'Tác giả',
        'desc': 'Mô tả',
        'height': 'Độ cao',
        'gen': 'TẠO!',
        'listen': 'Nghe',
        'lang_set': 'Ngôn ngữ',
        'enc_set': 'Mã hóa',
        'theme_set': 'Giao diện',
        'light': 'Sáng',
        'dark': 'Tối',
        'sc_set': 'Bật Phím tắt',
        'sc_list': (
            '[ Danh sách phím tắt ]\n---------------------------\n Ctrl +'
            ' Enter | Tạo\n Ctrl + P      | Nghe thử\n Ctrl + A      | Chọn tất'
            ' cả\n Ctrl + C / V | Sao chép / Dán\n Enter          | Lưu & Đóng'
        ),
        'msg_success': "Đã xuất ngân hàng giọng nói '{}' dạng zip thành công!",
        'err_no_folder': "Không tìm thấy thư mục '子音部・濁音部フォルダ' và 'oto.ini' trong Tài liệu!",
        'err_admin_cancel': 'Quyền quản trị đã bị hủy hoặc sao chép thất bại.',
        'err_ou': 'Không thể ghi vào thư mục OpenUTAU:\n{}',
        'err_utau': 'Không thể ghi vào thư mục UTAU:\n{}',
        'err_export': 'Không thể tạo tệp zip:\n{}',
        'decide': 'Áp dụng',
        'settings_title': 'Cài đặt & Xuất',
        'target_set': '[ Cài đặt đích xuất ]',
        'ou_label': 'Dành cho OpenUTAU (Tự động xuất)',
        'utau_label': 'Dành cho UTAU cổ điển (Tự động xuất)',
        'export_label': 'Thư mục xuất mặc định (zip)',
        'update_btn': 'Kiểm tra cập nhật',
        'update_notes_btn': 'Xem ghi chú phát hành theo ngôn ngữ',
        'update_check': 'Kiểm tra cập nhật',
        'warning': 'Cảnh báo',
        'uptodate': 'Bạn đang sử dụng phiên bản mới nhất!',
        'not_found_zip': (
            'Đã tìm thấy phiên bản mới ({version}), nhưng không tìm thấy tệp'
            ' cập nhật được chỉ định (utaun.zip).'
        ),
        'ask_update': (
            'Đã tìm thấy phiên bản mới ({version}).\nBạn có muốn cập nhật'
            ' không?'
        ),
    },
    '🇵🇭 Filipino': {
        'name': 'Pangalan',
        'auth': 'May-akda',
        'desc': 'Paglalarawan',
        'height': 'Taas',
        'gen': 'GUMAGAWA!',
        'listen': 'Makinig',
        'lang_set': 'Wika',
        'enc_set': 'Encoding',
        'theme_set': 'Tema',
        'light': 'Maliwanag',
        'dark': 'Madilim',
        'sc_set': 'Paganahin ang Shortcuts',
        'sc_list': (
            '[ Listahan ng Shortcuts ]\n---------------------------\n Ctrl +'
            ' Enter | Bumuo\n Ctrl + P      | Makinig\n Ctrl + A      | Piliin'
            ' Lahat\n Ctrl + C / V | Kopya / Idikit\n Enter          | I-save at'
            ' Isara'
        ),
        'msg_success': "Matagumpay na na-export ang voice bank na '{}' bilang zip!",
        'err_no_folder': "Hindi natagpuan ang folder na '子音部・濁音部フォルダ' at 'oto.ini' sa Documents!",
        'err_admin_cancel': 'Kinansela ang pahintulot ng admin o nabigo ang pagkopya.',
        'err_ou': 'Nabigong isulat sa OpenUTAU folder:\n{}',
        'err_utau': 'Nabigong isulat sa UTAU folder:\n{}',
        'err_export': 'Nabigong gumawa ng zip file:\n{}',
        'decide': 'Ilapat',
        'settings_title': 'Mga Setting at Export',
        'target_set': '[ Mga Setting ng Export Target ]',
        'ou_label': 'Para sa OpenUTAU (Auto export)',
        'utau_label': 'Para sa klasikong UTAU (Auto export)',
        'export_label': 'Default na Export Directory (zip)',
        'update_btn': 'Suriin ang mga update',
        'update_notes_btn': 'Tignan ang mga release note ayon sa wika',
        'update_check': 'Suriin ang mga Update',
        'warning': 'Babala',
        'uptodate': 'Gamit mo ang pinakabagong bersyon!',
        'not_found_zip': (
            'May natagpuang bagong bersyon ({version}), ngunit ang tinukoy na'
            ' update file (utaun.zip) ay hindi nahanap.'
        ),
        'ask_update': (
            'May nakitang bagong bersyon ({version}).\nGusto mo bang mag-update?'
        ),
    },
    '🇹🇭 ไทย': {
        'name': 'ชื่อ',
        'auth': 'ผู้แต่ง',
        'desc': 'คำอธิบาย',
        'height': 'ความสูง',
        'gen': 'สร้างเสียง!',
        'listen': 'ฟัง',
        'lang_set': 'ภาษา',
        'enc_set': 'การเข้ารหัส',
        'theme_set': 'ธีม',
        'light': 'สว่าง',
        'dark': 'มืด',
        'sc_set': 'เปิดใช้งานทางลัด',
        'sc_list': (
            '[ รายการทางลัด ]\n---------------------------\n Ctrl + Enter |'
            ' สร้าง\n Ctrl + P      | ฟัง\n Ctrl + A      | เลือกทั้งหมด\n Ctrl'
            ' + C / V | คัดลอก / วาง\n Enter          | บันทึกและปิด'
        ),
        'msg_success': "ส่งออกธนาคารเสียง '{}' เป็นไฟล์ zip สำเร็จแล้ว!",
        'err_no_folder': "ไม่พบโฟลเดอร์ '子音部・濁音部フォルダ' และ 'oto.ini' ในเอกสาร!",
        'err_admin_cancel': 'สิทธิ์ผู้ดูแลระบบถูกยกเลิกหรือคัดลอกไม่สำเร็จ',
        'err_ou': 'เขียนลงโฟลเดอร์ OpenUTAU ไม่สำเร็จ:\n{}',
        'err_utau': 'เขียนลงโฟลเดอร์ UTAU ไม่สำเร็จ:\n{}',
        'err_export': 'สร้างไฟล์ zip ไม่สำเร็จ:\n{}',
        'decide': 'ใช้',
        'settings_title': 'การตั้งค่าและการส่งออก',
        'target_set': '[ ตั้งค่าเป้าหมายการส่งออก ]',
        'ou_label': 'สำหรับ OpenUTAU (ส่งออกอัตโนมัติ)',
        'utau_label': 'สำหรับ UTAU แบบคลาสสิก (ส่งออกอัตโนมัติ)',
        'export_label': 'ไดเรกทอรีส่งออกเริ่มต้น (zip)',
        'update_btn': 'ตรวจสอบการอัปเดต',
        'update_notes_btn': 'ตรวจสอบบันทึกประจำรุ่นตามภาษา',
        'update_check': 'ตรวจสอบการอัปเดต',
        'warning': 'คำเตือน',
        'uptodate': 'คุณใช้เวอร์ชันล่าสุดอยู่แล้ว!',
        'not_found_zip': (
            'พบเวอร์ชันใหม่ ({version}) แต่ไม่พบไฟล์อัปเดตที่ระบุ (utaun.zip)'
        ),
        'ask_update': 'พบเวอร์ชันใหม่ ({version})\nต้องการอัปเดตหรือไม่',
    },
}


def generate_vowel_data(v_char, height, duration=1.0, sr=44100):
  t = np.linspace(0, duration, int(sr * duration), endpoint=False)
  base_recipes = {
      'あ': [800, 1200],
      'い': [300, 2500],
      'う': [300, 1200],
      'え': [500, 1900],
      'お': [500, 800],
      'ん': [250, 600],
  }
  base = base_recipes.get(v_char, [800, 1200])
  base_height = 200.0
  diff = max(0, height - base_height)
  shift_rate = 0.25
  targets = [val + (diff * shift_rate) for val in base]
  signal = np.zeros_like(t)
  max_harmonic = int(sr / 2 / height)
  for n in range(1, min(max_harmonic, 30)):
    freq = height * n
    amp = sum((np.exp(-(freq - c) ** 2 / 50000) for c in targets))
    signal += amp / (n**1.2) * np.sin(2 * np.pi * freq * t)
  if np.max(np.abs(signal)) > 0:
    signal = signal / np.max(np.abs(signal)) * 0.7
  return (signal * 32767).astype(np.int16)


def run_generator(
    char_name, author, readme_content, icon_path, height, encoding, l, export_config
):
  try:
    consonant_folder = os.path.join(BASE_PATH, '子音部・濁音部フォルダ')
    if not os.path.exists(consonant_folder) or not os.path.exists(
        os.path.join(BASE_PATH, 'oto.ini')
    ):
      return (False, l['err_no_folder'])

    save_dir = tempfile.mkdtemp(prefix=f'_temp_{char_name}_')
    char_folder = os.path.join(save_dir, char_name)
    os.makedirs(char_folder, exist_ok=True)

    if icon_path and os.path.exists(icon_path):
      with Image.open(icon_path) as img:
        w, h = img.size
        size = min(w, h)
        left, top = ((w - size) / 2, (h - size) / 2)
        img = (
            img.crop((left, top, left + size, top + size))
            .resize((100, 100), Image.Resampling.LANCZOS)
        )
        img.save(os.path.join(char_folder, 'icon.bmp'), dpi=(100, 100))
        img.convert('RGB').save(os.path.join(char_folder, 'icon.jpg'), quality=95)

    with open(
        os.path.join(char_folder, 'character.txt'), 'w', encoding=encoding, errors='ignore'
    ) as f:
      f.write(f'name={char_name}\nimage=icon.jpg\nauthor={author}')
    with open(
        os.path.join(char_folder, 'readme.txt'), 'w', encoding=encoding, errors='ignore'
    ) as f:
      f.write(readme_content)

    v_dict = {v: generate_vowel_data(v, height) for v in 'あいうえおん'}
    v_roma_map = {'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o', 'ん': 'nn'}

    for v, data in v_dict.items():
      for name in [v, v_roma_map[v]]:
        with wave.open(os.path.join(char_folder, f'{name}.wav'), 'w') as f:
          f.setnchannels(1)
          f.setsampwidth(2)
          f.setframerate(44100)
          f.writeframes(data.tobytes())

    mapping = {
        'm': ('ん', 4410, 'まみむめも'),
        'n': ('ん', 2205, 'なにぬねの'),
        'y': ('い', 4410, 'やゆよ'),
        'w': ('う', 4410, 'わを'),
    }
    for row, (base_v, length, hira_row) in mapping.items():
      sub = v_dict[base_v][:length]
      targets = (
          [('あ', 'a', 0), ('い', 'i', 1), ('う', 'u', 2), ('え', 'e', 3), ('お', 'o', 4)]
          if row in 'mn'
          else [('あ', 'a', 0), ('う', 'u', 1), ('お', 'o', 2)]
          if row == 'y'
          else [('あ', 'a', 0), ('お', 'o', 1)]
      )
      for v_hira, v_roma, idx in targets:
        combined = np.concatenate([sub, v_dict[v_hira]])
        for name in [f'{row}{v_roma}', hira_row[idx]]:
          with wave.open(os.path.join(char_folder, f'{name}.wav'), 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(44100)
            f.writeframes(combined.tobytes())

    search_list = [
        ('ka', 'か', 'ka', 'か'),
        ('ki', 'き', 'ki', 'き'),
        ('ku', 'く', 'ku', 'く'),
        ('ke', 'け', 'ke', 'け'),
        ('ko', 'こ', 'ko', 'こ'),
        ('sa', 'さ', 'sa', 'さ'),
        ('si', 'し', 'shi', 'し'),
        ('su', 'す', 'su', 'す'),
        ('se', 'せ', 'se', 'せ'),
        ('so', 'そ', 'so', 'そ'),
        ('ta', 'た', 'ta', 'た'),
        ('ti', 'ち', 'chi', 'ち'),
        ('tu', 'つ', 'tsu', 'つ'),
        ('te', 'て', 'te', 'て'),
        ('to', 'と', 'to', 'と'),
        ('na', 'な', 'na', 'な'),
        ('ni', 'に', 'ni', 'に'),
        ('nu', 'ぬ', 'nu', 'ぬ'),
        ('ne', 'ね', 'ne', 'ね'),
        ('no', 'の', 'no', 'の'),
        ('ha', 'は', 'ha', 'は'),
        ('hi', 'ひ', 'hi', 'ひ'),
        ('hu', 'ふ', 'hu', 'ふ'),
        ('he', 'へ', 'he', 'へ'),
        ('ho', 'ほ', 'ho', 'ほ'),
        ('ma', 'ま', 'ma', 'ま'),
        ('mi', 'み', 'mi', 'み'),
        ('mu', 'む', 'mu', 'む'),
        ('me', 'め', 'me', 'め'),
        ('mo', 'も', 'mo', 'も'),
        ('ya', 'や', 'ya', 'や'),
        ('yu', 'ゆ', 'yu', 'ゆ'),
        ('yo', 'よ', 'yo', 'よ'),
        ('ra', 'ら', 'ra', 'ら'),
        ('ri', 'り', 'ri', 'り'),
        ('ru', 'る', 'ru', 'る'),
        ('re', 'れ', 're', 'れ'),
        ('ro', 'ろ', 'ro', 'ろ'),
        ('wa', 'わ', 'wa', 'わ'),
        ('wo', 'を', 'wo', 'を'),
        ('ga', 'が', 'ga', 'が'),
        ('gi', 'ぎ', 'gi', 'ぎ'),
        ('gu', 'ぐ', 'gu', 'ぐ'),
        ('ge', 'げ', 'ge', 'げ'),
        ('go', 'ご', 'go', 'ご'),
        ('za', 'ざ', 'za', 'ざ'),
        ('zi', 'じ', 'ji', 'じ'),
        ('zu', 'ず', 'zu', 'ず'),
        ('ze', 'ぜ', 'ze', 'ぜ'),
        ('zo', 'ぞ', 'zo', 'ぞ'),
        ('da', 'だ', 'da', 'だ'),
        ('di', 'ぢ', 'di', 'ぢ'),
        ('du', 'づ', 'du', 'づ'),
        ('de', 'で', 'de', 'de'),
        ('do', 'ど', 'do', 'ど'),
        ('ba', 'ば', 'ba', 'ば'),
        ('bi', 'び', 'bi', 'び'),
        ('bu', 'ぶ', 'bu', 'ぶ'),
        ('be', 'べ', 'be', 'べ'),
        ('bo', 'ぼ', 'bo', 'ぼ'),
        ('pa', 'ぱ', 'pa', 'ぱ'),
        ('pi', 'ぴ', 'pi', 'ぴ'),
        ('pu', 'ぷ', 'pu', 'ぷ'),
        ('pe', 'ぺ', 'pe', 'ぺ'),
        ('po', 'ぽ', 'po', 'ぽ'),
    ]
    for roma_no_conon, hira_target, roma_with_conon, hira_row in search_list:
      c_data = None
      for f_name in os.listdir(consonant_folder):
        if (
            roma_with_conon in f_name or hira_target in f_name
        ) and f_name.endswith('.wav'):
          with wave.open(os.path.join(consonant_folder, f_name), 'rb') as wav:
            c_data = np.frombuffer(
                wav.readframes(wav.getnframes()), dtype=np.int16
            )
          break
      if c_data is not None:
        v_char_map = {'a': 'あ', 'i': 'い', 'u': 'う', 'e': 'え', 'o': 'お'}
        v_key = roma_with_conon[-1]
        v_hira = v_char_map.get(v_key, 'あ')
        combined = np.concatenate([c_data, v_dict[v_hira]])
        save_names = set([roma_with_conon, hira_target])
        for name in save_names:
          with wave.open(os.path.join(char_folder, f'{name}.wav'), 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(44100)
            f.writeframes(combined.tobytes())

    current_ini = os.path.join(BASE_PATH, 'oto.ini')
    if os.path.exists(current_ini):
      shutil.copy(current_ini, os.path.join(char_folder, 'oto.ini'))

    def copy_with_admin_if_needed(src, target_dir, char_name):
      dest_folder = os.path.join(target_dir, char_name)
      is_protected = (
          'Program Files' in target_dir
          or 'Windows' in target_dir
          or 'OneDrive' in target_dir
          or 'ドキュメント' in target_dir
          or 'Documents' in target_dir
      )

      if is_protected:
        temp_staging = os.path.join(
            tempfile.gettempdir(), f'utaun_staging_{char_name}'
        )
        if os.path.exists(temp_staging):
          shutil.rmtree(temp_staging)
        shutil.copytree(src, temp_staging)

        ps_command = (
            f"Copy-Item -Path '{temp_staging}' -Destination '{target_dir}'"
            f" -Recurse -Force; Remove-Item -Path '{temp_staging}' -Recurse"
            ' -Force'
        )
        cmd = [
            'powershell',
            '-Command',
            (
                'Start-Process powershell -ArgumentList'
                f' "-Command {ps_command}" -Verb RunAs -Wait'
            ),
        ]
        result_proc = subprocess.run(cmd)
        if result_proc.returncode != 0:
          return False, l['err_admin_cancel']
      else:
        if os.path.exists(dest_folder):
          shutil.rmtree(dest_folder)
        shutil.copytree(src, dest_folder)
      return True, ''

    if export_config.get('openutau_enabled', False):
      try:
        ou_path = export_config.get('openutau_path', '').strip()
        target_dir = (
            ou_path if ou_path and os.path.exists(ou_path) else BASE_PATH
        )
        success, err_msg = copy_with_admin_if_needed(
            char_folder, target_dir, char_name
        )
        if not success:
          return (False, err_msg)
      except Exception as e:
        return (False, l['err_ou'].format(e))

    if export_config.get('utau_enabled', False):
      try:
        utau_path = export_config.get('utau_path', '').strip()
        target_dir = (
            utau_path if utau_path and os.path.exists(utau_path) else BASE_PATH
        )
        success, err_msg = copy_with_admin_if_needed(
            char_folder, target_dir, char_name
        )
        if not success:
          return (False, err_msg)
      except Exception as e:
        return (False, l['err_utau'].format(e))

    try:
      custom_export_path = export_config.get('export_path', '').strip()
      default_export_dir = (
          custom_export_path
          if custom_export_path and os.path.exists(custom_export_path)
          else BASE_PATH
      )

      zip_base_name = os.path.join(default_export_dir, char_name)
      shutil.make_archive(zip_base_name, 'zip', save_dir, char_name)
    except Exception as e:
      return (False, l['err_export'].format(e))

    if os.path.exists(save_dir):
      shutil.rmtree(save_dir)

    return (True, char_name)
  except Exception as e:
    return (False, str(e))


class UtaunUI:

  def __init__(self, root):
    self.root = root
    self.root.title(f'Utaun {CURRENT_VERSION}')
    try:
      self.root.iconbitmap(resource_path('919c3668.ico'))
    except:
      pass
    window_width = 600
    window_height = 650

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)

    self.root.geometry(f'{window_width}x{window_height}+{x}+{y}')

    self.settings = self.load_settings()
    self.lang_var = tk.StringVar(
        value=self.settings.get('lang', '🇯🇵 日本語')
    )
    self.encoding_var = tk.StringVar(
        value=self.settings.get('encoding', 'shift_jis')
    )
    self.theme_var = tk.StringVar(value=self.settings.get('theme', 'light'))
    self.sc_enabled = tk.BooleanVar(
        value=self.settings.get('sc_enabled', True)
    )

    self.ou_enabled_var = tk.BooleanVar(
        value=self.settings.get('ou_enabled', True)
    )
    self.ou_path_var = tk.StringVar(value=self.settings.get('ou_path', ''))

    self.utau_enabled_var = tk.BooleanVar(
        value=self.settings.get('utau_enabled', False)
    )
    self.utau_path_var = tk.StringVar(value=self.settings.get('utau_path', ''))

    self.export_path_var = tk.StringVar(
        value=self.settings.get('export_path', '')
    )

    self.icon_path = ''

    self.header = tk.Frame(root)
    self.header.pack(fill='x', padx=15, pady=15)
    self.title_lbl = tk.Label(
        self.header, text='Utaun', font=('MS Gothic', 28, 'bold')
    )
    self.title_lbl.pack(side='left')

    self.settings_btn = tk.Button(
        self.header,
        text='⚙',
        command=self.open_settings,
        relief='flat',
        font=('Arial', 18),
    )
    self.settings_btn.pack(side='right')

    self.lb_name = tk.Label(root, font=('MS Gothic', 12, 'bold'))
    self.lb_name.pack(pady=(5, 0))

    self.name_wrap = tk.Frame(root, bd=1)
    self.name_wrap.pack(pady=3)
    self.name_ent = tk.Entry(
        self.name_wrap, width=30, font=('MS Gothic', 11), relief='flat', bd=0
    )
    self.name_ent.pack(padx=1, pady=1)

    self.lb_auth = tk.Label(root, font=('MS Gothic', 12, 'bold'))
    self.lb_auth.pack(pady=(5, 0))

    self.auth_wrap = tk.Frame(root, bd=1)
    self.auth_wrap.pack(pady=3)
    self.auth_ent = tk.Entry(
        self.auth_wrap, width=30, font=('MS Gothic', 11), relief='flat', bd=0
    )
    self.auth_ent.pack(padx=1, pady=1)

    self.lb_desc = tk.Label(root, font=('MS Gothic', 12, 'bold'))
    self.lb_desc.pack(pady=(5, 0))

    self.desc_wrap = tk.Frame(root, bd=1)
    self.desc_wrap.pack(pady=3)
    self.desc_txt = tk.Text(
        self.desc_wrap, width=40, height=6, font=('MS Gothic', 11), relief='flat', bd=0
    )
    self.desc_txt.pack(padx=1, pady=1)

    self.lb_enc = tk.Label(root, font=('MS Gothic', 12, 'bold'))
    self.lb_enc.pack(pady=(5, 0))
    self.enc_frame = tk.Frame(root)
    self.enc_frame.pack(pady=2)
    self.rb_sjis = tk.Radiobutton(
        self.enc_frame,
        text='Shift-JIS',
        variable=self.encoding_var,
        value='shift_jis',
        font=('MS Gothic', 9),
        command=self.save_current_settings,
    )
    self.rb_sjis.pack(side='left', padx=10)
    self.rb_utf8 = tk.Radiobutton(
        self.enc_frame,
        text='UTF-8',
        variable=self.encoding_var,
        value='utf-8',
        font=('MS Gothic', 9),
        command=self.save_current_settings,
    )
    self.rb_utf8.pack(side='left', padx=10)

    self.lb_icon = tk.Label(root, text='ICON', font=('MS Gothic', 12, 'bold'))
    self.lb_icon.pack(pady=(5, 0))

    self.icon_wrap = tk.Frame(root, bd=1)
    self.icon_wrap.pack(pady=3)
    self.icon_btn = tk.Button(
        self.icon_wrap,
        text='SELECT IMAGE',
        command=self.select_file,
        relief='flat',
        bd=0,
        font=('MS Gothic', 10),
    )
    self.icon_btn.pack(padx=1, pady=1)

    self.lb_height = tk.Label(root, font=('MS Gothic', 12, 'bold'))
    self.lb_height.pack(pady=(5, 0))
    self.height_sc = tk.Scale(
        root, from_=100, to=600, orient='horizontal', highlightthickness=0, length=250
    )
    self.height_sc.set(self.settings.get('height', 311))
    self.height_sc.pack()

    self.listen_wrap = tk.Frame(root, bd=1)
    self.listen_wrap.pack(pady=10)
    self.listen_btn = tk.Button(
        self.listen_wrap,
        text='♪',
        command=self.play_demo,
        relief='flat',
        bd=0,
        width=12,
        font=('MS Gothic', 10),
    )
    self.listen_btn.pack(padx=1, pady=1)

    self.gen_wrap = tk.Frame(root, bd=1)
    self.gen_wrap.pack(pady=15)
    self.gen_btn = tk.Button(
        self.gen_wrap,
        text='',
        command=self.start,
        font=('MS Gothic', 14, 'bold'),
        padx=25,
        pady=10,
        relief='flat',
        bd=0,
    )
    self.gen_btn.pack(padx=1, pady=1)

    self.root.bind(
        '<Control-Return>',
        lambda e: self.start() if self.sc_enabled.get() else None,
    )
    self.root.bind(
        '<Control-p>',
        lambda e: self.play_demo() if self.sc_enabled.get() else None,
    )

    self.apply_theme()
    self.refresh_ui()

    self.root.after(1000, lambda: check_for_updates(silent=True))

  def load_settings(self):
    if os.path.exists(CONFIG_PATH):
      try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
          return json.load(f)
      except:
        return {}
    return {}

  def save_current_settings(self):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
      json.dump(
          {
              'lang': self.lang_var.get(),
              'height': self.height_sc.get(),
              'sc_enabled': self.sc_enabled.get(),
              'encoding': self.encoding_var.get(),
              'theme': self.theme_var.get(),
              'ou_enabled': self.ou_enabled_var.get(),
              'ou_path': self.ou_path_var.get(),
              'utau_enabled': self.utau_enabled_var.get(),
              'utau_path': self.utau_path_var.get(),
              'export_path': self.export_path_var.get(),
          },
          f,
      )

  def apply_theme(self):
    is_dark = self.theme_var.get() == 'dark'
    bg_color = '#1e1e1e' if is_dark else '#ffffff'
    fg_color = '#ffffff' if is_dark else '#000000'
    entry_bg = '#2d2d2d' if is_dark else '#ffffff'
    entry_fg = '#ffffff' if is_dark else '#000000'
    btn_bg = '#333333' if is_dark else '#f0f0f0'
    btn_fg = '#ffffff' if is_dark else '#000000'
    border_color = '#ffffff' if is_dark else '#7f7f7f'
    trough_color = '#2d2d2d' if is_dark else '#e0e0e0'
    scale_bg = '#1e1e1e' if is_dark else '#ffffff'

    self.root.configure(bg=bg_color)
    for widget in [self.header, self.enc_frame]:
      widget.configure(bg=bg_color)

    self.title_lbl.configure(bg=bg_color, fg=fg_color)
    self.settings_btn.configure(
        bg=btn_bg, fg=btn_fg, activebackground=btn_bg, activeforeground=btn_fg
    )

    for lbl in [
        self.lb_name,
        self.lb_auth,
        self.lb_desc,
        self.lb_enc,
        self.lb_icon,
        self.lb_height,
    ]:
      lbl.configure(bg=bg_color, fg=fg_color)

    for wrap in [
        self.name_wrap,
        self.auth_wrap,
        self.desc_wrap,
        self.icon_wrap,
        self.listen_wrap,
        self.gen_wrap,
    ]:
      wrap.configure(bg=border_color)

    for ent in [self.name_ent, self.auth_ent, self.desc_txt]:
      ent.configure(bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)

    for rb in [self.rb_sjis, self.rb_utf8]:
      rb.configure(
          bg=bg_color,
          fg=fg_color,
          activebackground=bg_color,
          activeforeground=fg_color,
          selectcolor=bg_color,
      )

    self.icon_btn.configure(bg=btn_bg, fg=btn_fg)
    self.height_sc.configure(
        bg=scale_bg,
        fg=fg_color,
        troughcolor=trough_color,
        activebackground=btn_bg,
        highlightthickness=0,
    )
    self.listen_btn.configure(bg=btn_bg, fg=btn_fg)
    self.gen_btn.configure(bg=btn_bg, fg=btn_fg)

  def refresh_ui(self):
    l = LANG_DATA.get(self.lang_var.get(), LANG_DATA['🇯🇵 日本語'])
    self.lb_name.config(text=l['name'])
    self.lb_auth.config(text=l['auth'])
    self.lb_desc.config(text=l['desc'])
    self.lb_height.config(text=l['height'])
    self.lb_enc.config(text=l['enc_set'])
    self.gen_btn.config(text=l['gen'])
    self.listen_btn.config(text=f"♪ {l['listen']}")

  def open_settings(self):
    top = tk.Toplevel(self.root)
    top.title('Settings & Exports')
    top.geometry('580x660')
    try:
      top.iconbitmap(resource_path('utaun.ico'))
    except:
      pass

    l = LANG_DATA.get(self.lang_var.get(), LANG_DATA['🇯🇵 日本語'])
    top.focus_set()

    canvas = tk.Canvas(top, highlightthickness=0)
    scrollbar = ttk.Scrollbar(top, orient='vertical', command=canvas.yview)
    scroll_frame = tk.Frame(canvas)

    scroll_frame.bind(
        '<Configure>',
        lambda e: canvas.configure(scrollregion=canvas.bbox('all')),
    )
    canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')

    def apply_settings_window_theme():
      is_dark = self.theme_var.get() == 'dark'
      t_bg = '#1e1e1e' if is_dark else '#ffffff'
      t_fg = '#ffffff' if is_dark else '#000000'
      btn_bg = '#333333' if is_dark else '#f0f0f0'
      btn_fg = '#ffffff' if is_dark else '#000000'
      border_init = '#ffffff' if is_dark else '#7f7f7f'
      guide_bg_init = '#2d2d2d' if is_dark else '#f0f0f0'

      top.configure(bg=t_bg)
      canvas.configure(bg=t_bg)
      scroll_frame.configure(bg=t_bg)

      for widget in scroll_frame.winfo_children():
        w_type = widget.winfo_class()
        try:
          if w_type in ('Label', 'Checkbutton', 'Radiobutton'):
            widget.configure(bg=t_bg, fg=t_fg, activebackground=t_bg, activeforeground=t_fg)
            if w_type in ('Checkbutton', 'Radiobutton'):
              widget.configure(selectcolor=t_bg)
          elif w_type == 'Frame':
            widget.configure(bg=t_bg)
            for child in widget.winfo_children():
              c_type = child.winfo_class()
              if c_type in ('Label', 'Checkbutton', 'Radiobutton'):
                child.configure(bg=t_bg, fg=t_fg, activebackground=t_bg, activeforeground=t_fg)
                if c_type in ('Checkbutton', 'Radiobutton'):
                  child.configure(selectcolor=t_bg)
              elif c_type == 'Button':
                child.configure(bg=btn_bg, fg=btn_fg, activebackground=btn_bg, activeforeground=btn_fg)
              elif c_type == 'Entry':
                child.configure(bg='#2d2d2d' if is_dark else '#ffffff', fg=t_fg, insertbackground=t_fg)
          elif w_type == 'Button':
            widget.configure(bg=btn_bg, fg=btn_fg, activebackground=btn_bg, activeforeground=btn_fg)
        except:
          pass

      try:
        sc_guide_wrap.configure(bg=border_init)
        sc_guide_lbl.configure(bg=guide_bg_init, fg=t_fg)
        decide_wrap.configure(bg=border_init)
        decide_btn.configure(bg=btn_bg, fg=btn_fg, activebackground=btn_bg, activeforeground=btn_fg)
      except:
        pass

    lbl_lang = tk.Label(
        scroll_frame,
        text=l['lang_set'],
        font=('MS Gothic', 10, 'bold'),
    )
    lbl_lang.pack(pady=(10, 2))
    cb = ttk.Combobox(
        scroll_frame,
        textvariable=self.lang_var,
        values=list(LANG_DATA.keys()),
        state='readonly',
    )
    cb.pack(pady=5)

    lbl_theme = tk.Label(
        scroll_frame,
        text=l['theme_set'],
        font=('MS Gothic', 10, 'bold'),
    )
    lbl_theme.pack(pady=(10, 2))
    theme_frame = tk.Frame(scroll_frame)
    theme_frame.pack(pady=5)
    rb_light = tk.Radiobutton(
        theme_frame,
        text=l['light'],
        variable=self.theme_var,
        value='light',
        command=lambda: on_theme_toggle('light'),
        font=('MS Gothic', 9),
    )
    rb_light.pack(side='left', padx=10)
    rb_dark = tk.Radiobutton(
        theme_frame,
        text=l['dark'],
        variable=self.theme_var,
        value='dark',
        command=lambda: on_theme_toggle('dark'),
        font=('MS Gothic', 9),
    )
    rb_dark.pack(side='left', padx=10)

    def on_theme_toggle(val):
      self.theme_var.set(val)
      self.apply_theme()
      apply_settings_window_theme()
      self.save_current_settings()

    def on_lang_change(e):
      self.lang_var.set(cb.get())
      self.refresh_ui()
      self.save_current_settings()
      top.destroy()
      self.open_settings()

    cb.bind('<<ComboboxSelected>>', on_lang_change)

    chk_sc = tk.Checkbutton(
        scroll_frame,
        text=l['sc_set'],
        variable=self.sc_enabled,
        command=self.save_current_settings,
        font=('MS Gothic', 9),
    )
    chk_sc.pack(pady=5)

    update_frame_btn = tk.Frame(scroll_frame)
    update_frame_btn.pack(pady=10)
    btn_update = tk.Button(
        update_frame_btn,
        text=l.get('update_btn', 'アップデート確認'),
        command=lambda: check_for_updates(silent=False),
        font=('MS Gothic', 9, 'bold'),
        relief='flat',
    )
    btn_update.pack(side='left', padx=5, pady=2)
    btn_notes = tk.Button(
        update_frame_btn,
        text=l.get('update_notes_btn', '各言語のアップデート内容を確認'),
        command=lambda: show_update_notes_window(self.root),
        font=('MS Gothic', 9, 'bold'),
        relief='flat',
    )
    btn_notes.pack(side='left', padx=5, pady=2)

    lbl_target = tk.Label(
        scroll_frame,
        text=l['target_set'],
        font=('MS Gothic', 10, 'bold'),
    )
    lbl_target.pack(pady=(15, 5))

    chk_ou = tk.Checkbutton(
        scroll_frame,
        text=l['ou_label'],
        variable=self.ou_enabled_var,
        command=self.save_current_settings,
        font=('MS Gothic', 9, 'bold'),
    )
    chk_ou.pack(anchor='w', padx=20)
    ou_frame = tk.Frame(scroll_frame)
    ou_frame.pack(fill='x', padx=20, pady=2)
    ent_ou = tk.Entry(
        ou_frame, textvariable=self.ou_path_var, width=32, font=('MS Gothic', 9)
    )
    ent_ou.pack(side='left', padx=(0, 5))
    btn_ou = tk.Button(
        ou_frame,
        text='📁',
        command=lambda: [
            self.ou_path_var.set(filedialog.askdirectory()),
            self.save_current_settings(),
        ],
        font=('MS Gothic', 8),
    )
    btn_ou.pack(side='left')

    chk_utau = tk.Checkbutton(
        scroll_frame,
        text=l['utau_label'],
        variable=self.utau_enabled_var,
        command=self.save_current_settings,
        font=('MS Gothic', 9, 'bold'),
    )
    chk_utau.pack(anchor='w', padx=20, pady=(10, 0))
    utau_frame = tk.Frame(scroll_frame)
    utau_frame.pack(fill='x', padx=20, pady=2)
    ent_utau = tk.Entry(
        utau_frame,
        textvariable=self.utau_path_var,
        width=32,
        font=('MS Gothic', 9),
    )
    ent_utau.pack(side='left', padx=(0, 5))
    btn_utau = tk.Button(
        utau_frame,
        text='📁',
        command=lambda: [
            self.utau_path_var.set(filedialog.askdirectory()),
            self.save_current_settings(),
        ],
        font=('MS Gothic', 8),
    )
    btn_utau.pack(side='left')

    lbl_export = tk.Label(
        scroll_frame,
        text=l['export_label'],
        font=('MS Gothic', 9, 'bold'),
    )
    lbl_export.pack(anchor='w', padx=20, pady=(10, 0))
    export_frame = tk.Frame(scroll_frame)
    export_frame.pack(fill='x', padx=20, pady=2)
    ent_export = tk.Entry(
        export_frame,
        textvariable=self.export_path_var,
        width=32,
        font=('MS Gothic', 9),
    )
    ent_export.pack(side='left', padx=(0, 5))
    btn_export = tk.Button(
        export_frame,
        text='📁',
        command=lambda: [
            self.export_path_var.set(filedialog.askdirectory()),
            self.save_current_settings(),
        ],
        font=('MS Gothic', 8),
    )
    btn_export.pack(side='left')

    is_dark_initial = self.theme_var.get() == 'dark'
    border_init = '#ffffff' if is_dark_initial else '#7f7f7f'

    sc_guide_wrap = tk.Frame(scroll_frame, bd=1, bg=border_init)
    sc_guide_wrap.pack(pady=15, fill='x', padx=20)
    sc_guide_lbl = tk.Label(
        sc_guide_wrap,
        text=l['sc_list'],
        font=('Consolas', 9),
        justify='left',
        padx=10,
        pady=10,
        relief='flat',
        bd=0,
    )
    sc_guide_lbl.pack(padx=1, pady=1, fill='x')

    def on_decide():
      self.save_current_settings()
      top.destroy()

    decide_wrap = tk.Frame(scroll_frame, bd=1, bg=border_init)
    decide_wrap.pack(pady=10)
    decide_btn = tk.Button(
        decide_wrap,
        text=l['decide'],
        command=on_decide,
        font=('MS Gothic', 10, 'bold'),
        width=12,
        relief='flat',
        bd=0,
    )
    decide_btn.pack(padx=1, pady=1)

    apply_settings_window_theme()
    top.bind('<Return>', lambda e: on_decide())

  def play_demo(self):
    try:
      data = generate_vowel_data('あ', self.height_sc.get(), duration=0.5)

      with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
        tmp_name = tmp.name

      with wave.open(tmp_name, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(data.tobytes())

      winsound.PlaySound(tmp_name, winsound.SND_FILENAME)

      try:
        os.remove(tmp_name)
      except:
        pass
    except Exception as e:
      messagebox.showerror('再生エラー', f'試聴の再生に失敗しました:\n{e}')

  def select_file(self):
    path = filedialog.askopenfilename()
    if path:
      self.icon_path = path
      self.icon_btn.config(text='SELECTED')

  def start(self):
    raw_name = self.name_ent.get().strip()
    name = raw_name or 'NewVoice'
    raw_auth = self.auth_ent.get().strip()
    author = raw_auth if raw_auth else 'User'
    self.save_current_settings()
    l = LANG_DATA.get(self.lang_var.get(), LANG_DATA['🇯🇵 日本語'])
    self.gen_btn.config(text='...', state='disabled')
    self.root.update()

    export_config = {
        'openutau_enabled': self.ou_enabled_var.get(),
        'openutau_path': self.ou_path_var.get(),
        'utau_enabled': self.utau_enabled_var.get(),
        'utau_path': self.utau_path_var.get(),
        'export_path': self.export_path_var.get(),
    }

    success, result = run_generator(
        name,
        author,
        self.desc_txt.get('1.0', 'end-1c'),
        self.icon_path,
        self.height_sc.get(),
        self.encoding_var.get(),
        l,
        export_config,
    )

    self.gen_btn.config(text=l['gen'], state='normal')
    if success:
      messagebox.showinfo('Success', l['msg_success'].format(result))
    else:
      messagebox.showerror('Error', result)


if __name__ == '__main__':
  update_documents_folder()

  root = tk.Tk()
  app = UtaunUI(root)
  root.mainloop()
