import shutil
import sys
import uuid
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSlot
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QMainWindow,
    QLineEdit,
    QVBoxLayout,
    QPushButton,
    QWidget,
    QLabel,
    QApplication,
    QHBoxLayout,
)
from pyqtwaitingspinner import SpinnerParameters, WaitingSpinner

from core import ConvertAPI

STYLE_CLASS = "class"
DEFAULT_STYLE = "default"
CONVERT_SOURCE_STYLE = "source"
OUTPUT_STYLE = "output"
HINT_LABEL = "hint_label"


def class_str(*args) -> str:
    return ' '.join(args)


# custom input to support drag-n-drop
class DragNDropQLabel(QLabel):
    source_input = None
    def __init__(self,
                 parent,
                 source_input: QLineEdit,
                 convert_api: ConvertAPI,
                 allow_paks: bool,
                 *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.source_input = source_input
        self.convert_api = convert_api
        self.allow_paks = allow_paks
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        url = event.mimeData().urls()[0]
        drop_path = Path(url.toLocalFile())

        if drop_path.is_dir() or (self.allow_paks and self.convert_api.is_pak(drop_path)):
            self.source_input.setText(str(drop_path.resolve()))
        else:
            self.source_input.setText(str(drop_path.parent.resolve()))


# thread object to support converting
class ConvertQThread(QThread):
    def __init__(self, parent,
                 convert_api: ConvertAPI,
                 source_path_input: str,
                 output_path_input: str):
        super().__init__(parent)
        self.convert_api: ConvertAPI = convert_api
        self.source_path_input: str = source_path_input
        self.output_path_input: str = output_path_input

    def run(self):
        source_path: Path = Path(self.source_path_input).resolve()
        output_path: Path = Path(self.output_path_input).resolve()

        if self.convert_api.is_pak(source_path):
            output_tmp = output_path / f'tmp_{uuid.uuid4()}'
            pak_tmp = output_tmp / source_path.stem
            pak_tmp.mkdir(parents=True, exist_ok=True)
            self.convert_api.unpack_file(source_path, pak_tmp)
            self.convert_api.convert(output_tmp, output_path, False)
            shutil.rmtree(str(output_tmp))
        else:
            self.convert_api.convert(source_path, output_path, False)


# top level UI pyqt6 object
class ConverterUIWindow(QMainWindow):
    def __init__(self,
                 default_source_path: Path,
                 default_output_path: Path,
                 path_to_resources: Path,
                 convert_api: ConvertAPI) -> None:
        super().__init__()
        self.convert_api: ConvertAPI = convert_api

        # main window's name and size:
        self.setWindowTitle("Eclip5e™ Convert2Toolkit")
        self.setWindowIcon(QIcon(str(path_to_resources / 'convert.ico')))
        self.setGeometry(300, 300, 800, 600)
        self.setMinimumSize(800, 600)

        # Timer to give slight pause before checking path
        self.debounce = QTimer()
        self.debounce.setInterval(500)
        self.debounce.setSingleShot(True)
        # noinspection PyUnresolvedReferences
        self.debounce.timeout.connect(self.check_path)

        # text input for source path
        self.source_text_input = QLineEdit(self)
        self.source_text_input.setProperty(STYLE_CLASS, class_str(DEFAULT_STYLE))
        # noinspection PyUnresolvedReferences
        self.source_text_input.textChanged.connect(self.debounce.start)
        # noinspection PyUnresolvedReferences
        self.source_text_input.textChanged.connect(self.disable_convert_button)

        # text input for output path
        self.output_text_input = QLineEdit(self)
        self.output_text_input.setText(str(default_output_path.resolve()))
        self.output_text_input.setProperty(STYLE_CLASS, class_str(DEFAULT_STYLE))

        # main convert button
        self.convert_button = QPushButton("Convert")
        self.convert_button.setProperty(STYLE_CLASS, class_str(DEFAULT_STYLE))
        self.convert_button.setObjectName("convert_button")
        self.convert_button.setToolTip("Provide valid path for converting")
        # noinspection PyUnresolvedReferences
        self.convert_button.clicked.connect(self.run_convert)
        self.enable_convert_button(False)

        # loading spinner for convert button
        spin_pars = SpinnerParameters(
            disable_parent_when_spinning=True,
            inner_radius=4,
            line_length=10,
            line_width=2,
            number_of_lines=12,
            trail_fade_percentage=80
        )
        self.spinner = WaitingSpinner(self.convert_button, spin_pars)

        # ui group for input and convert button
        self.convert_container = QHBoxLayout()
        self.convert_container.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.convert_container.addWidget(self.source_text_input)
        self.convert_container.addWidget(self.convert_button)
        self.convert_container_widget = DragNDropQLabel(
            parent=self,
            source_input=self.source_text_input,
            convert_api=self.convert_api,
            allow_paks=True
        )
        self.convert_container_widget.setLayout(self.convert_container)
        self.convert_container_widget.setProperty(STYLE_CLASS, class_str(CONVERT_SOURCE_STYLE))

        # ui group for output path
        self.output_container = QHBoxLayout()
        self.output_container.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.output_container.addWidget(self.output_text_input)
        self.output_container_widget = DragNDropQLabel(
            parent=self,
            source_input=self.output_text_input,
            convert_api=self.convert_api,
            allow_paks=False
        )
        self.output_container_widget.setLayout(self.output_container)
        self.output_container_widget.setProperty(STYLE_CLASS, class_str(OUTPUT_STYLE, CONVERT_SOURCE_STYLE))

        # hint label for user on input
        self.convert_info_label = QLabel("Drop file/directory or enter path to convert")
        self.convert_info_label.setProperty(STYLE_CLASS, class_str(DEFAULT_STYLE, HINT_LABEL))

        # hint label for user on output
        self.output_info_label = QLabel("Drop directory or enter output path")
        self.output_info_label.setProperty(STYLE_CLASS, class_str(DEFAULT_STYLE, HINT_LABEL))

        # setup main container for window
        self.main_container = QVBoxLayout()
        self.main_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_container.addWidget(self.convert_info_label)
        self.main_container.addWidget(self.convert_container_widget)
        self.main_container.addWidget(self.output_info_label)
        self.main_container.addWidget(self.output_container_widget)

        # assemble central widget
        self.widget = QWidget()
        self.widget.setLayout(self.main_container)
        self.setCentralWidget(self.widget)

        # this is done late to detect change
        if not default_source_path is None:
            self.source_text_input.setText(str(default_source_path.resolve()))

    def check_path(self):
        if self.convert_api.is_valid_source(Path(self.source_text_input.text())):
            self.enable_convert_button(True)
        else:
            # TODO: show a message/label to notify user that path is invalid?
            pass

    def disable_convert_button(self):
        self.enable_convert_button(False)

    def enable_convert_button(self, enable: bool = True):
        if enable:
            self.convert_button.setEnabled(True)
            self.convert_button.setToolTip("Convert Files")
        else:
            self.convert_button.setEnabled(False)
            self.convert_button.setToolTip("Provide valid path for converting")

    def run_convert(self):
        self.spinner.start()

        # spawn convert thread for processing
        convert_qthread = ConvertQThread(
            parent=self,
            convert_api=self.convert_api,
            source_path_input=self.source_text_input.text(),
            output_path_input=self.output_text_input.text()
        )
        convert_qthread.finished.connect(self._convert_finished)
        convert_qthread.start()

    @pyqtSlot()
    def _convert_finished(self):
        # TODO: may need to do cleanup?  notify user?
        self.spinner.stop()


# Controlling object for GUI
class ConvertGUI:
    def __init__(self,
                 convert_api: ConvertAPI,
                 path_to_root: Path,
                 path_to_resources: Path):
        self.convert_api: ConvertAPI = convert_api
        self.path_to_root: Path = path_to_root
        self.path_to_resources: Path = path_to_resources

    def run(self):
        """
            Profound description
        """
        app = QApplication([])

        # load in qss for custom styling
        with open(f"{self.path_to_resources}/style.qss", "r") as f:
            _style = f.read()
            app.setStyleSheet(_style)

        # create and launch ui window
        window = ConverterUIWindow(
            # TODO: should default paths come from settings?
            default_source_path=self.path_to_root / 'convert',
            default_output_path=self.path_to_root / 'convert',
            path_to_resources=self.path_to_resources,
            convert_api=self.convert_api
        )

        window.show()
        sys.exit(app.exec())
