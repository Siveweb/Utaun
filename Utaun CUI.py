import os
import tempfile
import wave
import shutil
import unicodedata
import numpy as np
from PIL import Image

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

def generate_vowel_data(v_char, height, duration=1.0, sr=44100):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    base_recipes = {
        'あ': [800, 1200],
        'い': [300, 2200],
        'う': [300, 900],
        'え': [500, 1700],
        'お': [400, 800],
        'ん': [300, 800],
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

def run_generator(c_name, author, readme, height, text_encoding='shift_jis'):
    try:
        c_name = unicodedata.normalize('NFC', c_name)
        author = unicodedata.normalize('NFC', author)
        readme = unicodedata.normalize('NFC', readme)

        consonant_folder = os.path.join(BASE_PATH, '子音部・濁音部フォルダ')
        current_ini = os.path.join(BASE_PATH, 'oto.ini')
        if not os.path.exists(consonant_folder) or not os.path.exists(current_ini):
            return False, "「子音部・濁音部フォルダ」または「oto.ini」がスクリプトと同じ場所にありません。"

        save_dir = tempfile.mkdtemp(prefix=f'_temp_{c_name}_')
        char_folder = os.path.join(save_dir, c_name)
        os.makedirs(char_folder, exist_ok=True)

        icon_path = None
        supported_extensions = ('.png', '.jpg', '.jpeg', '.webp')
        for f_name in os.listdir(BASE_PATH):
            f_name_nfc = unicodedata.normalize('NFC', f_name)
            if f_name_nfc.lower().endswith(supported_extensions):
                icon_path = os.path.join(BASE_PATH, f_name)
                break

        if icon_path:
            with Image.open(icon_path) as img:
                w, h = img.size
                size = min(w, h)
                left = (w - size) / 2
                top = (h - size) / 2
                img = img.crop((left, top, left + size, top + size)).resize((100, 100), Image.Resampling.LANCZOS)
                img.save(os.path.join(char_folder, 'icon.bmp'), dpi=(100, 100))
                img.convert('RGB').save(os.path.join(char_folder, 'icon.jpg'), quality=95)
        
        with open(os.path.join(char_folder, 'character.txt'), 'w', encoding=text_encoding, errors='replace') as f:
            f.write(f'name={c_name}\nimage=icon.jpg\nauthor={author}')
        with open(os.path.join(char_folder, 'readme.txt'), 'w', encoding=text_encoding, errors='replace') as f:
            f.write(readme)

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
            ('ka', 'か', 'ka', 'か'), ('ki', 'き', 'ki', 'き'), ('ku', 'く', 'ku', 'く'), ('ke', 'け', 'ke', 'け'), ('ko', 'こ', 'ko', 'こ'),
            ('sa', 'さ', 'sa', 'さ'), ('si', 'し', 'shi', 'し'), ('su', 'す', 'su', 'す'), ('se', 'せ', 'se', 'せ'), ('so', 'そ', 'so', 'そ'),
            ('ta', 'た', 'ta', 'た'), ('ti', 'ち', 'chi', 'ち'), ('tu', 'つ', 'tsu', 'つ'), ('te', 'て', 'te', 'て'), ('to', 'と', 'to', 'と'),
            ('na', 'な', 'na', 'な'), ('ni', 'に', 'ni', 'に'), ('nu', 'ぬ', 'nu', 'ぬ'), ('ne', 'ね', 'ne', 'ね'), ('no', 'の', 'no', 'の'),
            ('ha', 'は', 'ha', 'は'), ('hi', 'ひ', 'hi', 'ひ'), ('hu', 'ふ', 'hu', 'ふ'), ('he', 'へ', 'he', 'へ'), ('ho', 'ほ', 'ho', 'ほ'),
            ('ma', 'ま', 'ma', 'ま'), ('mi', 'み', 'mi', 'み'), ('mu', 'む', 'mu', 'む'), ('me', 'め', 'me', 'め'), ('mo', 'も', 'mo', 'も'),
            ('ya', 'や', 'ya', 'や'), ('yu', 'ゆ', 'yu', 'ゆ'), ('yo', 'よ', 'yo', 'よ'),
            ('ra', 'ら', 'ra', 'ら'), ('ri', 'り', 'ri', 'り'), ('ru', 'る', 'ru', 'る'), ('re', 'れ', 're', 'れ'), ('ro', 'ろ', 'ro', 'ろ'),
            ('wa', 'わ', 'wa', 'わ'), ('wo', 'を', 'wo', 'を'),
            ('ga', 'が', 'ga', 'が'), ('gi', 'ぎ', 'gi', 'ぎ'), ('gu', 'ぐ', 'gu', 'ぐ'), ('ge', 'げ', 'ge', 'げ'), ('go', 'ご', 'go', 'ご'),
            ('za', 'ざ', 'za', 'ざ'), ('zi', 'じ', 'ji', 'じ'), ('zu', 'ず', 'zu', 'ず'), ('ze', 'ぜ', 'ze', 'ぜ'), ('zo', 'ぞ', 'zo', 'ぞ'),
            ('da', 'だ', 'da', 'だ'), ('di', 'ぢ', 'di', 'ぢ'), ('du', 'づ', 'du', 'づ'), ('de', 'で', 'de', 'de'), ('do', 'ど', 'do', 'ど'),
            ('ba', 'ば', 'ba', 'ば'), ('bi', 'び', 'bi', 'び'), ('bu', 'ぶ', 'bu', 'ぶ'), ('be', 'べ', 'be', 'べ'), ('bo', 'ぼ', 'bo', 'ぼ'),
            ('pa', 'ぱ', 'pa', 'ぱ'), ('pi', 'ぴ', 'pi', 'ぴ'), ('pu', 'ぷ', 'pu', 'ぷ'), ('pe', 'ぺ', 'pe', 'ぺ'), ('po', 'ぽ', 'po', 'ぽ')
        ]
        
        for roma_no_conon, hira_target, roma_with_conon, hira_row in search_list:
            c_data = None
            for f_name in os.listdir(consonant_folder):
                f_name_nfc = unicodedata.normalize('NFC', f_name)
                if (roma_with_conon in f_name_nfc or hira_target in f_name_nfc) and f_name_nfc.endswith('.wav'):
                    with wave.open(os.path.join(consonant_folder, f_name), 'rb') as wav:
                        c_data = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16)
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

        shutil.copy(current_ini, os.path.join(char_folder, 'oto.ini'))

        zip_base_name = os.path.join(BASE_PATH, c_name)
        shutil.make_archive(zip_base_name, 'zip', save_dir, c_name)

        if os.path.exists(save_dir):
            shutil.rmtree(save_dir)
        return True, c_name
    except Exception as e:
        return False, str(e)

