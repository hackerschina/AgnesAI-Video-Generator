# -*- coding: utf-8 -*-
import sys
import os
import json
import time
import uuid
import traceback
import logging
from datetime import datetime
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox,
    QSpinBox, QProgressBar, QFileDialog, QMessageBox,
    QGroupBox, QFormLayout, QListWidget, QListWidgetItem,
    QTabWidget, QSplitter, QScrollArea, QInputDialog, QMenu,
    QDialog, QDialogButtonBox, QDoubleSpinBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread, QUrl, QEvent
from PyQt5.QtGui import QFont, QIcon, QDesktopServices

APP_DIR = os.path.dirname(os.path.abspath(__file__))
API_BASE = "https://apihub.agnes-ai.com"
_DEFAULT_DATA_DIR = os.path.join(os.path.expanduser("~"), "AgnesAI_Data")
_CONFIG_FILENAME = "config.json"
_runtime_data_dir = None

def _get_data_dir():
    global _runtime_data_dir
    if _runtime_data_dir:
        return _runtime_data_dir
    config_file = os.path.join(_DEFAULT_DATA_DIR, _CONFIG_FILENAME)
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            saved_dir = config.get("data_dir", "")
            if saved_dir and os.path.isdir(saved_dir):
                _runtime_data_dir = saved_dir
                return saved_dir
        except Exception:
            pass
    _runtime_data_dir = _DEFAULT_DATA_DIR
    return _DEFAULT_DATA_DIR

def _set_data_dir(path):
    global _runtime_data_dir
    path = os.path.abspath(path)
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.join(path, "projects"), exist_ok=True)
    os.makedirs(os.path.join(path, "videos"), exist_ok=True)
    config_file = os.path.join(path, _CONFIG_FILENAME)
    existing = {}
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            pass
    existing["data_dir"] = path
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    old_config_file = os.path.join(_DEFAULT_DATA_DIR, _CONFIG_FILENAME)
    if os.path.abspath(config_file) != os.path.abspath(old_config_file) and os.path.exists(old_config_file):
        try:
            os.remove(old_config_file)
        except Exception:
            pass
    _runtime_data_dir = path

def _get_config_file():
    return os.path.join(_get_data_dir(), _CONFIG_FILENAME)

def _get_projects_dir():
    d = os.path.join(_get_data_dir(), "projects")
    os.makedirs(d, exist_ok=True)
    return d

def _ensure_dirs():
    d = _get_data_dir()
    os.makedirs(d, exist_ok=True)
    os.makedirs(os.path.join(d, "projects"), exist_ok=True)
    os.makedirs(os.path.join(d, "videos"), exist_ok=True)

_ensure_dirs()


def setup_logging():
    log_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(log_dir, "error.log")
    logging.basicConfig(
        filename=log_file,
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return log_file


def global_exception_handler(exc_type, exc_value, exc_tb):
    log_file = setup_logging()
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logging.error(error_msg)
    try:
        from PyQt5.QtWidgets import QMessageBox, QApplication
        app = QApplication.instance()
        if app:
            QMessageBox.critical(
                None, "程序错误",
                f"程序发生错误，请查看日志：\n{log_file}\n\n错误：{str(exc_value)}"
            )
    except Exception:
        pass


class ProjectManager:
    def __init__(self):
        self.projects = {}
        self._load_projects()

    def _load_projects(self):
        proj_dir = _get_projects_dir()
        self.projects = {}
        for filename in os.listdir(proj_dir):
            if filename.endswith('.json') and filename != 'config.json':
                filepath = os.path.join(proj_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        project = json.load(f)
                        self.projects[project['id']] = project
                except Exception:
                    pass

    def save_project(self, project):
        project['updated_at'] = datetime.now().isoformat()
        proj_dir = _get_projects_dir()
        filepath = os.path.join(proj_dir, f"{project['id']}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(project, f, ensure_ascii=False, indent=2)
        self.projects[project['id']] = project

    def create_project(self, name, mode="video"):
        project = {
            "id": str(uuid.uuid4()),
            "name": name,
            "mode": mode,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "characters": [],
            "scenes": [],
            "videos": [],
            "notes": ""
        }
        self.save_project(project)
        return project

    def delete_project(self, project_id):
        proj_dir = _get_projects_dir()
        filepath = os.path.join(proj_dir, f"{project_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
        self.projects.pop(project_id, None)

    def get_project(self, project_id):
        return self.projects.get(project_id)

    def get_all_projects(self):
        return sorted(self.projects.values(), key=lambda x: x['updated_at'], reverse=True)

    def add_character(self, project_id, character):
        project = self.get_project(project_id)
        if project:
            character['id'] = str(uuid.uuid4())
            project['characters'].append(character)
            self.save_project(project)
            return character
        return None

    def update_character(self, project_id, char_id, character):
        project = self.get_project(project_id)
        if project:
            for i, c in enumerate(project['characters']):
                if c['id'] == char_id:
                    character['id'] = char_id
                    project['characters'][i] = character
                    self.save_project(project)
                    break

    def delete_character(self, project_id, char_id):
        project = self.get_project(project_id)
        if project:
            project['characters'] = [c for c in project['characters'] if c['id'] != char_id]
            self.save_project(project)

    def add_scene(self, project_id, scene):
        project = self.get_project(project_id)
        if project:
            scene['id'] = str(uuid.uuid4())
            scene['status'] = scene.get('status', 'pending')
            project['scenes'].append(scene)
            self.save_project(project)
            return scene
        return None

    def update_scene(self, project_id, scene_id, scene):
        project = self.get_project(project_id)
        if project:
            for i, s in enumerate(project['scenes']):
                if s['id'] == scene_id:
                    scene['id'] = scene_id
                    project['scenes'][i] = scene
                    self.save_project(project)
                    break

    def add_video(self, project_id, video):
        project = self.get_project(project_id)
        if project:
            video['id'] = str(uuid.uuid4())
            video['created_at'] = datetime.now().isoformat()
            project['videos'].append(video)
            self.save_project(project)
            return video
        return None


class ChatWorker(QThread):
    status_update = pyqtSignal(str)
    result_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, api_key, messages, base_url, parent=None):
        super().__init__(parent)
        self.api_key = api_key
        self.messages = messages
        self.base_url = self._normalize_base_url(base_url)
        self._is_running = True

    def _normalize_base_url(self, url):
        url = url.rstrip("/")
        if url.endswith("/v1"):
            url = url[:-3]
        return url

    def stop(self):
        self._is_running = False

    def run(self):
        try:
            self.status_update.emit("AI 正在思考...")
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "agnes-2.0-flash",
                "messages": self.messages,
                "stream": False
            }
            url = f"{self.base_url}/v1/chat/completions"

            response = requests.post(url, headers=headers, json=payload, timeout=120)
            if response.status_code != 200:
                error_data = {}
                try:
                    error_data = response.json()
                except Exception:
                    pass
                detail = error_data.get("detail", error_data.get("message", str(response.text)[:200]))
                self.error_occurred.emit(f"请求失败 ({response.status_code}): {detail}")
                return

            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})
                content = message.get("content", "")
                self.result_ready.emit(content)
            else:
                self.error_occurred.emit("无法解析 AI 响应")

        except requests.exceptions.Timeout:
            self.error_occurred.emit("请求超时")
        except requests.exceptions.ConnectionError:
            self.error_occurred.emit("网络连接失败")
        except Exception as e:
            self.error_occurred.emit(f"发生错误: {str(e)}")


