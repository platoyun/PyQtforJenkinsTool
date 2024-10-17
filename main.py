import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
                             QComboBox, QFormLayout, QLineEdit, QHBoxLayout, QLabel, QCheckBox,
                             QScrollArea, QMessageBox, QFrame, QGridLayout)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QSize
from PyQt6.QtGui import QFont, QPalette, QColor
from playwright.sync_api import sync_playwright
import time
import configparser
import platform
import subprocess

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def print_debug_info():
    print(f"Current working directory: {os.getcwd()}")
    print(f"sys.executable: {sys.executable}")
    print(f"sys._MEIPASS: {getattr(sys, '_MEIPASS', 'Not running from PyInstaller')}")
    print(f"Platform: {platform.platform()}")
    print(f"Python version: {platform.python_version()}")
    
    # 打印环境变量
    print("Environment variables:")
    for key, value in os.environ.items():
        print(f"  {key}: {value}")

# 设置 Playwright 浏览器路径
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = resource_path("playwright-browsers")

# def install_playwright_browser():
#     try:
#         print("Attempting to install Playwright browser...")
#         result = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
#                                 check=True, capture_output=True, text=True)
#         print(f"Playwright browser installation output: {result.stdout}")
#         print("Playwright browser installed successfully")
#     except subprocess.CalledProcessError as e:
#         print(f"Failed to install Playwright browser: {e}")
#         print(f"Error output: {e}")

# 在应用程序启动时调用这个函数
# install_playwright_browser()

def get_chromium_executable():
    if getattr(sys, 'frozen', False):
        # 运行在打包的环境中
        base_path = sys._MEIPASS
    else:
        # 运行在开发环境中
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    system = platform.system()
    if system == "Windows":
        return os.path.join(base_path, 'playwright-browsers', 'chromium-1134', 'chrome-win', 'chrome.exe')
    elif system == "Darwin":  # macOS
        return os.path.join(base_path, 'playwright-browsers', 'chromium-1134', 'chrome-mac', 'Chromium.app', 'Contents', 'MacOS', 'Chromium')
    elif system == "Linux":
        return os.path.join(base_path, 'playwright-browsers', 'chromium-1134', 'chrome-linux', 'chrome')
    else:
        raise OSError(f"Unsupported operating system: {system}")

# 获取 Chromium 可执行文件路径
chromium_path = get_chromium_executable()

class WorkerThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, show_browser, params, pause_time):
        super().__init__()
        self.show_browser = show_browser
        self.params = params
        self.pause_time = pause_time

    def get_browser_executable_path(self):
        system = platform.system()
        if system == "Windows":
            path = resource_path("playwright-browsers/chromium-1134/chrome-win/chrome.exe")
        elif system == "Darwin":  # macOS
            path = resource_path("playwright-browsers/chromium-1134/chrome-mac/Chromium.app/Contents/MacOS/Chromium")
        else:
            raise OSError(f"Unsupported operating system: {system}")
        
        print(f"Browser executable path: {path}")
        print(f"Path exists: {os.path.exists(path)}")
        return path

    def run(self):
        print("Playwright execution starting...")
        print_debug_info()
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=not self.show_browser,
                    executable_path=chromium_path
                )
                print("Browser launched successfully")
                page = browser.new_page()
                context = browser.new_context()
                
                # 使用参数
                for key, value in self.params.items():
                    print(f"Using parameter in Playwright: {key} = {value}")

                # 这里添加您的 Playwright 测试脚本
                page.goto("https://www.example.com")  # 尝试打开一个网页
                print(f"Page title: {page.title()}")

                # 暂停
                print(f"Browser opened. Pausing for {self.pause_time} seconds...")
                time.sleep(self.pause_time)
                print("Pause finished. Closing browser...")

                browser.close()
            self.finished.emit()
        except Exception as e:
            print(f"An error occurred: {e}")
            print(f"Chromium path: {chromium_path}")
            import traceback
            traceback.print_exc()
            self.error.emit(f"An error occurred: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Tool")
        self.setMinimumWidth(700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #E8F5E9;
            }
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #1B5E20;
            }
            QComboBox, QLineEdit {
                font-size: 13px;
                padding: 8px;
                border: 1px solid #4CAF50;
                border-radius: 4px;
                background-color: #FFFFFF;
                color: #1B5E20;
            }
            QPushButton {
                font-size: 14px;
                padding: 10px;
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QScrollArea, QWidget#FormWidget {
                background-color: #FFFFFF;
                border: 1px solid #81C784;
                border-radius: 4px;
            }
            QCheckBox {
                font-size: 13px;
                color: #1B5E20;
            }
        """)
        
        self.config = configparser.ConfigParser()
        self.load_config()

        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # 系统选择
        system_layout = QHBoxLayout()
        system_label = QLabel("Choose the test mobile system:")
        self.system_combo = QComboBox()
        self.system_combo.addItems(['ios', 'aos'])
        self.system_combo.currentTextChanged.connect(self.update_params)
        system_layout.addWidget(system_label)
        system_layout.addWidget(self.system_combo)
        main_layout.addLayout(system_layout)

        # 浏览器显示选项
        self.show_browser_checkbox = QCheckBox("Display browser")
        main_layout.addWidget(self.show_browser_checkbox)

        # 参数表单
        params_label = QLabel("Parameters:")
        main_layout.addWidget(params_label)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(250)
        self.scroll_area.setMaximumHeight(400)
        main_layout.addWidget(self.scroll_area)

        # 暂停时间输入框
        pause_layout = QHBoxLayout()
        pause_label = QLabel("Browser auto close time (seconds):")
        self.pause_input = QLineEdit()
        self.pause_input.setText("10")
        pause_layout.addWidget(pause_label)
        pause_layout.addWidget(self.pause_input)
        main_layout.addLayout(pause_layout)

        # 开始按钮
        self.button = QPushButton("Start")
        self.button.clicked.connect(self.start_process)
        self.button.setFixedSize(200, 50)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.worker = None

        # 初始化显示默认系统的参数
        self.update_params(self.system_combo.currentText())

    def load_config(self):
        if os.path.exists('config.ini'):
            self.config.read('config.ini')
        else:
            self.config['ios'] = {}
            self.config['aos'] = {}
            with open('config.ini', 'w') as configfile:
                self.config.write(configfile)

    def update_params(self, system):
        form_widget = QWidget()
        form_widget.setObjectName("FormWidget")
        grid_layout = QGridLayout(form_widget)
        grid_layout.setSpacing(15)
        grid_layout.setContentsMargins(15, 15, 15, 15)

        if system in self.config:
            for row, (key, value) in enumerate(self.config[system].items()):
                label = QLabel(key)
                label.setStyleSheet("font-weight: normal; color: #2E7D32; text-align: left;")
                label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                
                line_edit = QLineEdit(value)
                line_edit.setMinimumWidth(300)  # 设置最小宽度
                
                grid_layout.addWidget(label, row, 0)
                grid_layout.addWidget(line_edit, row, 1)
            
            grid_layout.setColumnStretch(1, 1)  # 让第二列（value 列）占据更多空间
        else:
            grid_layout.addWidget(QLabel("No configuration"), 0, 0, 1, 2)

        self.scroll_area.setWidget(form_widget)
        form_widget.adjustSize()
        self.scroll_area.setMinimumWidth(form_widget.width() + 30)

        self.adjustSize()
        current_size = self.size()
        new_height = min(current_size.height() + 50, 800)
        new_width = max(current_size.width(), 800)  # 确保窗口宽度至少为 800
        self.resize(new_width, new_height)

    def start_process(self):
        print("Start button clicked, preparing to run Playwright...")
        self.button.setEnabled(False)

        # 读取当前选择的系统的配置
        system = self.system_combo.currentText()
        params = {}

        # 从界面上读取用户可能修改的值
        form_widget = self.scroll_area.widget()
        grid_layout = form_widget.layout()
        for i in range(grid_layout.rowCount()):
            key_item = grid_layout.itemAtPosition(i, 0)
            value_item = grid_layout.itemAtPosition(i, 1)
            if key_item and value_item:
                key = key_item.widget().text()
                value = value_item.widget().text()
                params[key] = value

        print("Parameters being used:")
        for key, value in params.items():
            print(f"{key} = {value}")

        show_browser = self.show_browser_checkbox.isChecked()
        pause_time = int(self.pause_input.text())
        self.worker = WorkerThread(show_browser, params, pause_time)
        self.worker.finished.connect(self.process_finished)
        self.worker.error.connect(self.process_error)
        self.worker.start()

    def process_finished(self):
        self.button.setEnabled(True)
        print("Playwright execution finished")

    def process_error(self, error_message):
        self.button.setEnabled(True)
        print(f"Error: {error_message}")
        QMessageBox.critical(self, "Error", error_message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
