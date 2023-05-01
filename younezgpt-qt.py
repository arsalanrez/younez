import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, \
    QScrollArea, QFileDialog, QInputDialog
from PyQt5.QtCore import Qt, QThreadPool, QRunnable, pyqtSignal, QObject
from PyQt5.QtGui import QCursor, QPalette, QColor
import openai
import YounezGPTKeys

# Initialize OpenAI API
openai.api_key = ""

# Initialize Qt Thread Pool
threadpool = QThreadPool()
threadpool.setMaxThreadCount(1)


class Worker(QRunnable):
    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt

    def run(self):
        # Get response from OpenAI API
        self.response = get_res(self.prompt)


class CompletedSignal(QObject):
    completed = pyqtSignal(object)


def get_res(prompt):
    # Set up the model and prompt
    model_engine = "text-davinci-003"

    # Generate a response
    completion = openai.Completion.create(
        engine=model_engine,
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )

    return completion.choices[0].text


# Define GUI window
class YounezGPT(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize OpenAI API keys
        self.keys = YounezGPTKeys.YounezGPTKeys()

        # Set window size
        self.resize(400, 400)

        # Create input and output widgets
        self.input = QLineEdit()
        self.output_label = QLabel(wordWrap=True)

        # Create buttons
        self.ask_button = QPushButton("Ask")
        self.clear_button = QPushButton("Clear")
        self.exit_button = QPushButton("Exit")
        self.export_button = QPushButton("Export")
        self.api_key_button = QPushButton("Set API Key")
        self.add_key_button = QPushButton("Add Key")
        self.remove_key_button = QPushButton("Remove Key")

        # Connect buttons to callbacks
        self.ask_button.clicked.connect(self.ask_question)
        self.clear_button.clicked.connect(self.clear_input)
        self.exit_button.clicked.connect(self.close)
        self.export_button.clicked.connect(self.export_response)
        self.api_key_button.clicked.connect(self.set_api_key)
        self.add_key_button.clicked.connect(self.add_api_key)
        self.remove_key_button.clicked.connect(self.remove_api_key)

        # Create scroll area for output label
        self.scroll_area = QScrollArea(widgetResizable=True)
        self.scroll_area.setWidget(self.output_label)

        # Create layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Ask a question:"))
        layout.addWidget(self.input)
        layout.addWidget(self.ask_button)
        layout.addWidget(self.clear_button)
        layout.addWidget(self.export_button)
        layout.addWidget(self.api_key_button)
        layout.addWidget(self.add_key_button)
        layout.addWidget(self.remove_key_button)
        layout.addWidget(self.exit_button)
        layout.addWidget(QLabel("Response:"))
        layout.addWidget(self.scroll_area)

        # Set layout
        self.setLayout(layout)

    def set_api_key(self):
        # Get list of API key names
        key_names = self.keys.get_key_names()

        if len(key_names) == 0:
            # Show message if no keys exist
            QMessageBox.information(self, "Set API Key", "No API keys exist. Add a key before setting the API key.")
        elif len(key_names) == 1:
            # Set current key automatically if only one key exists
            self.keys.set_current_key(key_names[0])

            # Show confirmation message
            QMessageBox.information(self, "Set API Key", "API key set successfully.")
        else:
            # Ask user to select API key
            key, ok = QInputDialog.getItem(self, "Set API Key", "Select an OpenAI API key:", key_names)

            if ok:
                # Set selected API key as current key
                self.keys.set_current_key(key)

                # Show confirmation message
                QMessageBox.information(self, "Set API Key", "API key set successfully.")

    def clear_input(self):
        self.input.clear()
        self.output_label.clear()

    def export_response(self):
        # Get file path from user
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Response", "", "Text files (*.txt)")

        if file_path:
            # Write response to file
            with open(file_path, "w") as f:
                f.write(self.output_label.text())

    def set_loading_state(self, x):
        if x:
            self.setCursor(QCursor(Qt.WaitCursor))
            self.ask_button.setEnabled(False)
            self.clear_button.setEnabled(False)
            self.export_button.setEnabled(False)
            self.api_key_button.setEnabled(False)
            self.add_key_button.setEnabled(False)
            self.remove_key_button.setEnabled(False)
        else:
            self.setCursor(QCursor(Qt.ArrowCursor))
            self.ask_button.setEnabled(True)
            self.clear_button.setEnabled(True)
            self.export_button.setEnabled(True)
            self.api_key_button.setEnabled(True)
            self.add_key_button.setEnabled(True)
            self.remove_key_button.setEnabled(True)

    def add_api_key(self):
        # Get new API key from user
        key, ok = QInputDialog.getText(self, "Add API Key", "Enter the name and OpenAI API key (separated by a comma):")

        if ok:
            # Split input into name and key
            name, key = key.split(",")

            # Add new key to list
            self.keys.add_key(name.strip(), key.strip())

            # Show confirmation message
            QMessageBox.information(self, "Add API Key", "API key added successfully.")

    def remove_api_key(self):
        # Get list of API key names
        key_names = self.keys.get_key_names()

        if len(key_names) == 0:
            # Show message if no keys exist
            QMessageBox.information(self, "Remove API Key", "No API keys exist.")
        elif len(key_names) == 1:
            # Show message if only one key exists
            QMessageBox.information(self, "Remove API Key", "You cannot remove the only API key that exists.")
        else:
            # Ask user to select API key to remove
            key, ok = QInputDialog.getItem(self, "Remove API Key", "Select an OpenAI API key to remove:", key_names)

            if ok:
                # Remove selected API key
                self.keys.remove_key(key)

                # Show confirmation message
                QMessageBox.information(self, "Remove API Key", "API key removed successfully.")

    def ask_question(self):
        # Get question from input field
        question = self.input.text()

        if not question:
            # Show error message if no question is entered
            QMessageBox.warning(self, "Error", "Please enter a question.")
            return

        # Show loading message
        self.set_loading_state(True)

        # Create worker thread for getting response
        worker = Worker(question)
        signal = CompletedSignal()
        signal.completed.connect(self.display_response)
        worker.signals = signal

        # Start worker in thread pool
        threadpool.start(worker)

    def display_response(self, response):
        # Display response in output label
        self.output_label.setText(response.response)

        # Reset loading state
        self.set_loading_state(False)


# Create application and window
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Set modern and flat theme
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.Highlight, QColor(142, 45, 197).lighter())
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    window = YounezGPT()
    window.setWindowTitle("YounezGPT")
    window.show()

    # Run application
    sys.exit(app.exec_())
