import os, re, nuke
# PySide6 / PySide2 compatibility
try:
    from PySide6 import QtWidgets, QtCore, QtGui
except Exception:
    from PySide2 import QtWidgets, QtCore, QtGui

# Use pipeline gloss root
try:
    from gloss_utils.paths_nyc import GLOSS_ROOT
except Exception:
    GLOSS_ROOT = "/Volumes/san-01/GlossPost"

LINEUP_PATTERN = re.compile(r"Line_up_v(\d+)\.nk$", re.IGNORECASE)
_lineup_browser_instance = None  # singleton

class LineupBrowser(QtWidgets.QWidget):
    def __init__(self):
        super(LineupBrowser, self).__init__()
        self.setWindowTitle("Lineup Browser")
        self.setGeometry(200, 200, 500, 600)

        self.projects_directory = GLOSS_ROOT
        self._set_global_font()

        self.layout = QtWidgets.QVBoxLayout(self)

        self.directory_label = QtWidgets.QLabel(f"Directory: {self.projects_directory}")
        self.layout.addWidget(self.directory_label)

        self.filter_input = QtWidgets.QLineEdit()
        self.filter_input.setPlaceholderText("Filter projects...")
        self.filter_input.textChanged.connect(self._filter_projects)
        self.layout.addWidget(self.filter_input)

        self.project_list_widget = QtWidgets.QListWidget()
        self.layout.addWidget(self.project_list_widget)

        button_layout = QtWidgets.QHBoxLayout()
        self.refresh_button = QtWidgets.QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._load_projects)
        button_layout.addWidget(self.refresh_button)

        self.set_directory_button = QtWidgets.QPushButton("Set Directory")
        self.set_directory_button.clicked.connect(self._set_directory)
        button_layout.addWidget(self.set_directory_button)

        self.layout.addLayout(button_layout)

        self.project_list_widget.itemClicked.connect(self._handle_project_click)
        self.all_project_names = []

        self._load_projects()

    def _set_global_font(self):
        font = QtGui.QFont()
        font.setPointSize(12)
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        app.setFont(font)

    def _set_directory(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Projects Directory", self.projects_directory)
        if directory:
            self.projects_directory = directory
            self.directory_label.setText(f"Directory: {self.projects_directory}")
            self._load_projects()

    def _load_projects(self):
        self.project_list_widget.clear()
        self.all_project_names = []

        if not os.path.exists(self.projects_directory):
            QtWidgets.QMessageBox.critical(self, "Error", f"Directory not found: {self.projects_directory}")
            return

        project_names = [name for name in os.listdir(self.projects_directory)
                         if os.path.isdir(os.path.join(self.projects_directory, name))]

        if not project_names:
            self.project_list_widget.addItem("No projects found.")
            return

        for project in sorted(project_names):
            self.all_project_names.append(project)
            item = QtWidgets.QListWidgetItem(project)
            item.setData(QtCore.Qt.UserRole, os.path.join(self.projects_directory, project))
            self.project_list_widget.addItem(item)

    def _filter_projects(self, text):
        self.project_list_widget.clear()
        t = (text or "").lower()
        for project in self.all_project_names:
            if t in project.lower():
                item = QtWidgets.QListWidgetItem(project)
                item.setData(QtCore.Qt.UserRole, os.path.join(self.projects_directory, project))
                self.project_list_widget.addItem(item)

    def _handle_project_click(self, item):
        project_path = item.data(QtCore.Qt.UserRole)
        progress_folder = self._find_progress_folder(project_path)

        if not progress_folder:
            QtWidgets.QMessageBox.warning(self, "Error", "PROGRESS-###### folder not found.")
            return

        nuke_folder = os.path.join(progress_folder, "NUKE")
        if not os.path.exists(nuke_folder):
            os.makedirs(nuke_folder)

        lineup_path = self._find_latest_lineup_comp(nuke_folder)
        if lineup_path:
            nuke.scriptOpen(lineup_path)
            nuke.message(f"Opened latest lineup comp:\n{lineup_path}")
        else:
            confirm = QtWidgets.QMessageBox.question(
                self,
                "Create New Lineup",
                "No existing lineup comp found. Create a new Line_up_v01.nk?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if confirm == QtWidgets.QMessageBox.Yes:
                new_lineup_path = os.path.join(nuke_folder, "Line_up_v01.nk")
                nuke.scriptSaveAs(new_lineup_path)
                nuke.message(f"Created new lineup comp:\n{new_lineup_path}")
            else:
                return
        self.close()

    def _find_progress_folder(self, project_path):
        for folder in os.listdir(project_path):
            p = os.path.join(project_path, folder)
            if folder.startswith("PROGRESS-") and os.path.isdir(p):
                return p
        return None

    def _find_latest_lineup_comp(self, nuke_folder):
        lineup_files = []
        for f in os.listdir(nuke_folder):
            m = LINEUP_PATTERN.match(f)
            if m:
                lineup_files.append((int(m.group(1)), f))
        if lineup_files:
            latest = max(lineup_files, key=lambda x: x[0])
            return os.path.join(nuke_folder, latest[1])
        return None

def launch_lineup_browser():
    global _lineup_browser_instance
    # singleton instance
    try:
        visible = _lineup_browser_instance and _lineup_browser_instance.isVisible()
    except Exception:
        visible = False
    if not visible:
        _lineup_browser_instance = LineupBrowser()
        _lineup_browser_instance.show()
    else:
        _lineup_browser_instance.raise_()
        _lineup_browser_instance.activateWindow()
