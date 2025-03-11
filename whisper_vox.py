#!/usr/bin/env python3
import argparse
import os
import subprocess
import time
import whisper
import torch

def format_time(seconds):
    """秒数を SRT 形式の時間文字列に変換"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def format_duration(seconds):
    """秒数を読みやすい形式に変換"""
    if seconds < 60:
        return f"{seconds:.2f}秒"
    minutes = seconds // 60
    seconds %= 60
    if minutes < 60:
        return f"{int(minutes)}分{seconds:.2f}秒"
    hours = minutes // 60
    minutes %= 60
    return f"{int(hours)}時間{int(minutes)}分{seconds:.2f}秒"

def generate_subtitles(video_path, output_srt_path="output.srt", model_size="large", language="ja", device=None):
    """動画から字幕を生成する関数"""
    start_time = time.time()
    
    # デバイスの自動検出と設定
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # GPUが使えるか確認
    if device == "cuda" and not torch.cuda.is_available():
        print("警告: GPUが使えません。CPUで実行します。")
        device = "cpu"
    
    if device == "cuda":
        print(f"GPU使用: {torch.cuda.get_device_name(0)}")
        print(f"VRAM容量: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")
    else:
        print("CPU使用")
    
    # 1. 動画から音声を抽出
    audio_path = "temp_audio.mp3"
    try:
        print(f"動画ファイル '{video_path}' から音声を抽出中...")
        subprocess.run([
            "ffmpeg", 
            "-i", video_path, 
            "-vn", 
            "-acodec", "mp3", 
            "-y",  # 既存ファイルを上書き
            audio_path
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("音声抽出完了")
    except subprocess.CalledProcessError as e:
        print(f"音声抽出エラー: {e}")
        print(f"FFmpeg出力: {e.stderr.decode('utf-8', errors='replace')}")
        return
    except FileNotFoundError:
        print("エラー: FFmpegが見つかりません。インストールしてパスを通してください。")
        return
    
    # 2. Whisperで文字起こし
    try:
        print(f"{model_size}モデルをロード中...")
        model_load_start = time.time()
        model = whisper.load_model(model_size)
        if device == "cuda":
            model = model.cuda()
        model_load_time = time.time() - model_load_start
        print(f"モデルロード完了 ({format_duration(model_load_time)})")
        
        print(f"文字起こし中... (言語: {language})")
        transcribe_start = time.time()
        result = model.transcribe(audio_path, language=language)
        transcribe_time = time.time() - transcribe_start
        print(f"文字起こし完了 ({format_duration(transcribe_time)})")
        
        # 3. SRT形式で保存
        with open(output_srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(result["segments"]):
                start = segment["start"]
                end = segment["end"]
                text = segment["text"]
                f.write(f"{i+1}\n")
                f.write(f"{format_time(start)} --> {format_time(end)}\n")
                f.write(f"{text.strip()}\n\n")
        
        total_time = time.time() - start_time
        print(f"SRTファイル保存: {output_srt_path}")
        print(f"合計処理時間: {format_duration(total_time)}")
        
        # 処理した音声の長さを取得
        audio_duration = result["segments"][-1]["end"] if result["segments"] else 0
        if audio_duration > 0:
            processing_ratio = total_time / audio_duration
            print(f"音声長: {format_duration(audio_duration)}")
            print(f"処理速度比: {processing_ratio:.2f}x (1分の音声を{processing_ratio * 60:.2f}秒で処理)")
    
    except Exception as e:
        print(f"文字起こしエラー: {e}")
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"一時ファイル削除: {audio_path}")

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="WhisperVox - GPU加速による高速文字起こしツール")
    parser.add_argument("video", help="処理する動画ファイルのパス")
    parser.add_argument("-o", "--output", help="出力するSRTファイルのパス", default=None)
    parser.add_argument("-m", "--model", help="使用するWhisperモデルのサイズ", 
                        choices=["tiny", "base", "small", "medium", "large"], default="large")
    parser.add_argument("-l", "--language", help="文字起こしの言語", default="ja")
    parser.add_argument("--cpu", help="CPUを強制的に使用する", action="store_true")
    
    args = parser.parse_args()
    
    # 出力ファイル名が指定されていない場合、入力ファイル名から自動生成
    if args.output is None:
        base_name = os.path.splitext(os.path.basename(args.video))[0]
        args.output = f"{base_name}.srt"
    
    # デバイスの設定
    device = "cpu" if args.cpu else None
    
    # 字幕生成実行
    generate_subtitles(
        video_path=args.video,
        output_srt_path=args.output,
        model_size=args.model,
        language=args.language,
        device=device
    )

if __name__ == "__main__":
    main()