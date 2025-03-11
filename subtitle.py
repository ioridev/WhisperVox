import subprocess
import whisper
import os
import torch

def generate_subtitles(video_path, output_srt_path="output.srt"):
    # GPUが使えるか確認
    if not torch.cuda.is_available():
        print("警告: GPUが使えません。CPUで実行します。")
    else:
        print(f"GPU使用: {torch.cuda.get_device_name(0)}")

    # 1. 動画から音声を抽出
    audio_path = "temp_audio.mp3"
    try:
        subprocess.run([
            "ffmpeg", 
            "-i", video_path, 
            "-vn", 
            "-acodec", "mp3", 
            audio_path
        ], check=True)
        print("音声抽出完了")
    except subprocess.CalledProcessError as e:
        print(f"音声抽出エラー: {e}")
        return

    # 2. Whisperで文字起こし（GPU自動対応）
    try:
        model = whisper.load_model("large").cuda()  # largeモデルをGPUにロード
        result = model.transcribe(audio_path, language="ja")  # 日本語指定
        print("文字起こし完了")
        
        # 3. SRT形式で保存
        with open(output_srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(result["segments"]):
                start = segment["start"]
                end = segment["end"]
                text = segment["text"]
                f.write(f"{i+1}\n")
                f.write(f"{format_time(start)} --> {format_time(end)}\n")
                f.write(f"{text.strip()}\n\n")
        print(f"SRTファイル保存: {output_srt_path}")
    except Exception as e:
        print(f"文字起こしエラー: {e}")
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

if __name__ == "__main__":
    video_file = "sample_video.mp4"  # 動画パスを指定
    generate_subtitles(video_file, "sample_subtitles.srt")