class VideoWorker(QThread):
    status_update = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    result_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, api_key, prompt, width=1280, height=720, num_frames=121, frame_rate=24, base_url=API_BASE, parent=None):
        super().__init__(parent)
        self.api_key = api_key
        self.prompt = prompt
        self.width = width
        self.height = height
        self.num_frames = num_frames
        self.frame_rate = frame_rate
        self.base_url = self._normalize_base_url(base_url)
        self._is_running = True

    def _normalize_base_url(self, url):
        url = url.rstrip("/")
        if url.endswith("/v1"):
            url = url[:-3]
        return url

    def stop(self):
        self._is_running = False
        self.status_update.emit("正在取消...")

    def run(self):
        try:
            self.status_update.emit("正在创建视频生成任务...")
            self.progress_update.emit(5)

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "agnes-video-v2.0",
                "prompt": self.prompt,
                "height": self.height,
                "width": self.width,
                "num_frames": self.num_frames,
                "frame_rate": self.frame_rate
            }

            response = requests.post(
                f"{self.base_url}/v1/videos",
                headers=headers, json=payload, timeout=60
            )

            if response.status_code != 200:
                error_data = {}
                try:
                    error_data = response.json()
                except Exception:
                    pass
                detail = error_data.get("detail", error_data.get("message", str(response.text)[:200]))
                self.error_occurred.emit(f"请求失败 ({response.status_code}): {detail}")
                return

            data = response.json()
            video_id = None
            if isinstance(data, dict):
                video_id = data.get("video_id") or data.get("id")
                if not video_id and "data" in data:
                    inner = data["data"]
                    if isinstance(inner, dict):
                        video_id = inner.get("video_id") or inner.get("id")

            if not video_id:
                self.error_occurred.emit(f"无法获取 video_id")
                return

            self.status_update.emit(f"任务已创建，正在等待生成...")
            self.progress_update.emit(10)

            poll_count = 0
            while self._is_running and poll_count < 120:
                time.sleep(5)
                poll_count += 1
                try:
                    poll_resp = requests.get(
                        f"{self.base_url}/agnesapi",
                        params={"video_id": video_id},
                        headers=headers, timeout=30
                    )
                    if poll_resp.status_code != 200:
                        continue

                    poll_data = poll_resp.json()
                    status = poll_data.get("status", "")
                    video_url = None

                    if "data" in poll_data and isinstance(poll_data["data"], dict):
                        inner = poll_data["data"]
                        video_url = inner.get("url") or inner.get("video_url") or inner.get("download_url")
                        if not status:
                            status = inner.get("status", "")

                    progress = min(10 + int((poll_count / 120) * 80), 90)
                    self.progress_update.emit(progress)
                    self.status_update.emit(f"正在生成视频... ({poll_count})")

                    if status in ["completed", "succeeded", "success", "done", "finished"]:
                        if video_url:
                            self.progress_update.emit(100)
                            self.result_ready.emit(video_url)
                            return
                        urls = self._extract_urls(poll_data)
                        if urls:
                            self.progress_update.emit(100)
                            self.result_ready.emit(urls[0])
                            return

                    if status in ["failed", "error", "cancelled"]:
                        self.error_occurred.emit(f"视频生成失败: {poll_data.get('error', '')}")
                        return
                except Exception:
                    continue

            if poll_count >= 120:
                self.error_occurred.emit("视频生成超时")

        except requests.exceptions.Timeout:
            self.error_occurred.emit("请求超时")
        except requests.exceptions.ConnectionError:
            self.error_occurred.emit("网络连接失败")
        except Exception as e:
            self.error_occurred.emit(f"发生错误: {str(e)}")

    def _extract_urls(self, data):
        urls = []
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and value.startswith("http"):
                    urls.append(value)
                elif isinstance(value, (dict, list)):
                    urls.extend(self._extract_urls(value))
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    urls.extend(self._extract_urls(item))
        return urls


