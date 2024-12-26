from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QComboBox, QCheckBox, QPushButton,
                            QGroupBox, QGridLayout, QDoubleSpinBox, QToolButton,
                            QSpinBox, QTextEdit)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

class SlackTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Shortcut
        shortcut_layout = self._create_field_with_help(
            "Shortcut:", 
            QLineEdit("ctrl+shift+s"),
            "Keyboard shortcut to activate Slack transcription"
        )
        layout.addLayout(shortcut_layout)
        
        # Model Selection Group
        model_group = QGroupBox("Model")
        model_layout = QGridLayout()
        
        # Model Type
        model_type_label = QLabel("Model Type:")
        self.model_type_combo = QComboBox()
        self.model_type_combo.addItems(["faster_whisper", "openai"])
        self.model_type_combo.currentTextChanged.connect(self._on_model_type_changed)
        model_layout.addWidget(model_type_label, 0, 0)
        model_layout.addLayout(
            self._add_help_button("Select the speech-to-text model provider", self.model_type_combo),
            0, 1
        )
        
        # Stacked layouts for different model types
        self.faster_whisper_widget = QWidget()
        self.openai_widget = QWidget()
        
        # Faster Whisper Options
        fw_layout = QGridLayout(self.faster_whisper_widget)
        
        # Model
        fw_model_label = QLabel("Model:")
        self.fw_model_combo = QComboBox()
        self.fw_model_combo.addItems(["base", "tiny", "large"])
        fw_layout.addWidget(fw_model_label, 0, 0)
        fw_layout.addLayout(
            self._add_help_button("Select the Whisper model size", self.fw_model_combo),
            0, 1
        )
        
        # Compute Type
        compute_label = QLabel("Compute Type:")
        self.compute_combo = QComboBox()
        self.compute_combo.addItems(["default", "float16"])
        fw_layout.addWidget(compute_label, 1, 0)
        fw_layout.addLayout(
            self._add_help_button("Select computation precision", self.compute_combo),
            1, 1
        )
        
        # Device
        device_label = QLabel("Device:")
        self.device_combo = QComboBox()
        self.device_combo.addItems(["cuda", "cpu", "auto"])
        fw_layout.addWidget(device_label, 2, 0)
        fw_layout.addLayout(
            self._add_help_button("Select processing device", self.device_combo),
            2, 1
        )
        
        # Temperature
        temp_label = QLabel("Temperature:")
        self.fw_temp_spin = QDoubleSpinBox()
        self.fw_temp_spin.setRange(0.0, 1.0)
        self.fw_temp_spin.setSingleStep(0.1)
        fw_layout.addWidget(temp_label, 3, 0)
        fw_layout.addLayout(
            self._add_help_button("Sampling temperature (higher = more random)", self.fw_temp_spin),
            3, 1
        )
        
        # OpenAI Options
        openai_layout = QGridLayout(self.openai_widget)
        
        # Model
        openai_model_label = QLabel("Model:")
        self.openai_model_combo = QComboBox()
        self.openai_model_combo.addItems(["whisper-1"])
        openai_layout.addWidget(openai_model_label, 0, 0)
        openai_layout.addLayout(
            self._add_help_button("Select OpenAI model", self.openai_model_combo),
            0, 1
        )
        
        # API Key
        api_key_label = QLabel("API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        openai_layout.addWidget(api_key_label, 1, 0)
        openai_layout.addLayout(
            self._add_help_button("Your OpenAI API key", self.api_key_input),
            1, 1
        )
        
        # Temperature
        openai_temp_label = QLabel("Temperature:")
        self.openai_temp_spin = QDoubleSpinBox()
        self.openai_temp_spin.setRange(0.0, 1.0)
        self.openai_temp_spin.setSingleStep(0.1)
        openai_layout.addWidget(openai_temp_label, 2, 0)
        openai_layout.addLayout(
            self._add_help_button("Sampling temperature (higher = more random)", self.openai_temp_spin),
            2, 1
        )
        
        # Add model layouts to group
        model_layout.addWidget(self.faster_whisper_widget, 1, 0, 1, 2)
        model_layout.addWidget(self.openai_widget, 1, 0, 1, 2)
        self.openai_widget.hide()  # Hide OpenAI options initially
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Recording Options Group
        recording_group = QGroupBox("Recording Options")
        recording_layout = QGridLayout()
        
        # Device
        rec_device_label = QLabel("Device:")
        self.rec_device_combo = QComboBox()
        self.rec_device_combo.addItems(["headphone", "microphone array"])
        recording_layout.addWidget(rec_device_label, 0, 0)
        recording_layout.addLayout(
            self._add_help_button("Select audio input device", self.rec_device_combo),
            0, 1
        )
        
        # Sample Rate
        sample_rate_label = QLabel("Sample Rate:")
        self.sample_rate_spin = QSpinBox()
        self.sample_rate_spin.setRange(8000, 48000)
        self.sample_rate_spin.setValue(16000)
        recording_layout.addWidget(sample_rate_label, 1, 0)
        recording_layout.addLayout(
            self._add_help_button("Audio sample rate in Hz", self.sample_rate_spin),
            1, 1
        )
        
        recording_group.setLayout(recording_layout)
        layout.addWidget(recording_group)
        
        # LLM Options Group
        llm_group = QGroupBox("LLM Options")
        llm_layout = QGridLayout()
        
        # Model
        llm_model_label = QLabel("Model:")
        self.llm_model_combo = QComboBox()
        self.llm_model_combo.addItems(["llama", "gemma"])
        llm_layout.addWidget(llm_model_label, 0, 0)
        llm_layout.addLayout(
            self._add_help_button("Select language model", self.llm_model_combo),
            0, 1
        )
        
        # System Prompt
        system_prompt_label = QLabel("System Prompt:")
        self.system_prompt_input = QTextEdit()
        self.system_prompt_input.setMinimumHeight(100)
        self.system_prompt_input.setPlaceholderText("Enter system instructions for the LLM...")
        llm_layout.addWidget(system_prompt_label, 1, 0)
        llm_layout.addLayout(
            self._add_help_button("Initial system instructions for the LLM", self.system_prompt_input),
            1, 1
        )
        
        # User Prompt
        user_prompt_label = QLabel("User Prompt:")
        self.user_prompt_input = QTextEdit()
        self.user_prompt_input.setMinimumHeight(100)
        self.user_prompt_input.setPlaceholderText("Enter template for user messages...")
        llm_layout.addWidget(user_prompt_label, 2, 0)
        llm_layout.addLayout(
            self._add_help_button("Template for user messages", self.user_prompt_input),
            2, 1
        )
        
        llm_group.setLayout(llm_layout)
        layout.addWidget(llm_group)
        
        # Action Buttons
        button_layout = QHBoxLayout()
        self.delete_btn = QPushButton("Delete App")
        self.rename_btn = QPushButton("Rename App")
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.rename_btn)
        layout.addLayout(button_layout)
        
        layout.addStretch()
    
    def _create_field_with_help(self, label_text, widget, help_text):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label_text))
        layout.addWidget(widget)
        help_btn = self._create_help_button(help_text)
        layout.addWidget(help_btn)
        return layout
    
    def _create_help_button(self, help_text):
        help_btn = QToolButton()
        help_btn.setText("?")
        help_btn.setToolTip(help_text)
        return help_btn
    
    def _add_help_button(self, help_text, widget):
        layout = QHBoxLayout()
        layout.addWidget(widget)
        help_btn = self._create_help_button(help_text)
        layout.addWidget(help_btn)
        return layout
    
    def _on_model_type_changed(self, model_type):
        if model_type == "faster_whisper":
            self.faster_whisper_widget.show()
            self.openai_widget.hide()
        else:
            self.faster_whisper_widget.hide()
            self.openai_widget.show() 