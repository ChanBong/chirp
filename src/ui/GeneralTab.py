from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QCheckBox, QToolButton)
from PyQt6.QtCore import Qt

class GeneralTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Activate Apps
        activate_layout = self._create_checkbox_with_help(
            "Activate Apps",
            "Enable or disable all speech-to-text applications"
        )
        layout.addLayout(activate_layout)
        
        # Start on startup
        startup_layout = self._create_checkbox_with_help(
            "Start on startup",
            "Automatically start the application when your system boots"
        )
        layout.addLayout(startup_layout)
        
        # Print to terminal
        terminal_layout = self._create_checkbox_with_help(
            "Print to terminal",
            "Output debug information and transcriptions to the terminal"
        )
        layout.addLayout(terminal_layout)
        
        # Save debug audio
        debug_audio_layout = self._create_checkbox_with_help(
            "Save debug audio",
            "Save audio recordings for debugging purposes"
        )
        layout.addLayout(debug_audio_layout)
        
        # Add stretch to push everything to the top
        layout.addStretch()
    
    def _create_checkbox_with_help(self, text, help_text):
        layout = QHBoxLayout()
        
        # Create checkbox
        checkbox = QCheckBox(text)
        layout.addWidget(checkbox)
        
        # Create help button
        help_btn = QToolButton()
        help_btn.setText("?")
        help_btn.setToolTip(help_text)
        layout.addWidget(help_btn)
        
        # Add stretch to keep checkbox and help button together on the left
        layout.addStretch()
        
        return layout 