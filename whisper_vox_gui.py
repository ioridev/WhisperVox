#!/usr/bin/env python3
"""
WhisperVox GUI - ドラッグアンドドロップで文字起こしを実行するGUIアプリケーション
"""
import sys
import os
import time
import threading
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QComboBox, QPushButton, QTextEdit, QProgressBar, 
    QFileDialog, QMessageBox, QGroupBox, QRadioButton
)
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal, QObject, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

# whisper_vox.pyから関数をインポート
from whisper_vox import generate_subtitles, format_duration

class WorkerSignals(QObject):
    """ワーカースレッドからのシグナルを定義するクラス"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

class TranscriptionWorker(threading.Thread):
    """バックグラウンドで文字起こしを実行するワーカースレッド"""
    def __init__(self, video_path, model_size, language, output_format):
        super().__init__()
        self.video_path = video_path
        self.model_size = model_size
        self.language = language
        self.output_format = output_format
        self.signals = WorkerSignals()
        self.daemon = True  # メインスレッドが終了したら一緒に終了
        
    def run(self):
        """文字起こしを実行"""
        try:
            # 出力ファイル名を生成
            base_name = os.path.splitext(os.path.basename(self.video_path))[0]
            extension = ".srt" if self.output_format == "srt" else ".txt"
            output_path = f"{base_name}{extension}"
            
            # 進捗状況を表示するためのカスタムコールバック
            def progress_callback(message):
                self.signals.progress.emit(message)
            
            # 文字起こしを実行
            start_time = time.time()
            self.signals.progress.emit(f"文字起こしを開始: {self.video_path}")
            self.signals.progress.emit(f"モデル: {self.model_size}, 言語: {self.language}, 形式: {self.output_format}")
            
            # 標準出力をキャプチャするためのリダイレクト
            import io
            import contextlib
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                generate_subtitles(
                    video_path=self.video_path,
                    output_path=output_path,
                    model_size=self.model_size,
                    language=self.language,
                    device=None,  # 自動検出
                    output_format=self.output_format
                )
            
            # キャプチャした出力を取得
            output = f.getvalue()
            for line in output.split('\n'):
                if line.strip():
                    self.signals.progress.emit(line)
            
            total_time = time.time() - start_time
            self.signals.progress.emit(f"文字起こし完了: {output_path}")
            self.signals.progress.emit(f"合計処理時間: {format_duration(total_time)}")
            
            # 完了シグナルを発行
            self.signals.finished.emit(output_path)
            
        except Exception as e:
            self.signals.error.emit(f"エラー: {str(e)}")

class DropArea(QWidget):
    """ファイルをドロップできるエリア"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(200)
        self.setStyleSheet("""
            DropArea {
                border: 2px dashed #aaa;
                border-radius: 5px;
                background-color: #f8f8f8;
            }
            DropArea:hover {
                border-color: #3498db;
            }
        """)
        
        layout = QVBoxLayout()
        self.label = QLabel("ここに動画ファイルをドラッグ＆ドロップ")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        self.setLayout(layout)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """ドラッグされたアイテムがエリアに入ったときの処理"""
        mime_data = event.mimeData()
        if mime_data.hasUrls() and self._is_valid_video_file(mime_data):
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """アイテムがドロップされたときの処理"""
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            for url in mime_data.urls():
                file_path = url.toLocalFile()
                if self._is_valid_video_extension(file_path):
                    self.parent().set_video_file(file_path)
                    break
            event.acceptProposedAction()
    
    def _is_valid_video_file(self, mime_data: QMimeData) -> bool:
        """有効な動画ファイルかどうかを判定"""
        if mime_data.hasUrls():
            for url in mime_data.urls():
                file_path = url.toLocalFile()
                if self._is_valid_video_extension(file_path):
                    return True
        return False
    
    def _is_valid_video_extension(self, file_path: str) -> bool:
        """有効な動画ファイルの拡張子かどうかを判定"""
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
        _, ext = os.path.splitext(file_path.lower())
        return ext in video_extensions