class DownloadWorker(QThread):
    progress_update = pyqtSignal(int)
    finished_download = pyqtSignal(str)
    download_error = pyqtSignal(str)

    def __init__(self, url, save_path, parent=None):
        super().__init__(parent)
        self.url = url
        self.save_path = save_path

    def run(self):
        try:
            response = requests.get(self.url, stream=True, timeout=30)
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))
            block_size = 8192
            downloaded = 0

            with open(self.save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            self.progress_update.emit(int((downloaded / total_size) * 100))

            self.progress_update.emit(100)
            self.finished_download.emit(self.save_path)
        except Exception as e:
            self.download_error.emit(f"下载失败: {str(e)}")


class CharacterDialog(QDialog):
    def __init__(self, character=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("角色档案")
        self.setMinimumWidth(450)
        self.character = character or {}

        layout = QFormLayout(self)

        self.name_input = QLineEdit(self.character.get("name", ""))
        self.name_input.setPlaceholderText("角色名称")
        layout.addRow("名称:", self.name_input)

        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["女", "男", "其他"])
        self.gender_combo.setCurrentText(self.character.get("gender", "女"))
        layout.addRow("性别:", self.gender_combo)

        self.age_input = QSpinBox()
        self.age_input.setRange(1, 100)
        self.age_input.setValue(self.character.get("age", 20))
        layout.addRow("年龄:", self.age_input)

        self.appearance_input = QTextEdit(self.character.get("appearance", ""))
        self.appearance_input.setPlaceholderText("外貌特征：发型、发色、眼睛、肤色等")
        self.appearance_input.setMinimumHeight(80)
        layout.addRow("外貌:", self.appearance_input)

        self.clothing_input = QTextEdit(self.character.get("clothing", ""))
        self.clothing_input.setPlaceholderText("服装设计：风格、颜色、配饰等")
        self.clothing_input.setMinimumHeight(60)
        layout.addRow("服装:", self.clothing_input)

        self.personality_input = QTextEdit(self.character.get("personality", ""))
        self.personality_input.setPlaceholderText("性格特点、说话风格等")
        self.personality_input.setMinimumHeight(60)
        layout.addRow("性格:", self.personality_input)

        self.story_input = QTextEdit(self.character.get("story", ""))
        self.story_input.setPlaceholderText("角色背景故事、身份等")
        self.story_input.setMinimumHeight(60)
        layout.addRow("背景:", self.story_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_character(self):
        return {
            "name": self.name_input.text().strip(),
            "gender": self.gender_combo.currentText(),
            "age": self.age_input.value(),
            "appearance": self.appearance_input.toPlainText().strip(),
            "clothing": self.clothing_input.toPlainText().strip(),
            "personality": self.personality_input.toPlainText().strip(),
            "story": self.story_input.toPlainText().strip()
        }

    def get_character_description(self):
        c = self.get_character()
        parts = [f"{c['name']}({c['gender']}, {c['age']}岁)"]
        if c['appearance']:
            parts.append(f"外貌: {c['appearance']}")
        if c['clothing']:
            parts.append(f"服装: {c['clothing']}")
        if c['personality']:
            parts.append(f"性格: {c['personality']}")
        if c['story']:
            parts.append(f"背景: {c['story']}")
        return ", ".join(parts)


class AgnesVideoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.project_manager = ProjectManager()
        self.current_project = None
        self.video_worker = None
        self.chat_worker = None
        self.download_worker = None
        self.chat_history = []
        self._init_ui()
        self._load_config()

    def _init_ui(self):
        self.setWindowTitle("Agnes AI 智能创作助手")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        splitter.setSizes([320, 1080])

        self.setStyleSheet("""
            QMainWindow { background-color: #f5f7fa; }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e0e6ed;
                border-radius: 8px;
                margin-top: 14px;
                padding-top: 14px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 8px;
                color: #2c3e50;
            }
            QLineEdit, QTextEdit, QSpinBox, QComboBox {
                border: 1px solid #d0d7de;
                border-radius: 6px;
                padding: 6px 10px;
                background-color: #f8f9fa;
                selection-background-color: #4CAF50;
            }
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
                border-color: #4CAF50;
                background-color: white;
            }
            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QListWidget {
                border: 1px solid #e0e6ed;
                border-radius: 6px;
                background-color: white;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                margin: 2px 0;
            }
            QListWidget::item:selected {
                background-color: #e8f5e9;
                color: #2e7d32;
            }
            QProgressBar {
                border: 1px solid #d0d7de;
                border-radius: 6px;
                text-align: center;
                height: 22px;
                background-color: #f8f9fa;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 5px;
            }
            QTabWidget::pane {
                border: 1px solid #e0e6ed;
                border-radius: 8px;
                top: -1px;
                background-color: white;
            }
            QTabBar::tab {
                padding: 10px 20px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #4CAF50;
                border-bottom: 2px solid #4CAF50;
            }
        """)

        self.current_video_url = ""

    def _create_left_panel(self):
        panel = QWidget()
        panel.setFixedWidth(320)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title = QLabel("🎬 Agnes AI")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; padding: 8px;")
        layout.addWidget(title)

        dir_group = QGroupBox("📂 数据目录")
        dir_layout = QVBoxLayout(dir_group)

        self.data_dir_label = QLabel(_get_data_dir())
        self.data_dir_label.setWordWrap(True)
        self.data_dir_label.setStyleSheet("color: #555; font-size: 11px; padding: 4px; background: #f0f0f0; border-radius: 4px;")
        dir_layout.addWidget(self.data_dir_label)

        dir_btn_layout = QHBoxLayout()
        choose_dir_btn = QPushButton("📁 选择目录")
        choose_dir_btn.setStyleSheet("background-color: #3498DB; color: white;")
        choose_dir_btn.setCursor(Qt.PointingHandCursor)
        choose_dir_btn.clicked.connect(self._choose_data_dir)
        dir_btn_layout.addWidget(choose_dir_btn)

        open_dir_btn = QPushButton("📂 打开目录")
        open_dir_btn.setStyleSheet("background-color: #27ae60; color: white;")
        open_dir_btn.setCursor(Qt.PointingHandCursor)
        open_dir_btn.clicked.connect(lambda: self._open_folder(_get_data_dir()))
        dir_btn_layout.addWidget(open_dir_btn)

        dir_layout.addLayout(dir_btn_layout)
        layout.addWidget(dir_group)

        api_group = QGroupBox("API 配置")
        api_layout = QFormLayout(api_group)
        api_layout.setSpacing(8)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("请输入 API Key")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setMinimumHeight(30)
        api_layout.addRow("API Key:", self.api_key_input)

        self.base_url_input = QLineEdit(API_BASE)
        self.base_url_input.setMinimumHeight(30)
        api_layout.addRow("Base URL:", self.base_url_input)

        test_btn = QPushButton("🔗 测试连接")
        test_btn.setStyleSheet("background-color: #F39C12; color: white;")
        test_btn.setCursor(Qt.PointingHandCursor)
        test_btn.clicked.connect(self._test_connection)
        api_layout.addRow(test_btn)

        save_btn = QPushButton("💾 保存配置")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save_config)
        api_layout.addRow(save_btn)

        layout.addWidget(api_group)

        project_group = QGroupBox("📁 项目管理")
        project_layout = QVBoxLayout(project_group)

        new_proj_btn = QPushButton("➕ 新建项目")
        new_proj_btn.setStyleSheet("background-color: #3498DB; color: white;")
        new_proj_btn.setCursor(Qt.PointingHandCursor)
        new_proj_btn.clicked.connect(self._create_project)
        project_layout.addWidget(new_proj_btn)

        self.project_list = QListWidget()
        self.project_list.setMinimumHeight(150)
        self.project_list.itemClicked.connect(self._on_project_clicked)
        self.project_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.project_list.customContextMenuRequested.connect(self._project_context_menu)
        project_layout.addWidget(self.project_list)

        layout.addWidget(project_group)

        self._refresh_project_list()

        char_group = QGroupBox("👤 角色档案")
        char_layout = QVBoxLayout(char_group)

        new_char_btn = QPushButton("➕ 新建角色")
        new_char_btn.setStyleSheet("background-color: #9B59B6; color: white;")
        new_char_btn.setCursor(Qt.PointingHandCursor)
        new_char_btn.clicked.connect(self._create_character)
        char_layout.addWidget(new_char_btn)

        self.char_list = QListWidget()
        self.char_list.setMinimumHeight(120)
        self.char_list.itemClicked.connect(self._on_character_clicked)
        self.char_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.char_list.customContextMenuRequested.connect(self._character_context_menu)
        char_layout.addWidget(self.char_list)

        layout.addWidget(char_group)

        layout.addStretch()
        return panel

    def _choose_data_dir(self):
        current_dir = _get_data_dir()
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择数据保存目录", current_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if dir_path:
            try:
                reply = QMessageBox.question(
                    self, "确认",
                    f"将数据目录设置为:\n{dir_path}\n\n"
                    f"这会把配置、项目、视频都保存到此目录。\n"
                    f"如果目录中有旧数据，会自动加载。\n\n"
                    f"是否继续？",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
                _set_data_dir(dir_path)
                self.data_dir_label.setText(dir_path)
                self.project_manager._load_projects()
                self._refresh_project_list()
                self._save_config()
                QMessageBox.information(self, "成功", f"数据目录已设置为:\n{dir_path}\n\n请重启程序以确保所有功能正常。")
            except Exception as e:
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "错误", f"设置目录失败: {str(e)}")

    def _create_right_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self._create_chat_tab()
        self._create_video_tab()
        self._create_comic_tab()

        return panel

    def _create_chat_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setMinimumHeight(300)
        self.chat_display.setPlaceholderText("与 AI 对话，或请求生成剧本...")
        layout.addWidget(self.chat_display, 1)

        input_layout = QHBoxLayout()
        self.chat_input = QTextEdit()
        self.chat_input.setPlaceholderText("输入消息... (Enter 发送, Shift+Enter 换行)")
        self.chat_input.setMaximumHeight(80)
        input_layout.addWidget(self.chat_input, 1)

        send_btn = QPushButton("📤 发送")
        send_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 12px 24px;")
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.clicked.connect(self._send_chat_message)
        input_layout.addWidget(send_btn)

        layout.addLayout(input_layout)

        self.chat_input.installEventFilter(self)
        self.chat_send_btn = send_btn

        self.tabs.addTab(tab, "💬 AI 对话")

    def _create_video_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        params_group = QGroupBox("视频生成参数")
        params_layout = QFormLayout(params_group)
        params_layout.setSpacing(8)

        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText(
            "描述你想要生成的视频场景...\n\n"
            "支持角色引用，例如：\n"
            "{角色: 小美} 在樱花树下漫步，春风拂过她的长发..."
        )
        self.prompt_input.setMinimumHeight(120)
        params_layout.addRow("提示词:", self.prompt_input)

        context_layout = QHBoxLayout()
        self.use_context_check = QPushButton("使用项目角色")
        self.use_context_check.setCheckable(True)
        self.use_context_check.setStyleSheet(
            "QPushButton:checked { background-color: #4CAF50; color: white; }"
            "QPushButton:unchecked { background-color: #ecf0f1; color: #7f8c8d; }"
        )
        self.use_context_check.setCursor(Qt.PointingHandCursor)
        self.use_context_check.clicked.connect(self._on_context_toggle)
        context_layout.addWidget(self.use_context_check)
        context_layout.addStretch()
        params_layout.addRow("角色:", context_layout)

        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "1152 x 768 (4:3)",
            "1280 x 720 (16:9 HD)",
            "1920 x 1080 (16:9 Full HD)",
            "768 x 768 (1:1 方形)",
            "1080 x 1920 (9:16 竖屏)",
        ])
        self.resolution_combo.setCurrentIndex(1)
        params_layout.addRow("分辨率:", self.resolution_combo)

        size_layout = QHBoxLayout()
        self.width_spin = QSpinBox()
        self.width_spin.setRange(256, 4096)
        self.width_spin.setValue(1280)
        self.width_spin.setSingleStep(64)
        self.width_spin.setEnabled(False)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(256, 4096)
        self.height_spin.setValue(720)
        self.height_spin.setSingleStep(64)
        self.height_spin.setEnabled(False)

        size_layout.addWidget(QLabel("宽:"))
        size_layout.addWidget(self.width_spin)
        size_layout.addWidget(QLabel("高:"))
        size_layout.addWidget(self.height_spin)
        size_layout.addStretch()
        params_layout.addRow("尺寸:", size_layout)

        other_layout = QHBoxLayout()
        self.frames_spin = QSpinBox()
        self.frames_spin.setRange(1, 300)
        self.frames_spin.setValue(121)

        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(24)

        other_layout.addWidget(QLabel("帧数:"))
        other_layout.addWidget(self.frames_spin)
        other_layout.addWidget(QLabel("帧率:"))
        other_layout.addWidget(self.fps_spin)
        other_layout.addStretch()
        params_layout.addRow(other_layout)

        layout.addWidget(params_group)

        action_layout = QHBoxLayout()
        self.generate_btn = QPushButton("🚀 开始生成视频")
        self.generate_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; font-size: 14px; padding: 12px 32px;"
        )
        self.generate_btn.setCursor(Qt.PointingHandCursor)
        self.generate_btn.clicked.connect(self._on_generate)
        action_layout.addWidget(self.generate_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setStyleSheet(
            "background-color: #e74c3c; color: white; padding: 12px 24px;"
        )
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self._on_cancel)
        action_layout.addWidget(self.cancel_btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)

        progress_group = QGroupBox("生成进度")
        progress_layout = QVBoxLayout(progress_group)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #555;")
        self.status_label.setWordWrap(True)
        progress_layout.addWidget(self.status_label)
        layout.addWidget(progress_group)

        result_group = QGroupBox("生成结果")
        result_layout = QVBoxLayout(result_group)

        self.result_url_label = QLabel("视频链接将在此处显示")
        self.result_url_label.setOpenExternalLinks(False)
        self.result_url_label.setWordWrap(True)
        self.result_url_label.setStyleSheet(
            "color: #2980b9; padding: 10px; background: #eaf4fb; border-radius: 6px; font-size: 12px;"
        )
        self.result_url_label.setCursor(Qt.PointingHandCursor)
        self.result_url_label.mousePressEvent = self._on_url_clicked
        result_layout.addWidget(self.result_url_label)

        download_layout = QHBoxLayout()
        self.copy_url_btn = QPushButton("📋 复制链接")
        self.copy_url_btn.setEnabled(False)
        self.copy_url_btn.setStyleSheet("background-color: #3498DB; color: white;")
        self.copy_url_btn.setCursor(Qt.PointingHandCursor)
        self.copy_url_btn.clicked.connect(self._on_copy_url)

        self.download_btn = QPushButton("💾 下载视频")
        self.download_btn.setEnabled(False)
        self.download_btn.setStyleSheet("background-color: #27ae60; color: white;")
        self.download_btn.setCursor(Qt.PointingHandCursor)
        self.download_btn.clicked.connect(self._on_download)

        self.open_btn = QPushButton("🔗 打开视频")
        self.open_btn.setEnabled(False)
        self.open_btn.setStyleSheet("background-color: #9b59b6; color: white;")
        self.open_btn.setCursor(Qt.PointingHandCursor)
        self.open_btn.clicked.connect(self._on_open_video)

        download_layout.addWidget(self.copy_url_btn)
        download_layout.addWidget(self.download_btn)
        download_layout.addWidget(self.open_btn)
        download_layout.addStretch()
        result_layout.addLayout(download_layout)

        self.download_status = QLabel("")
        self.download_status.setStyleSheet("color: #666; font-size: 12px;")
        result_layout.addWidget(self.download_status)

        layout.addWidget(result_group)
        layout.addStretch()

        self.resolution_combo.currentIndexChanged.connect(self._on_resolution_changed)

        self.tabs.addTab(tab, "🎬 视频生成")

    def _create_comic_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        desc_group = QGroupBox("漫剧描述")
        desc_layout = QVBoxLayout(desc_group)

        self.comic_desc_input = QTextEdit()
        self.comic_desc_input.setPlaceholderText(
            "描述你想要生成的漫剧，例如：\n"
            "古装仙侠剧，讲述一位少女修仙的故事\n"
            "风格：国风、水墨、唯美\n"
            "场景：山间竹林、古寺庙宇、云海仙境"
        )
        self.comic_desc_input.setMinimumHeight(100)
        desc_layout.addWidget(self.comic_desc_input)

        self.comic_style_combo = QComboBox()
        self.comic_style_combo.addItems([
            "自动", "国风仙侠", "现代都市", "科幻未来",
            "悬疑推理", "校园青春", "武侠江湖", "奇幻魔法"
        ])
        desc_layout.addWidget(QLabel("风格:"))
        desc_layout.addWidget(self.comic_style_combo)

        generate_script_btn = QPushButton("✍️ AI 生成剧本")
        generate_script_btn.setStyleSheet(
            "background-color: #9B59B6; color: white; padding: 10px 20px;"
        )
        generate_script_btn.setCursor(Qt.PointingHandCursor)
        generate_script_btn.clicked.connect(self._generate_comic_script)
        desc_layout.addWidget(generate_script_btn)

        layout.addWidget(desc_group)

        script_group = QGroupBox("分镜剧本")
        script_layout = QVBoxLayout(script_group)

        self.comic_script_display = QTextEdit()
        self.comic_script_display.setPlaceholderText("AI 生成的剧本将显示在此处...")
        self.comic_script_display.setMinimumHeight(150)
        self.comic_script_display.setReadOnly(True)
        script_layout.addWidget(self.comic_script_display)

        scene_actions = QHBoxLayout()
        add_scene_btn = QPushButton("➕ 添加场景")
        add_scene_btn.setStyleSheet("background-color: #3498DB; color: white;")
        add_scene_btn.setCursor(Qt.PointingHandCursor)
        add_scene_btn.clicked.connect(self._add_manual_scene)

        gen_all_btn = QPushButton("🎬 批量生成所有场景")
        gen_all_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        gen_all_btn.setCursor(Qt.PointingHandCursor)
        gen_all_btn.clicked.connect(self._generate_all_scenes)

        scene_actions.addWidget(add_scene_btn)
        scene_actions.addWidget(gen_all_btn)
        scene_actions.addStretch()
        script_layout.addLayout(scene_actions)

        self.scene_list = QListWidget()
        self.scene_list.setMinimumHeight(150)
        self.scene_list.itemDoubleClicked.connect(self._on_scene_double_clicked)
        script_layout.addWidget(self.scene_list)

        layout.addWidget(script_group)

        self.comic_status_label = QLabel("")
        self.comic_status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.comic_status_label)

        self.tabs.addTab(tab, "🖼️ 漫剧生成")

    def eventFilter(self, obj, event):
        if obj == self.chat_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and not (event.modifiers() & Qt.ShiftModifier):
                self._send_chat_message()
                return True
        return super().eventFilter(obj, event)

    def _refresh_project_list(self):
        self.project_list.clear()
        projects = self.project_manager.get_all_projects()
        for project in projects:
            item = QListWidgetItem(f"📁 {project['name']}")
            item.setData(Qt.UserRole, project['id'])
            self.project_list.addItem(item)

    def _on_project_clicked(self, item):
        project_id = item.data(Qt.UserRole)
        project = self.project_manager.get_project(project_id)
        if project:
            self.current_project = project
            self._refresh_character_list()
            self._refresh_scene_list()

    def _project_context_menu(self, pos):
        item = self.project_list.itemAt(pos)
        if not item:
            return
        project_id = item.data(Qt.UserRole)
        menu = QMenu(self)
        delete_action = menu.addAction("🗑️ 删除项目")
        action = menu.exec_(self.project_list.mapToGlobal(pos))
        if action == delete_action:
            reply = QMessageBox.question(
                self, "确认删除", "确定要删除此项目吗？此操作不可撤销。",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.project_manager.delete_project(project_id)
                self._refresh_project_list()
                if self.current_project and self.current_project['id'] == project_id:
                    self.current_project = None
                    self.char_list.clear()
                    self.scene_list.clear()

    def _create_project(self):
        name, ok = QInputDialog.getText(self, "新建项目", "项目名称:")
        if ok and name.strip():
            project = self.project_manager.create_project(name.strip())
            self._refresh_project_list()

    def _refresh_character_list(self):
        self.char_list.clear()
        if self.current_project:
            for char in self.current_project.get('characters', []):
                item = QListWidgetItem(f"👤 {char['name']} ({char.get('gender', '')}, {char.get('age', '')}岁)")
                item.setData(Qt.UserRole, char['id'])
                self.char_list.addItem(item)

    def _character_context_menu(self, pos):
        item = self.char_list.itemAt(pos)
        if not item or not self.current_project:
            return
        char_id = item.data(Qt.UserRole)
        menu = QMenu(self)
        edit_action = menu.addAction("✏️ 编辑")
        delete_action = menu.addAction("🗑️ 删除")
        action = menu.exec_(self.char_list.mapToGlobal(pos))
        if action == edit_action:
            self._edit_character(char_id)
        elif action == delete_action:
            reply = QMessageBox.question(self, "确认删除", "确定要删除此角色吗？", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.project_manager.delete_character(self.current_project['id'], char_id)
                self._refresh_character_list()

    def _on_character_clicked(self, item):
        if not self.current_project:
            QMessageBox.information(self, "提示", "请先选择或创建一个项目")
            return
        char_id = item.data(Qt.UserRole)
        self._edit_character(char_id)

    def _create_character(self):
        if not self.current_project:
            project = self.project_manager.create_project(f"新项目_{datetime.now().strftime('%m%d')}")
            self.current_project = project
            self._refresh_project_list()

        dialog = CharacterDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            character = dialog.get_character()
            self.project_manager.add_character(self.current_project['id'], character)
            self._refresh_character_list()

    def _edit_character(self, char_id):
        if not self.current_project:
            return
        character = None
        for c in self.current_project.get('characters', []):
            if c['id'] == char_id:
                character = c
                break

        dialog = CharacterDialog(character, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            updated = dialog.get_character()
            self.project_manager.update_character(self.current_project['id'], char_id, updated)
            self._refresh_character_list()

    def _get_context_description(self):
        if not self.use_context_check.isChecked() or not self.current_project:
            return ""
        characters = self.current_project.get('characters', [])
        if not characters:
            return ""
        descriptions = []
        for char in characters:
            parts = [f"{char.get('name', '')}({char.get('gender', '')}, {char.get('age', '')}岁)"]
            if char.get('appearance'):
                parts.append(f"外貌: {char['appearance']}")
            if char.get('clothing'):
                parts.append(f"服装: {char['clothing']}")
            if char.get('personality'):
                parts.append(f"性格: {char['personality']}")
            descriptions.append(", ".join(parts))
        return "【角色设定】" + "; ".join(descriptions)

    def _on_context_toggle(self):
        if self.use_context_check.isChecked() and not self.current_project:
            QMessageBox.information(self, "提示", "请先选择或创建一个项目")
            self.use_context_check.setChecked(False)
        elif self.use_context_check.isChecked():
            self._refresh_character_list()

    def _on_resolution_changed(self, index):
        presets = {
            0: (1152, 768), 1: (1280, 720), 2: (1920, 1080),
            3: (768, 768), 4: (1080, 1920),
        }
        if index in presets:
            self.width_spin.setValue(presets[index][0])
            self.height_spin.setValue(presets[index][1])

    def _send_chat_message(self):
        message = self.chat_input.toPlainText().strip()
        if not message:
            return
        api_key = self.api_key_input.text().strip()
        base_url = self.base_url_input.text().strip()

        if not api_key:
            QMessageBox.warning(self, "提示", "请填写 API Key")
            return

        self.chat_input.clear()

        user_msg = f"<div style='color:#1a73e8'><b>你:</b></div><div>{message}</div><br>"
        self.chat_display.append(user_msg)

        self.chat_history.append({"role": "user", "content": message})

        context = self._get_context_description()
        messages = list(self.chat_history)
        if context:
            messages.insert(0, {"role": "system", "content": context})

        self.chat_worker = ChatWorker(api_key, messages, base_url)
        self.chat_worker.status_update.connect(lambda m: self.chat_display.append(f"<div style='color:#666'><i>{m}</i></div>"))
        self.chat_worker.result_ready.connect(self._on_chat_result)
        self.chat_worker.error_occurred.connect(lambda e: self.chat_display.append(f"<div style='color:#e74c3c'>错误: {e}</div>"))
        self.chat_worker.start()

    def _on_chat_result(self, result):
        self.chat_history.append({"role": "assistant", "content": result})
        ai_msg = f"<div style='color:#2e7d32'><b>AI:</b></div><div>{result}</div><br>"
        self.chat_display.append(ai_msg)
        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())

    def _on_generate(self):
        api_key = self.api_key_input.text().strip()
        prompt = self.prompt_input.toPlainText().strip()
        base_url = self.base_url_input.text().strip()

        if not api_key:
            QMessageBox.warning(self, "提示", "请填写 API Key")
            return
        if not prompt:
            QMessageBox.warning(self, "提示", "请填写视频生成提示词")
            return

        context = self._get_context_description()
        full_prompt = f"{context}\n\n{prompt}" if context else prompt

        self.generate_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("正在启动...")
        self.current_video_url = ""
        self.result_url_label.setText("视频链接将在此处显示")
        self.copy_url_btn.setEnabled(False)
        self.download_btn.setEnabled(False)
        self.open_btn.setEnabled(False)
        self.download_status.setText("")

        width = self.width_spin.value()
        height = self.height_spin.value()
        num_frames = self.frames_spin.value()
        frame_rate = self.fps_spin.value()

        self.video_worker = VideoWorker(
            api_key, full_prompt, width, height, num_frames, frame_rate, base_url
        )
        self.video_worker.status_update.connect(self._update_status)
        self.video_worker.progress_update.connect(self._update_progress)
        self.video_worker.result_ready.connect(self._on_result_ready)
        self.video_worker.error_occurred.connect(self._on_error)
        self.video_worker.finished.connect(self._on_worker_finished)
        self.video_worker.start()

    def _on_cancel(self):
        if self.video_worker and self.video_worker.isRunning():
            self.video_worker.stop()

    def _update_status(self, message):
        self.status_label.setText(message)

    def _update_progress(self, value):
        self.progress_bar.setValue(value)

    def _on_result_ready(self, url):
        self.current_video_url = url
        self.result_url_label.setText(f"🎬 视频链接: {url}")
        self.copy_url_btn.setEnabled(True)
        self.download_btn.setEnabled(True)
        self.open_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.status_label.setText("✅ 视频生成完成！点击链接可打开视频")

        if self.current_project:
            self.project_manager.add_video(self.current_project['id'], {
                "url": url,
                "prompt": self.prompt_input.toPlainText()
            })

    def _on_error(self, error_msg):
        self.status_label.setText(f"❌ {error_msg}")
        self.status_label.setStyleSheet("color: #e74c3c;")
        QMessageBox.critical(self, "错误", error_msg)
        self.status_label.setStyleSheet("color: #555;")

    def _on_worker_finished(self):
        self.generate_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

    def _on_url_clicked(self, event):
        if self.current_video_url:
            QDesktopServices.openUrl(QUrl(self.current_video_url))

    def _on_copy_url(self):
        if self.current_video_url:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.current_video_url)
            self.status_label.setText("✅ 链接已复制")

    def _on_download(self):
        if not self.current_video_url:
            return
        save_dir = os.path.join(_get_data_dir(), "videos")
        os.makedirs(save_dir, exist_ok=True)
        filename = f"agnes_video_{int(time.time())}.mp4"
        default_path = os.path.join(save_dir, filename)
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存视频", default_path, "MP4 视频 (*.mp4);;所有文件 (*)"
        )
        if not file_path:
            return
        self.download_btn.setEnabled(False)
        self.copy_url_btn.setEnabled(False)
        self.download_status.setText(f"正在下载...")

        self.download_worker = DownloadWorker(self.current_video_url, file_path)
        self.download_worker.progress_update.connect(self._update_download_progress)
        self.download_worker.finished_download.connect(self._on_download_finished)
        self.download_worker.download_error.connect(self._on_download_error)
        self.download_worker.start()

    def _update_download_progress(self, value):
        self.download_status.setText(f"下载进度: {value}%")

    def _on_download_finished(self, path):
        self.download_status.setText(f"✅ 下载完成: {path}")
        self.download_status.setStyleSheet("color: #27ae60;")
        self.download_btn.setEnabled(True)
        self.copy_url_btn.setEnabled(True)
        reply = QMessageBox.information(self, "下载完成", f"视频已保存到:\n{path}\n\n是否打开所在文件夹？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._open_folder(os.path.dirname(path))

    def _on_download_error(self, error_msg):
        self.download_status.setText(f"❌ {error_msg}")
        self.download_status.setStyleSheet("color: #e74c3c;")
        self.download_btn.setEnabled(True)
        self.copy_url_btn.setEnabled(True)

    def _on_open_video(self):
        if self.current_video_url:
            QDesktopServices.openUrl(QUrl(self.current_video_url))

    def _open_folder(self, path):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", path])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", path])
        except Exception:
            pass

    def _test_connection(self):
        api_key = self.api_key_input.text().strip()
        base_url = self.base_url_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "提示", "请填写 API Key")
            return
        if not base_url:
            QMessageBox.warning(self, "提示", "请填写 Base URL")
            return

        self.status_label.setText("🔗 正在测试连接...")
        QApplication.processEvents()

        try:
            normalized_url = base_url.rstrip("/")
            if normalized_url.endswith("/v1"):
                normalized_url = normalized_url[:-3]
            url = f"{normalized_url}/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {"model": "agnes-2.0-flash", "messages": [{"role": "user", "content": "test"}], "max_tokens": 10}

            response = requests.post(url, headers=headers, json=payload, timeout=15)

            if response.status_code == 200:
                self.status_label.setText("✅ 连接成功")
                QMessageBox.information(self, "连接成功", "✅ API 连接正常！")
            elif response.status_code == 401:
                self.status_label.setText("❌ 认证失败")
                QMessageBox.critical(self, "连接失败", "❌ API Key 无效或格式错误")
            else:
                error_data = {}
                try:
                    error_data = response.json()
                except Exception:
                    pass
                detail = error_data.get("detail", str(response.text)[:200])
                self.status_label.setText(f"❌ 连接失败 ({response.status_code})")
                QMessageBox.critical(self, "连接失败", f"❌ 请求失败 ({response.status_code}): {detail}")

        except requests.exceptions.Timeout:
            self.status_label.setText("❌ 连接超时")
        except requests.exceptions.ConnectionError:
            self.status_label.setText("❌ 网络连接失败")
        except Exception as e:
            self.status_label.setText("❌ 测试失败")

    def _save_config(self):
        try:
            config_file = _get_config_file()
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            existing = {}
            if os.path.exists(config_file):
                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                except Exception:
                    pass
            data_dir = _get_data_dir()
            geometry_bytes = bytes(self.saveGeometry().toBase64())
            config = {
                "data_dir": data_dir,
                "api_key": self.api_key_input.text(),
                "base_url": self.base_url_input.text(),
                "window_geometry": geometry_bytes.decode('utf-8') if geometry_bytes else ""
            }
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self.status_label.setText("✅ 配置已保存")
            QTimer.singleShot(2000, lambda: self.status_label.setText("就绪"))
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            logging.error(f"保存配置失败: {error_detail}")
            QMessageBox.critical(self, "保存失败", f"保存配置失败：\n{str(e)}\n\n日志路径：{os.path.join(_get_data_dir(), 'error.log')}")

    def _load_config(self):
        try:
            config_file = _get_config_file()
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                self.api_key_input.blockSignals(True)
                self.base_url_input.blockSignals(True)
                self.api_key_input.setText(config.get("api_key", ""))
                self.base_url_input.setText(config.get("base_url", API_BASE))
                self.api_key_input.blockSignals(False)
                self.base_url_input.blockSignals(False)
                geometry = config.get("window_geometry", "")
                if geometry:
                    try:
                        self.restoreGeometry(geometry.encode('utf-8'))
                    except Exception:
                        pass
        except Exception as e:
            logging.error(f"加载配置失败: {str(e)}")

    def _generate_comic_script(self):
        api_key = self.api_key_input.text().strip()
        desc = self.comic_desc_input.toPlainText().strip()
        style = self.comic_style_combo.currentText()

        if not api_key:
            QMessageBox.warning(self, "提示", "请填写 API Key")
            return
        if not desc:
            QMessageBox.warning(self, "提示", "请填写漫剧描述")
            return

        context = self._get_context_description()
        prompt = f"""请根据以下描述生成一个漫剧分镜剧本。

【漫剧描述】{desc}
【风格】{style}

{context if context else ''}

请生成 3-5 个场景的分镜剧本，每个场景包含：
1. 场景编号和标题
2. 场景描述（环境、氛围、时间）
3. 角色动作和对话
4. 镜头语言（远景/中景/特写等）

格式示例：
场景1: [场景标题]
- 环境描述: ...
- 角色: ...
- 动作: ...
- 镜头: ...
- 对话: ..."""

        self.comic_status_label.setText("✍️ AI 正在生成剧本...")
        self.comic_script_display.clear()

        self.chat_worker = ChatWorker(api_key, [{"role": "user", "content": prompt}], self.base_url_input.text().strip())
        self.chat_worker.result_ready.connect(self._on_comic_script_result)
        self.chat_worker.error_occurred.connect(lambda e: self.comic_status_label.setText(f"❌ {e}"))
        self.chat_worker.start()

    def _on_comic_script_result(self, script):
        self.comic_script_display.setPlainText(script)
        self.comic_status_label.setText("✅ 剧本生成完成，请手动添加场景或点击批量生成")

    def _add_manual_scene(self):
        if not self.current_project:
            project = self.project_manager.create_project(f"漫剧项目_{datetime.now().strftime('%m%d')}")
            self.current_project = project
            self._refresh_project_list()

        scene_num = len(self.current_project.get('scenes', [])) + 1
        prompt, ok = QInputDialog.getMultiLineText(
            self, "添加场景",
            f"场景 {scene_num} 描述:\n\n例如:\n主角在樱花树下漫步，微风吹过她的长发...",
            ""
        )
        if ok and prompt.strip():
            scene = {
                "scene_number": scene_num,
                "prompt": prompt.strip(),
                "status": "pending"
            }
            self.project_manager.add_scene(self.current_project['id'], scene)
            self._refresh_scene_list()

    def _refresh_scene_list(self):
        self.scene_list.clear()
        if self.current_project:
            for scene in self.current_project.get('scenes', []):
                status_icon = "⏳" if scene['status'] == 'pending' else "✅" if scene['status'] == 'completed' else "❌"
                item = QListWidgetItem(f"{status_icon} 场景{scene.get('scene_number', '')}: {scene.get('prompt', '')[:50]}...")
                item.setData(Qt.UserRole, scene['id'])
                item.setToolTip(scene.get('prompt', ''))
                self.scene_list.addItem(item)

    def _on_scene_double_clicked(self, item):
        scene_id = item.data(Qt.UserRole)
        if scene_id:
            self._generate_single_scene(scene_id)

    def _generate_single_scene(self, scene_id):
        if not self.current_project:
            return
        scene = None
        for s in self.current_project.get('scenes', []):
            if s['id'] == scene_id:
                scene = s
                break
        if not scene:
            return

        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "提示", "请填写 API Key")
            return

        context = self._get_context_description()
        full_prompt = f"{context}\n\n{scene['prompt']}" if context else scene['prompt']

        self.comic_status_label.setText(f"🎬 正在生成场景 {scene['scene_number']}...")

        self.video_worker = VideoWorker(
            api_key, full_prompt,
            width=self.width_spin.value(),
            height=self.height_spin.value(),
            num_frames=self.frames_spin.value(),
            frame_rate=self.fps_spin.value(),
            base_url=self.base_url_input.text().strip()
        )
        self.video_worker.status_update.connect(self.comic_status_label.setText)
        self.video_worker.result_ready.connect(lambda url: self._on_scene_video_ready(scene_id, url))
        self.video_worker.error_occurred.connect(lambda e: self.comic_status_label.setText(f"❌ {e}"))
        self.video_worker.start()

    def _on_scene_video_ready(self, scene_id, url):
        self.project_manager.update_scene(
            self.current_project['id'], scene_id,
            {"status": "completed", "video_url": url}
        )
        self._refresh_scene_list()
        self.comic_status_label.setText(f"✅ 场景视频已生成！")
        QDesktopServices.openUrl(QUrl(url))

    def _generate_all_scenes(self):
        if not self.current_project:
            QMessageBox.information(self, "提示", "请先选择或创建一个项目")
            return

        scenes = self.current_project.get('scenes', [])
        pending_scenes = [s for s in scenes if s['status'] == 'pending']

        if not pending_scenes:
            QMessageBox.information(self, "提示", "没有待生成的场景")
            return

        reply = QMessageBox.question(
            self, "批量生成",
            f"将批量生成 {len(pending_scenes)} 个场景的视频，这可能需要较长时间。\n\n是否继续？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        for scene in pending_scenes:
            self._generate_single_scene(scene['id'])
            QApplication.processEvents()

    def closeEvent(self, event):
        try:
            self._save_config()
        except Exception:
            pass
        event.accept()


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    log_file = setup_logging()
    sys.excepthook = global_exception_handler

    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        window = AgnesVideoApp()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        error_msg = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        logging.error(error_msg)
        try:
            QMessageBox.critical(
                None, "启动错误",
                f"程序启动失败！\n\n错误：{str(e)}\n\n日志：{log_file}"
            )
        except Exception:
            print(f"启动失败！日志：{log_file}", file=sys.stderr)
            input("按回车键退出...")
        sys.exit(1)


if __name__ == "__main__":
    main()
