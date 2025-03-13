# SMPTE LTC Generator

SMPTE標準に準拠したLTC（Linear Timecode）を生成するためのPythonツールです。様々なフレームレート（24, 25, 29.97, 30, 59.94, 60fps）でLTCを生成し、WAVファイルとして出力できます。

## 機能

- SMPTE標準のフレームレート（24, 25, 29.97, 30, 59.94, 60fps）をサポート
- ドロップフレームとノンドロップフレームのタイムコードをサポート（29.97fpsと59.94fps用）
- 時間、分、秒、フレームを指定してLTCを生成
- 現在の時刻からLTCを生成
- 生成したLTCを音声ファイル（WAV）として出力
- ユーザービットデータのサポート（日付、タイムゾーン、リール番号、カメラIDなど）
- ユーザービットフィールド1のサポート（4ビット: 0-15）

## インストール

必要なパッケージをインストールします：

```bash
pip install -r requirements.txt
```

## 使い方

### コマンドライン

```bash
# デフォルト設定（30fps、ノンドロップフレーム、5秒間のLTC）
python ltc_generator.py

# フレームレートを指定（24fps）
python ltc_generator.py --fps 24

# ドロップフレームタイムコード（29.97fps）
python ltc_generator.py --fps 29.97 --drop-frame

# ノンドロップフレームタイムコード（30fps）を明示的に指定
python ltc_generator.py --fps 30 --non-drop-frame

# タイムコードを指定（01:30:45:10）
python ltc_generator.py --hours 1 --minutes 30 --seconds 45 --frames 10

# 出力ファイル名を指定
python ltc_generator.py --output my_ltc.wav

# 現在の時刻からLTCを生成
python ltc_generator.py --current-time

# 生成するLTCの長さを指定（10秒）
python ltc_generator.py --duration 10.0

# ユーザービットデータを指定
python ltc_generator.py --date 2024-03-11 --timezone UTC+9 --reel 1 --camera CAM1

# カスタムユーザーグループを指定
python ltc_generator.py --user-group1 123 --user-group2 45 --user-group3 67 --user-group4 89

# ユーザービットフィールド1を指定（値: 10）
python ltc_generator.py --user-bits-field1 10

# フレームレートとユーザービットフィールド1を指定
python ltc_generator.py --fps 30 --user-bits-field1 15
```

### Pythonコードとして

```python
from ltc_generator import LTCGenerator

# ユーザービットデータを設定
user_bits = {
    'date': '2024-03-11',      # 撮影日
    'timezone': 'UTC+9',       # タイムゾーン
    'reel_number': 1,          # リール番号
    'camera_id': 'CAM1',       # カメラID
    'groups': [0, 0, 0, 0],    # カスタムユーザーグループ
    'binary_groups': [0] * 8,   # バイナリグループフラグ
    'user_bits_field1': 10      # ユーザービットフィールド1
}

# LTCジェネレーターを初期化（フレームレート: 29.97fps、ドロップフレーム）
ltc_gen = LTCGenerator(fps=29.97, use_drop_frame=True, user_bits=user_bits)

# LTCを生成（01:30:45:10、10秒間）
waveform = ltc_gen.generate_ltc(hours=1, minutes=30, seconds=45, frames=10, duration=10.0)

# ファイルに保存
ltc_gen.save_to_file(waveform, 'my_ltc.wav')

# ユーザービットデータを後から変更
ltc_gen.set_user_bits({
    'reel_number': 2,
    'camera_id': 'CAM2'
})

# ユーザービットフィールド1を後から変更
ltc_gen.set_user_bits_field1(15)
```

## オプション

### 基本オプション
- `--fps`: フレームレート（24, 25, 29.97, 30, 59.94, 60）
- `--sample-rate`: サンプルレート（デフォルト: 48000Hz）
- `--hours`: 時間（0-23）
- `--minutes`: 分（0-59）
- `--seconds`: 秒（0-59）
- `--frames`: フレーム（0-fps-1）
- `--duration`: 生成するLTCの長さ（秒）
- `--output`: 出力ファイル名
- `--current-time`: 現在の時刻を使用
- `--drop-frame`: ドロップフレームタイムコードを使用（29.97fpsと59.94fpsのみ有効）
- `--non-drop-frame`: ノンドロップフレームタイムコードを使用

### ユーザービットオプション
- `--date`: 日付（YYYY-MM-DD形式）
- `--timezone`: タイムゾーン（UTC+HH形式）
- `--reel`: リール番号（0-99）
- `--camera`: カメラID（最大4文字）
- `--user-group1`: ユーザーグループ1（0-255）
- `--user-group2`: ユーザーグループ2（0-255）
- `--user-group3`: ユーザーグループ3（0-255）
- `--user-group4`: ユーザーグループ4（0-255）
- `--user-bits-field1`: ユーザービットフィールド1（0-15）

## SMPTE標準について

このジェネレーターは以下のSMPTE標準に準拠しています：

- SMPTE 12M-1: タイムコードの規格
- SMPTE 12M-2: LTCのビットレイアウトと信号特性

### ドロップフレームとノンドロップフレーム

ドロップフレームタイムコードは、29.97fpsと59.94fpsで実時間との同期を維持するために使用されます。このタイムコードでは、毎分の最初の2フレームがスキップされます（ただし、10分の倍数の分を除く）。

### ユーザービットデータ

LTCのユーザービットは、タイムコード以外の追加情報を格納するために使用されます。以下のような情報を含めることができます：

- 撮影日付（月/日）
- タイムゾーン情報
- リール番号（0-99）
- カメラID（最大4文字）
- カスタムデータ（4つの8ビットグループ）
- バイナリグループフラグ（8ビット）

### ユーザービットフィールド1

ユーザービットフィールド1は、LTCフレーム内の4ビットフィールドで、以下の特徴があります：

- ビット位置：4-7ビット
- 値の範囲：0-15（4ビット）
- 用途：ユーザー定義の情報を格納（例：テイク番号、シーン番号など）

### LTCフレーム構造

80ビットのLTCフレームは以下の構造を持ちます：

- フレーム番号（0-3ビット）
- ユーザービットフィールド1（4-7ビット）
- フラグビット（ドロップフレーム、カラーフレーム）
- タイムコード情報（時、分、秒）
- 同期ワード

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細はLICENSEファイルを参照してください。