@echo off
echo WhisperVox Setup Script
echo ============================
echo.

REM Check for administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Warning: You don't have administrator privileges. Some features may be limited.
    echo It is recommended to run this script as administrator.
    echo.
    pause
)

REM Check Python
echo Checking Python version...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: Python not found.
    echo Please install Python and run this script again.
    echo https://www.python.org/downloads/
    exit /b 1
)
python --version
echo.

REM Check FFmpeg
echo Checking FFmpeg...
ffmpeg -version >nul 2>&1
if %errorLevel% neq 0 (
    echo FFmpeg not found. Do you want to install it?
    echo 1. Install with winget
    echo 2. Install with Chocolatey
    echo 3. Install with Scoop
    echo 4. Manual installation (skip)
    echo.
    set /p ffmpeg_choice="Select an option (1-4): "
    
    if "%ffmpeg_choice%"=="1" (
        echo Installing FFmpeg with winget...
        winget install FFmpeg
    ) else if "%ffmpeg_choice%"=="2" (
        echo Installing with Chocolatey...
        choco install ffmpeg -y
    ) else if "%ffmpeg_choice%"=="3" (
        echo Installing with Scoop...
        scoop install ffmpeg
    ) else (
        echo.
        echo Skipping FFmpeg installation.
        echo Please install manually: https://ffmpeg.org/download.html
        echo.
    )
) else (
    echo FFmpeg is already installed.
    ffmpeg -version | findstr "version"
)
echo.

REM Create virtual environment
echo Do you want to create a virtual environment? (recommended)
set /p venv_choice="Create virtual environment (y/n): "
if /i "%venv_choice%"=="y" (
    echo Creating virtual environment...
    python -m venv venv
    echo Activating virtual environment...
    call venv\Scripts\activate
    echo Virtual environment activated.
) else (
    echo Skipping virtual environment creation.
)
echo.

REM Check NVIDIA GPU and CUDA
echo Checking NVIDIA GPU and CUDA...
nvidia-smi >nul 2>&1
if %errorLevel% neq 0 (
    echo Warning: NVIDIA GPU not detected or drivers not properly installed.
    echo Continuing with CPU-only installation.
    set cuda_version=cpu
) else (
    echo NVIDIA GPU detected:
    nvidia-smi | findstr "NVIDIA"
    
    echo Checking CUDA version...
    nvcc --version >nul 2>&1
    if %errorLevel% neq 0 (
        echo Warning: CUDA not installed or not in PATH.
        echo It is recommended to install CUDA: https://developer.nvidia.com/cuda-downloads
        echo.
        echo Please select available CUDA version:
        echo 1. CUDA 11.8
        echo 2. CUDA 12.1
        echo 3. CPU only (no GPU support)
        echo.
        set /p cuda_choice="Select an option (1-3): "
        
        if "%cuda_choice%"=="1" (
            set cuda_version=cu118
        ) else if "%cuda_choice%"=="2" (
            set cuda_version=cu121
        ) else (
            set cuda_version=cpu
        )
    ) else (
        echo CUDA detected:
        for /f "tokens=*" %%i in ('nvcc --version ^| findstr "release"') do set cuda_info=%%i
        echo %cuda_info%
        
        echo.
        echo Selecting appropriate PyTorch version based on detected CUDA.
        echo %cuda_info% | findstr "11.8" >nul
        if %errorLevel% equ 0 (
            set cuda_version=cu118
        ) else (
            echo %cuda_info% | findstr "12.1" >nul
            if %errorLevel% equ 0 (
                set cuda_version=cu121
            ) else (
                echo Warning: Could not auto-detect version. Please select CUDA version:
                echo 1. CUDA 11.8
                echo 2. CUDA 12.1
                echo 3. CPU only (no GPU support)
                echo.
                set /p cuda_choice="Select an option (1-3): "
                
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

REM Install PyTorch
echo Installing PyTorch...
if "%cuda_version%"=="cpu" (
    echo Installing CPU version of PyTorch...
    pip install torch>=2.0.0 torchvision>=0.15.0 torchaudio>=2.0.0
) else (
    echo Installing GPU-enabled PyTorch (%cuda_version%)...
    pip install torch>=2.0.0 torchvision>=0.15.0 torchaudio>=2.0.0 --index-url https://download.pytorch.org/whl/%cuda_version%
)
echo.

REM Install dependencies
echo Installing other dependencies...
pip install -r requirements.txt
echo.

REM Check GPU functionality
echo Checking GPU functionality...
python -c "import torch; print('GPU available:', torch.cuda.is_available()); print('Number of GPUs:', torch.cuda.device_count()); print('GPU device name:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None')"
echo.

REM Download sample video and run test
echo Do you want to download a sample video and run a quick test?
set /p test_choice="Run test (y/n): "
if /i "%test_choice%"=="y" (
    echo.
    echo Downloading sample video and running a quick test...
    echo Note: First run will take time to download the Whisper model.
    echo.
    
    echo Please select model size to use:
    echo 1. tiny (fastest, lowest accuracy)
    echo 2. base (fast, low accuracy)
    echo 3. small (medium speed, medium accuracy)
    echo 4. medium (slow, high accuracy)
    echo 5. large (slowest, highest accuracy)
    echo.
    set /p model_choice="Select an option (1-5): "
    
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
    echo Running test with %model_size% model...
    python download_sample.py -m %model_size%
)

echo.
echo ============================
echo WhisperVox setup completed!
echo.
echo Usage:
echo - Test with sample video: python download_sample.py
echo - Transcribe a video file: python whisper_vox.py your_video.mp4
echo.
echo For detailed usage instructions, please refer to README.md.
echo ============================
echo.

if /i "%venv_choice%"=="y" (
    echo Note: If using a virtual environment, activate it before use with:
    echo call venv\Scripts\activate
    echo.
)

pause