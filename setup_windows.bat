@echo off
echo WhisperVox セットアップスクリプト
echo ============================
echo.

REM 管理者権限の確認
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 警告: 管理者権限がありません。一部の機能が制限される可能性があります。
    echo 管理者として実行することをお勧めします。
    echo.
    pause
)

REM Pythonの確認
echo Pythonのバージョンを確認中...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo エラー: Pythonが見つかりません。
    echo Pythonをインストールしてから再度実行してください。
    echo https://www.python.org/downloads/
    exit /b 1
)
python --version
echo.

REM FFmpegの確認
echo FFmpegの確認中...
ffmpeg -version >nul 2>&1
if %errorLevel% neq 0 (
    echo FFmpegが見つかりません。インストールしますか？
    echo 1. wingetでインストール
    echo 2. Chocolateyでインストール
    echo 3. Scoopでインストール
    echo 4. 手動でインストール（スキップ）
    echo.
    set /p ffmpeg_choice="選択してください (1-4): "
    
    if "%ffmpeg_choice%"=="1" (
        echo wingetでFFmpegをインストール中...
        winget install FFmpeg
    ) else if "%ffmpeg_choice%"=="2" (
        echo Chocolateyでインストール中...
        choco install ffmpeg -y
    ) else if "%ffmpeg_choice%"=="3" (
        echo Scoopでインストール中...
        scoop install ffmpeg
    ) else (
        echo.
        echo FFmpegのインストールをスキップします。
        echo 手動でインストールしてください: https://ffmpeg.org/download.html
        echo.
    )
) else (
    echo FFmpegは既にインストールされています。
    ffmpeg -version | findstr "version"
)
echo.

REM 仮想環境の作成
echo 仮想環境を作成しますか？ (推奨)
set /p venv_choice="仮想環境を作成する (y/n): "
if /i "%venv_choice%"=="y" (
    echo 仮想環境を作成中...
    python -m venv venv
    echo 仮想環境を有効化中...
    call venv\Scripts\activate
    echo 仮想環境が有効化されました。
) else (
    echo 仮想環境の作成をスキップします。
)
echo.

REM NVIDIAのGPUとCUDAの確認
echo NVIDIAのGPUとCUDAを確認中...
nvidia-smi >nul 2>&1
if %errorLevel% neq 0 (
    echo 警告: NVIDIA GPUが検出されないか、ドライバが正しくインストールされていません。
    echo CPUモードでインストールを続行します。
    set cuda_version=cpu
) else (
    echo NVIDIA GPUが検出されました:
    nvidia-smi | findstr "NVIDIA"
    
    echo CUDAバージョンを確認中...
    nvcc --version >nul 2>&1
    if %errorLevel% neq 0 (
        echo 警告: CUDAがインストールされていないか、パスが通っていません。
        echo CUDAをインストールすることをお勧めします: https://developer.nvidia.com/cuda-downloads
        echo.
        echo 利用可能なCUDAバージョンを選択してください:
        echo 1. CUDA 11.8
        echo 2. CUDA 12.1
        echo 3. CPUのみ（GPU非対応）
        echo.
        set /p cuda_choice="選択してください (1-3): "
        
        if "%cuda_choice%"=="1" (
            set cuda_version=cu118
        ) else if "%cuda_choice%"=="2" (
            set cuda_version=cu121
        ) else (
            set cuda_version=cpu
        )
    ) else (
        echo CUDAが検出されました:
        for /f "tokens=*" %%i in ('nvcc --version ^| findstr "release"') do set cuda_info=%%i
        echo %cuda_info%
        
        echo.
        echo 検出されたCUDAに基づいて、適切なPyTorchバージョンを選択します。
        echo %cuda_info% | findstr "11.8" >nul
        if %errorLevel% equ 0 (
            set cuda_version=cu118
        ) else (
            echo %cuda_info% | findstr "12.1" >nul
            if %errorLevel% equ 0 (
                set cuda_version=cu121
            ) else (
                echo 警告: 自動検出できませんでした。CUDAバージョンを選択してください:
                echo 1. CUDA 11.8
                echo 2. CUDA 12.1
                echo 3. CPUのみ（GPU非対応）
                echo.
                set /p cuda_choice="選択してください (1-3): "
                
                if "%cuda_choice%"=="1" (
                    set cuda_version=cu118
                ) else if "%cuda_choice%"=="2" (
                    set cuda_version=cu121
                ) else (
                    set cuda_version=cpu
                )
            )
        )
    )
)
echo.

REM PyTorchのインストール
echo PyTorchをインストール中...
if "%cuda_version%"=="cpu" (
    echo CPUバージョンのPyTorchをインストール中...
    pip install torch>=2.0.0 torchvision>=0.15.0 torchaudio>=2.0.0
) else (
    echo GPU対応PyTorch (%cuda_version%)をインストール中...
    pip install torch>=2.0.0 torchvision>=0.15.0 torchaudio>=2.0.0 --index-url https://download.pytorch.org/whl/%cuda_version%
)
echo.

REM 依存パッケージのインストール
echo その他の依存パッケージをインストール中...
pip install -r requirements.txt
echo.

REM GPUの動作確認
echo GPUの動作確認を行います...
python -c "import torch; print('GPU利用可能:', torch.cuda.is_available()); print('GPU数:', torch.cuda.device_count()); print('GPUデバイス名:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'なし')"
echo.

REM サンプル動画のダウンロードと簡単なテスト
echo サンプル動画をダウンロードして簡単なテストを実行しますか？
set /p test_choice="テストを実行する (y/n): "
if /i "%test_choice%"=="y" (
    echo.
    echo サンプル動画をダウンロードして簡単なテストを実行します...
    echo 注意: 初回実行時はWhisperモデルのダウンロードに時間がかかります。
    echo.
    
    echo 使用するモデルサイズを選択してください:
    echo 1. tiny (最速・低精度)
    echo 2. base (高速・低精度)
    echo 3. small (中速・中精度)
    echo 4. medium (低速・高精度)
    echo 5. large (最低速・最高精度)
    echo.
    set /p model_choice="選択してください (1-5): "
    
    set model_size=small
    if "%model_choice%"=="1" (
        set model_size=tiny
    ) else if "%model_choice%"=="2" (
        set model_size=base
    ) else if "%model_choice%"=="3" (
        set model_size=small
    ) else if "%model_choice%"=="4" (
        set model_size=medium
    ) else if "%model_choice%"=="5" (
        set model_size=large
    )
    
    echo.
    echo %model_size%モデルを使用してテストを実行します...
    python download_sample.py -m %model_size%
)

echo.
echo ============================
echo WhisperVoxのセットアップが完了しました！
echo.
echo 使用方法:
echo - サンプル動画のテスト: python download_sample.py
echo - 動画ファイルの文字起こし: python whisper_vox.py 動画ファイル.mp4
echo.
echo 詳細な使用方法はREADME.mdを参照してください。
echo ============================
echo.

if /i "%venv_choice%"=="y" (
    echo 注意: 仮想環境を使用している場合、使用前に以下のコマンドで有効化してください:
    echo call venv\Scripts\activate
    echo.
)

pause