if __name__ == '__main__':
    print("=== Utaun CUI Generator ===")
    
    # スマホ環境（EOFError対策）で入力を安全に受け取る
    try:
        c_name = input("キャラクター名 (Name) [NewVoice]: ").strip() or "NewVoice"
    except (EOFError, KeyboardInterrupt):
        c_name = "NewVoice"
        print("入力が検知されないため、デフォルト値 'NewVoice' を使用します。")

    try:
        author = input("作者名 (Author) [User]: ").strip() or "User"
    except (EOFError, KeyboardInterrupt):
        author = "User"

    try:
        readme = input("説明文 (Readme) [Generated via CUI]: ").strip() or "Generated via CUI"
    except (EOFError, KeyboardInterrupt):
        readme = "Generated via CUI"

    try:
        height_input = input("音の高さ (Height Hz) [475]: ").strip()
        height = int(height_input) if height_input.isdigit() else 475
    except (EOFError, KeyboardInterrupt):
        height = 475

    try:
        enc_input = input("文字エンコード (1: shift_jis, 2: utf-8) [1]: ").strip()
        text_encoding = 'utf-8' if enc_input == '2' else 'shift_jis'
    except (EOFError, KeyboardInterrupt):
        text_encoding = 'shift_jis'
    
    print("\n音声データおよびパッケージを生成中...")
    success, msg = run_generator(c_name, author, readme, height, text_encoding)
    
    if success:
        print(f"\n[成功] 「{msg}」のZIP出力が完了しました！（エンコード: {text_encoding}）")
    else:
        print(f"\n[エラー] {msg}")