class WhisperVoxGUI(QMainWindow):
    """WhisperVox GUIのメインウィンドウ"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.current_video_file = None
        self.worker = None
    
    def init_ui(self):
        """UIの初期化"""
        self.setWindowTitle("WhisperVox GUI")
        self.setMinimumSize(800, 600)
        
        # メインウィジェットとレイアウト
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # ドロップエリア
        self.drop_area = DropArea(self)
        main_layout.addWidget(self.drop_area)
        
        # 設定グループ
        settings_group = QGroupBox("設定")
        settings_layout = QHBoxLayout()
        
        # モデルサイズ
        model_layout = QVBoxLayout()
        model_label = QLabel("モデルサイズ:")
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny", "base", "small", "medium", "large"])
        self.model_combo.setCurrentText("large")
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        settings_layout.addLayout(model_layout)
        
        # 言語
        language_layout = QVBoxLayout()
        language_label = QLabel("言語:")
        self.language_combo = QComboBox()
        self.language_combo.addItems(["ja", "en", "auto"])
        self.language_combo.setCurrentText("ja")
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combo)
        settings_layout.addLayout(language_layout)
        
        # 出力形式
        format_layout = QVBoxLayout()
        format_label = QLabel("出力形式:")
        self.format_group = QWidget()
        format_group_layout = QHBoxLayout()
        self.srt_radio = QRadioButton("SRT")
        self.txt_radio = QRadioButton("テキスト")
        self.srt_radio.setChecked(True)
        format_group_layout.addWidget(self.srt_radio)
        format_group_layout.addWidget(self.txt_radio)
        self.format_group.setLayout(format_group_layout)
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_group)
        settings_layout.addLayout(format_layout)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # ファイル選択ボタン
        file_button = QPushButton("ファイルを選択...")
        file_button.clicked.connect(self.select_file)
        main_layout.addWidget(file_button)
        
        # 実行ボタン
        self.run_button = QPushButton("文字起こしを実行")
        self.run_button.clicked.connect(self.run_transcription)
        self.run_button.setEnabled(False)
        main_layout.addWidget(self.run_button)
        
        # 進捗状況
        progress_group = QGroupBox("進捗状況")
        progress_layout = QVBoxLayout()
        
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        progress_layout.addWidget(self.progress_text)
        
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        # メインレイアウトを設定
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def select_file(self):
        """ファイル選択ダイアログを表示"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "動画ファイルを選択", "", 
            "動画ファイル (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm);;すべてのファイル (*)"
        )
        if file_path:
            self.set_video_file(file_path)
    
    def set_video_file(self, file_path):
        """動画ファイルをセット"""
        self.current_video_file = file_path
        self.drop_area.label.setText(f"選択されたファイル: {os.path.basename(file_path)}")
        self.run_button.setEnabled(True)
        self.log_message(f"ファイルが選択されました: {file_path}")
    
    def run_transcription(self):
        """文字起こしを実行"""
        if not self.current_video_file:
            QMessageBox.warning(self, "エラー", "動画ファイルが選択されていません。")
            return
        
        # 設定を取得
        model_size = self.model_combo.currentText()
        language = self.language_combo.currentText()
        output_format = "srt" if self.srt_radio.isChecked() else "txt"
        
        # UIを無効化
        self.run_button.setEnabled(False)
        self.progress_text.clear()
        
        # ワーカースレッドを作成して実行
        self.worker = TranscriptionWorker(
            self.current_video_file, model_size, language, output_format
        )
        self.worker.signals.progress.connect(self.log_message)
        self.worker.signals.finished.connect(self.on_transcription_finished)
        self.worker.signals.error.connect(self.on_transcription_error)
        self.worker.start()
    
    def log_message(self, message):
        """ログメッセージを表示"""
        self.progress_text.append(message)
        # 自動スクロール
        self.progress_text.verticalScrollBar().setValue(
            self.progress_text.verticalScrollBar().maximum()
        )
    
    def on_transcription_finished(self, output_path):
        """文字起こしが完了したときの処理"""
        self.run_button.setEnabled(True)
        
        # 完了メッセージを表示
        QMessageBox.information(
            self, "完了", 
            f"文字起こしが完了しました。\n出力ファイル: {output_path}"
        )
        
        # 出力ファイルを開くかどうか確認
        reply = QMessageBox.question(
            self, "ファイルを開く", 
            "出力ファイルを開きますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # プラットフォームに応じてファイルを開く
            if sys.platform == 'win32':
                os.startfile(output_path)
            elif sys.platform == 'darwin':  # macOS
                os.system(f'open "{output_path}"')
            else:  # Linux
                os.system(f'xdg-open "{output_path}"')
    
    def on_transcription_error(self, error_message):
        """文字起こし中にエラーが発生したときの処理"""
        self.run_button.setEnabled(True)
        self.log_message(f"エラーが発生しました: {error_message}")
        QMessageBox.critical(self, "エラー", f"文字起こし中にエラーが発生しました:\n{error_message}")

def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    window = WhisperVoxGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()