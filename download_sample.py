#!/usr/bin/env python3
"""
サンプル動画をダウンロードしてWhisperVoxをテストするスクリプト
"""
import os
import sys
import argparse
import subprocess
import urllib.request
import shutil

# サンプル動画のURL（クリエイティブコモンズライセンスの動画）
SAMPLE_VIDEOS = {
    "ja": {
        "url": "https://download.blender.org/demo/movies/BBB/bbb_sunflower_1080p_30fps_normal.mp4",
        "name": "sample_video_ja.mp4",
        "description": "Big Buck Bunny (日本語吹き替えなし - 英語音声)"
    },
    "en": {
        "url": "https://download.blender.org/demo/movies/BBB/bbb_sunflower_1080p_30fps_normal.mp4",
        "name": "sample_video_en.mp4",
        "description": "Big Buck Bunny (英語音声)"
    }
}

def download_file(url, output_path):
    """URLからファイルをダウンロード"""
    print(f"ダウンロード中: {url}")
    print(f"保存先: {output_path}")
    
    # プログレスバー用の関数
    def report_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(int(downloaded * 100 / total_size), 100)
        sys.stdout.write(f"\r進捗: {percent}% [{downloaded} / {total_size} バイト]")
        sys.stdout.flush()
    
    try:
        urllib.request.urlretrieve(url, output_path, reporthook=report_progress)
        print("\nダウンロード完了")
        return True
    except Exception as e:
        print(f"\nダウンロードエラー: {e}")
        return False

def check_ffmpeg():
    """FFmpegがインストールされているか確認"""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def main():
    parser = argparse.ArgumentParser(description="サンプル動画をダウンロードしてWhisperVoxをテスト")
    parser.add_argument("-l", "--language", choices=["ja", "en"], default="ja", 
                        help="ダウンロードする動画の言語 (デフォルト: ja)")
    parser.add_argument("-m", "--model", choices=["tiny", "base", "small", "medium", "large"], 
                        default="small", help="使用するWhisperモデル (デフォルト: small)")
    parser.add_argument("--no-transcribe", action="store_true", 
                        help="ダウンロードのみ行い、文字起こしは行わない")
    parser.add_argument("--cpu", action="store_true", help="CPUを強制的に使用")
    
    args = parser.parse_args()
    
    # FFmpegの確認
    if not check_ffmpeg():
        print("エラー: FFmpegがインストールされていません。")
        print("README.mdのインストール手順を参照してFFmpegをインストールしてください。")
        return
    
    # サンプル動画の選択
    if args.language not in SAMPLE_VIDEOS:
        print(f"エラー: 言語 '{args.language}' のサンプル動画は利用できません。")
        return
    
    video_info = SAMPLE_VIDEOS[args.language]
    video_path = video_info["name"]
    
    # 動画のダウンロード
    print(f"サンプル動画: {video_info['description']}")
    
    if os.path.exists(video_path):
        print(f"ファイル '{video_path}' は既に存在します。")
        redownload = input("再ダウンロードしますか？ (y/n): ").lower() == 'y'
        if not redownload:
            print("既存のファイルを使用します。")
        else:
            success = download_file(video_info["url"], video_path)
            if not success:
                return
    else:
        success = download_file(video_info["url"], video_path)
        if not success:
            return
    
    # 文字起こしの実行
    if not args.no_transcribe:
        print("\n文字起こしを開始します...")
        cmd = ["python", "whisper_vox.py", video_path, "-m", args.model, "-l", args.language]
        
        if args.cpu:
            cmd.append("--cpu")
        
        try:
            subprocess.run(cmd, check=True)
            print("\nテスト完了！")
            
            # 出力ファイルのパス
            output_path = os.path.splitext(video_path)[0] + ".srt"
            if os.path.exists(output_path):
                print(f"字幕ファイルが生成されました: {output_path}")
                
                # 最初の数行を表示
                print("\n字幕ファイルの内容（先頭部分）:")
                with open(output_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        if i >= 15:  # 最初の15行まで表示
                            break
                        print(line.rstrip())
                    
                    if len(lines) > 15:
                        print("...")
        
        except subprocess.SubprocessError as e:
            print(f"文字起こし実行エラー: {e}")
    else:
        print("\nダウンロードのみ完了しました。")
        print(f"文字起こしを実行するには: python whisper_vox.py {video_path}")

if __name__ == "__main__":
    main()