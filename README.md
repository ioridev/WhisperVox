# WhisperVox

WhisperVoxは、NVIDIA GPUを活用してOpenAIのWhisperモデルによる高速・高精度な文字起こしを行うツールです。動画ファイルから自動的に字幕（SRTファイル）を生成します。

## 特徴

- NVIDIA GPU（CUDA）による高速処理
- OpenAIのWhisper largeモデルによる高精度な文字起こし
- 日本語に最適化
- SRT形式の字幕ファイル出力

## 必要環境

- Python 3.8以上
- NVIDIA GPU（VRAM 8GB以上推奨）
- CUDA Toolkit 11.8以上
- cuDNN（対応バージョン）

## インストール手順

### Windows向け自動セットアップ（推奨）

Windowsユーザーは、同梱の自動セットアップスクリプトを使用して簡単にセットアップできます：

1. コマンドプロンプトまたはPowerShellを管理者として実行
2. プロジェクトディレクトリに移動
3. 以下のいずれかの方法でセットアップスクリプトを実行:

   **英語版スクリプトを使用する場合（文字化け回避）:**
   ```powershell
   .\setup_windows_en.bat
   ```

   **日本語版スクリプトを使用する場合:**
   ```powershell
   # PowerShellの場合
   .\setup_windows.bat

   # 文字化けする場合は、コードページをUTF-8に設定してから実行
   chcp 65001
   .\setup_windows.bat
   
   # コマンドプロンプト(cmd.exe)の場合
   setup_windows.bat
   ```

このスクリプトは以下の処理を自動的に行います：
- Pythonの確認
- FFmpegのインストール確認（必要に応じてインストールオプションを提供）
- 仮想環境の作成（オプション）
- NVIDIA GPUとCUDAの確認
- 適切なPyTorchバージョンのインストール
- 依存パッケージのインストール
- GPUの動作確認
- サンプル動画のダウンロードとテスト実行（オプション）

### 手動インストール

#### 1. CUDAとcuDNNのインストール

##### Windows:

1. **NVIDIA GPUドライバのインストール**
   - 最新のNVIDIA GPUドライバが必要です
   - [NVIDIA Driver Downloads](https://www.nvidia.com/Download/index.aspx)から最新ドライバをダウンロードしてインストール
   - または以下のコマンドでインストール:
     ```bash
     winget install NVIDIA.GeForceExperience
     ```

2. **CUDA Toolkitのインストール**
   - [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)からインストーラをダウンロード
   - または以下のコマンドでインストール:
     ```bash
     winget install Nvidia.CUDA
     ```

3. **cuDNNのインストール**
   - [NVIDIA cuDNN](https://developer.nvidia.com/cudnn)からダウンロード（NVIDIAアカウントが必要）
   - ダウンロードしたzipファイルを展開し、中身をCUDAのインストールディレクトリにコピー
   - 通常、CUDAは`C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.x`にインストールされます

#### 2. 依存パッケージのインストール

##### Windows:

```bash
# 仮想環境の作成（推奨）
python -m venv venv
venv\Scripts\activate

# GPU対応PyTorchをインストール（CUDA 11.8の場合）
pip install torch>=2.0.0 torchvision>=0.15.0 torchaudio>=2.0.0 --index-url https://download.pytorch.org/whl/cu118

# その他の依存パッケージをインストール
pip install -r requirements.txt
```

**注意:** インストールするPyTorchのバージョンは、使用しているCUDAのバージョンと互換性がある必要があります。

| CUDAバージョン | PyTorchインストールコマンド |
|--------------|---------------------------|
| CUDA 11.8    | `pip install torch>=2.0.0 torchvision>=0.15.0 torchaudio>=2.0.0 --index-url https://download.pytorch.org/whl/cu118` |
| CUDA 12.1    | `pip install torch>=2.0.0 torchvision>=0.15.0 torchaudio>=2.0.0 --index-url https://download.pytorch.org/whl/cu121` |

**重要:** torchvisionのバージョンは0.15.0以上を指定してください。torchvisionは2.0.0以上のバージョンが存在しないため、`torchvision>=2.0.0`と指定するとエラーが発生します。

インストールされているCUDAバージョンを確認するには、コマンドプロンプトで以下を実行:
```bash
nvcc --version
```

#### 3. FFmpegのインストール

文字起こしには動画から音声を抽出するためにFFmpegが必要です。

##### Windows:

以下のいずれかの方法でインストールできます：

**wingetを使用する場合:**
```bash
winget install FFmpeg
```

**Chocolateyを使用する場合:**
```bash
choco install ffmpeg
```

**Scoopを使用する場合:**
```bash
scoop install ffmpeg
```

**手動インストール:**
1. [FFmpeg公式サイト](https://ffmpeg.org/download.html)からWindows用のビルドをダウンロード
2. ダウンロードしたzipファイルを展開
3. 展開したフォルダ内の`bin`ディレクトリをシステム環境変数PATHに追加

##### macOS:
```bash
brew install ffmpeg
```

##### Linux:
```bash
# Debian/Ubuntu
apt-get install ffmpeg

# Fedora
dnf install ffmpeg

# CentOS/RHEL
yum install ffmpeg
```

## 使用方法

WhisperVoxには3つの使用方法があります：

### 1. サンプル動画でテスト（初めての方向け）

サンプル動画をダウンロードして文字起こしをテストするには：

```bash
# サンプル動画をダウンロードして文字起こしをテスト（smallモデル使用）
python download_sample.py

# モデルサイズを指定（tiny, base, small, medium, large）
python download_sample.py -m tiny

# 英語のサンプル動画を使用
python download_sample.py -l en

# ダウンロードのみ行い、文字起こしは手動で実行
python download_sample.py --no-transcribe

# CPUを強制的に使用
python download_sample.py --cpu

# ヘルプを表示
python download_sample.py --help
```

### 2. コマンドラインインターフェース（推奨）

`whisper_vox.py`スクリプトを使用すると、コマンドラインから簡単に文字起こしを実行できます：

```bash
# 基本的な使い方
python whisper_vox.py 動画ファイル.mp4

# 出力ファイルを指定
python whisper_vox.py 動画ファイル.mp4 -o 字幕ファイル.srt

# モデルサイズを指定（tiny, base, small, medium, large）
python whisper_vox.py 動画ファイル.mp4 -m medium

# 言語を指定（デフォルトは日本語 'ja'）
python whisper_vox.py 動画ファイル.mp4 -l en

# 出力形式を指定（srt または txt）
python whisper_vox.py 動画ファイル.mp4 -f txt

# CPUを強制的に使用
python whisper_vox.py 動画ファイル.mp4 --cpu

# ヘルプを表示
python whisper_vox.py --help
```

### 3. シンプルスクリプト

より単純な`subtitle.py`スクリプトも利用可能です：

```bash
python subtitle.py
```

デフォルトでは`sample_video.mp4`という名前の動画ファイルを処理し、`sample_subtitles.srt`という字幕ファイルを生成します。

カスタム設定をする場合は、`subtitle.py`を編集して、処理したい動画ファイルのパスと出力ファイル名を変更できます：

```python
if __name__ == "__main__":
    video_file = "あなたの動画.mp4"  # 動画パスを指定
    generate_subtitles(video_file, "出力字幕.srt")
```

## パフォーマンス

- VRAM 11GB: largeモデル（約5GB使用）を余裕で実行可能
- 処理速度: CPUと比較して数倍高速（GPUでは1分の音声を数十秒で処理）
- 10分の動画: CPUで5～10分 → GPUで1～2分程度

## 注意点

- 初回実行時はWhisperモデル（約3GB）のダウンロードが発生します
- GPUドライバとCUDAバージョンの不一致によるエラーが発生した場合は、バージョンを合わせる必要があります
- 長時間連続処理する場合はGPU温度に注意してください

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。