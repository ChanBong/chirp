import os
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QTabWidget, QGroupBox, QGridLayout,
    QLabel, QLineEdit, QComboBox, QCheckBox, QPushButton, QFileDialog,
    QScrollArea, QToolButton, QMessageBox, QVBoxLayout, QInputDialog,
    QSpacerItem, QSizePolicy, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QIntValidator, QDoubleValidator

from config_manager import ConfigManager


class SettingsWindow(QWidget):
    close_window = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")
        self.resize(700, 700)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.create_tabs()
        self.create_buttons(layout)
        self.setLayout(layout)

    def create_tabs(self):  
        # Global options tab
        global_tab = self.create_global_tab()
        self.tabs.addTab(global_tab, "Global Options")

        # Profile tabs
        apps = ConfigManager.get_apps()
        for app in apps:
            app_name = app['name']
            app_tab = self.create_app_tab(app_name)
            self.tabs.addTab(app_tab, app_name)

        # Add app button
        self.tabs.setCornerWidget(self.create_add_app_button(), Qt.Corner.TopRightCorner)

    def create_global_tab(self):
        tab = QScrollArea()
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)

        global_options = ConfigManager.get_section('global_options')
        self.create_section_widgets(tab_layout, global_options, 'global_options')

        # Add stretch factor to push widgets to the top
        tab_layout.addStretch(1)

        tab.setWidget(tab_widget)
        tab.setWidgetResizable(True)
        return tab

    def create_app_tab(self, app_name):
        tab = QScrollArea()
        tab_widget = QWidget()
        tab_layout = QVBoxLayout()

        app_config = ConfigManager.get_section('apps', app_name)

        self.add_app_sections(tab_layout, app_name, app_config)
        self.add_app_management_buttons(tab_layout, app_name)

        tab_widget.setLayout(tab_layout)
        tab.setWidget(tab_widget)
        tab.setWidgetResizable(True)
        return tab

    def add_app_sections(self, layout, app_name, app_config):
        """
        Define the order of major sections for each app
        """
        # Define the order of sections
        section_order = ['activation_backend_type', 'activation_backend', 'recording_options', 'transcription_backend_type', 'transcription_backend', 'llm_backend_type', 'llm_backend', 'prompts', 'output_options']

        # Add sections in the specified order, then any remaining sections
        for section_name in section_order:
            # Get the section data from ConfigManager instead of app_config
            section = ConfigManager.get_section(section_name, app_name)
            if section:
                self.add_section(layout, app_name, {section_name: section}, section_name)

        # Add any remaining sections not in the predefined order
        remaining_sections = set(app_config.keys()) - set(section_order) - {'name'}
        for section_name in remaining_sections:
            section = ConfigManager.get_section(section_name, app_name)
            if section:
                self.add_section(layout, app_name, {section_name: section}, section_name)

        # After adding the llm_backend section, add the prompts section
        if 'llm_backend' in section_order:
            idx = section_order.index('llm_backend')
            prompts_group = self.create_prompts_section(app_name)
            if prompts_group:
                layout.addWidget(prompts_group)

    def add_section(self, layout, app_name, app_config, section_name):
        section = app_config[section_name]
        widget = None  # Initialize widget variable
        
        if isinstance(section, dict):
            group_box = QGroupBox(section_name.replace('_', ' ').capitalize())
            group_box.setObjectName(f"{app_name}_{section_name}")
            group_layout = QVBoxLayout()
            self.create_section_widgets(group_layout, section,
                                        f'apps.{app_name}.{section_name}')
            group_box.setLayout(group_layout)
            layout.addWidget(group_box)
        else:
            widget = self.create_setting_widget(f'apps.{app_name}.{section_name}', section)
            layout.addWidget(widget)

        # Add backend type change listener
        if section_name == 'transcription_backend_type' and widget and isinstance(widget.input_widget, QComboBox):
            widget.input_widget.currentTextChanged.connect(
                lambda value, pn=app_name: self.update_backend_options(pn, 'transcription_backend', value)
            )

        if section_name == 'llm_backend_type' and widget and isinstance(widget.input_widget, QComboBox):
            widget.input_widget.currentTextChanged.connect(
                lambda value, pn=app_name: self.update_backend_options(pn, 'llm_backend', value)
            )

        if section_name == 'activation_backend_type' and widget and isinstance(widget.input_widget, QComboBox):
            widget.input_widget.currentTextChanged.connect(
                lambda value, pn=app_name: self.update_backend_options(pn, 'activation_backend_type', value)
            )

    def add_app_management_buttons(self, layout, app_name):
        delete_button = QPushButton(f"Delete {app_name}")
        delete_button.clicked.connect(lambda: self.delete_app(app_name))
        layout.addWidget(delete_button)

        rename_button = QPushButton("Rename Profile")
        rename_button.clicked.connect(lambda: self.rename_app(app_name))
        layout.addWidget(rename_button)

    def rename_app(self, old_name):
        new_name, ok = QInputDialog.getText(self, 'Rename Profile', 'Enter new app name:')
        if ok and new_name:
            if ConfigManager.rename_app(old_name, new_name):
                # Update tab name
                for i in range(self.tabs.count()):
                    if self.tabs.tabText(i) == old_name:
                        self.tabs.setTabText(i, new_name)
                        break

                # Update the tab's content
                new_tab = self.create_app_tab(new_name)
                self.tabs.removeTab(i)
                self.tabs.insertTab(i, new_tab, new_name)

                # Update active apps widget
                self.update_active_apps_widget()

                # Inform user of successful rename
                QMessageBox.information(self,
                                        'Profile Renamed',
                                        f'Profile "{old_name}" has been renamed to "{new_name}".')
            else:
                QMessageBox.warning(self,
                                    'Rename Failed',
                                    f'The name "{new_name}" is already in use or '
                                    f'the app could not be found.')

    def update_backend_options(self, app_name, backend_name, backend_type):
        ConfigManager.set_value(f'apps.{app_name}.{backend_name}_type', backend_type)

        # Refresh the backend options
        backend_group = self.findChild(QGroupBox, f"{app_name}_{backend_name}")
        if backend_group:
            backend_layout = backend_group.layout()
            # Clear existing widgets
            while backend_layout.count():
                item = backend_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

            # Add new widgets
            backend_config = ConfigManager.get_section(backend_name, app_name)
            self.create_section_widgets(backend_layout, backend_config,
                                        f'apps.{app_name}.{backend_name}')
        else:
            print(f"Backend group for {app_name} not found")  # Debug print
            # If the backend group doesn't exist, recreate the entire app tab
            for i in range(self.tabs.count()):
                if self.tabs.tabText(i) == app_name:
                    new_tab = self.create_app_tab(app_name)
                    self.tabs.removeTab(i)
                    self.tabs.insertTab(i, new_tab, app_name)
                    self.tabs.setCurrentIndex(i)
                    break

        # Force the UI to update
        self.update()

    def create_section_widgets(self, layout, section, section_path):
        if not isinstance(section, dict):
            widget = self.create_setting_widget(section_path, section)
            if widget:
                layout.addWidget(widget)
            return

        # Define the order of elements within sections
        element_order = {
            'global_options': [
                'active_apps', 'input_backend', 'print_to_terminal',
                'status_update_mode', 'noise_on_completion'
            ],
            'recording_options': [
                'sound_device', 'gain', 'sample_rate', 'recording_mode',
                'silence_duration', 'min_duration', 'save_debug_audio'
            ],
            'post_processing': [
                'writing_key_press_delay', 'keyboard_simulator', 'enabled_scripts'
            ],
            'backend': [
                'model', 'compute_type', 'device', 'model_path', 'vad_filter',
                'condition_on_previous_text', 'base_url', 'api_key', 'temperature',
                'initial_prompt', 'use_streaming', 'min_transcription_interval',
                'vad_silence_duration'
            ]
        }

        # Get the section name from the section_path
        section_name = section_path.split('.')[-1]

        # Use the predefined order if available, otherwise use all keys
        ordered_keys = element_order.get(section_name, list(section.keys()))

        # Add elements in the specified order, then any remaining elements
        for key in ordered_keys + list(set(section.keys()) - set(ordered_keys)):
            if key in section:
                value = section[key]
                if isinstance(value, dict):
                    # This is a nested section, create a group box
                    group_box = QGroupBox(key.replace('_', ' ').capitalize())
                    group_layout = QVBoxLayout()
                    # Pass the nested section path to the next level
                    self.create_section_widgets(group_layout, value, f'{section_path}.{key}')
                    group_box.setLayout(group_layout)
                    layout.addWidget(group_box)
                else:
                    # This is a setting, create a widget for it
                    # Pass the full setting path to the widget
                    widget = self.create_setting_widget(f'{section_path}.{key}', value)
                    if widget:
                        layout.addWidget(widget)

    def create_setting_widget(self, config_key, value):
        widget = SettingWidget(config_key, value)
        return widget

    def create_add_app_button(self):
        button = QPushButton("Add Profile")
        button.clicked.connect(self.add_app)
        return button

    def add_app(self):
        new_app = ConfigManager.create_app("New Profile")
        app_name = new_app['name']
        app_tab = self.create_app_tab(app_name)
        self.tabs.addTab(app_tab, app_name)
        self.tabs.setCurrentIndex(self.tabs.count() - 1)  # Switch to the new tab

        # Update the active apps widget
        self.update_active_apps_widget()

    def delete_app(self, app_name):
        if self.tabs.count() <= 2:  # 1 for global options, 1 for the last app
            QMessageBox.warning(self, 'Cannot Delete Profile',
                                'You cannot delete the last remaining app.')
            return

        reply = QMessageBox.question(self, 'Delete Profile',
                                     f"Delete the app '{app_name}'?",
                                     QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if ConfigManager.delete_app(app_name):
                for i in range(self.tabs.count()):
                    if self.tabs.tabText(i) == app_name:
                        self.tabs.removeTab(i)
                        break
                self.update_active_apps_widget()
                QMessageBox.information(self, 'Profile Deleted',
                                        f'Profile "{app_name}" has been deleted.')
            else:
                QMessageBox.warning(self, 'Cannot Delete Profile',
                                    'The app could not be deleted. '
                                    'It may be the last remaining app.')

    def update_active_apps_widget(self):
        global_tab = self.tabs.widget(0)  # Assuming global options is always the first tab
        if global_tab and isinstance(global_tab, QScrollArea):
            scroll_content = global_tab.widget()
            if scroll_content and scroll_content.layout():
                for i in range(scroll_content.layout().count()):
                    widget = scroll_content.layout().itemAt(i).widget()
                    if (isinstance(widget, SettingWidget) and
                            widget.config_key == 'global_options.active_apps'):
                        all_apps = [app['name']
                                        for app in ConfigManager.get_apps()]
                        active_apps = ConfigManager.get_value('global_options.active_apps')

                        # Create a new CheckboxListWidget with updated options
                        new_widget = CheckboxListWidget(all_apps, active_apps)
                        new_widget.optionsChanged.connect(widget.update_config)

                        # Replace the old widget with the new one
                        old_layout = widget.layout()
                        old_layout.replaceWidget(widget.input_widget, new_widget)
                        widget.input_widget.deleteLater()
                        widget.input_widget = new_widget
                        break

    def create_buttons(self, layout):
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset_settings)
        button_layout.addWidget(save_button)
        button_layout.addWidget(reset_button)
        layout.addLayout(button_layout)

    def save_settings(self):
        ConfigManager.save_config()
        self.close()

    def reset_settings(self):
        ConfigManager.reload_config()
        self.create_tabs()  # Recreate all tabs to reflect the reset config

    def closeEvent(self, event):
        event.accept()

    def create_prompts_section(self, app_name):
        """Create a group box for system and user prompts"""
        group_box = QGroupBox("Prompts")
        layout = QVBoxLayout()

        # System prompt
        system_label = QLabel("System Prompt:")
        system_text = QTextEdit()
        system_text.setMinimumHeight(100)
        
        # User prompt
        user_label = QLabel("User Prompt:")
        user_text = QTextEdit()
        user_text.setMinimumHeight(100)

        # Load current prompts
        try:
            app_system_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'apps', app_name, 'SYSTEM.txt')
            default_system_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'apps', 'SYSTEM.txt')

            app_user_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'apps', app_name, 'USER.txt')
            default_user_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'apps', 'USER.txt')

            if os.path.exists(app_system_path):
                with open(app_system_path, 'r', encoding='utf-8') as f:
                    system_text.setText(f.read())
            elif os.path.exists(default_system_path):
                with open(default_system_path, 'r', encoding='utf-8') as f:
                    system_text.setText(f.read())
            
            if os.path.exists(app_user_path):
                with open(app_user_path, 'r', encoding='utf-8') as f:
                    user_text.setText(f.read())
            elif os.path.exists(default_user_path):
                with open(default_user_path, 'r', encoding='utf-8') as f:
                    user_text.setText(f.read())
        except Exception as e:
            print(f"Error loading prompts: {str(e)}")

        # Save button
        save_button = QPushButton("Save Prompts")
        
        def save_prompts():
            try:
                app_dir = os.path.join('src', 'apps', app_name)
                os.makedirs(app_dir, exist_ok=True)
                
                with open(os.path.join(app_dir, "SYSTEM.txt"), 'w', encoding='utf-8') as f:
                    f.write(system_text.toPlainText())
                
                with open(os.path.join(app_dir, "USER.txt"), 'w', encoding='utf-8') as f:
                    f.write(user_text.toPlainText())
                    
                QMessageBox.information(self, "Success", "Prompts saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save prompts: {str(e)}")

        save_button.clicked.connect(save_prompts)

        # Add widgets to layout
        layout.addWidget(system_label)
        layout.addWidget(system_text)
        layout.addWidget(user_label)
        layout.addWidget(user_text)
        layout.addWidget(save_button)

        group_box.setLayout(layout)
        return group_box


class SettingWidget(QWidget):
    def __init__(self, config_key, value):
        super().__init__()
        self.config_key = config_key
        self.value = value
        self.schema = ConfigManager.get_schema_for_key(config_key)
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        label_text = self.config_key.split('.')[-1].replace('_', ' ').capitalize()
        self.label = QLabel(label_text)

        self.input_widget = self.create_input_widget()

        help_button = QToolButton()
        help_button.setText("?")
        # Change 1: Set the tooltip from the schema
        help_text = self.schema.get('description', 'No description available.')
        help_button.setToolTip(help_text)

        # Optional: If you still want a click to open a message box, keep this:
        help_button.clicked.connect(self.show_help)

        # Layout: label left, spacer, input widget right, help button right
        layout.addWidget(self.label, 0, 0, 1, 1, Qt.AlignmentFlag.AlignLeft)

        layout.addItem(
            QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum),
            0, 1
        )

        layout.addWidget(self.input_widget, 0, 2, Qt.AlignmentFlag.AlignRight)
        layout.addWidget(help_button, 0, 3, Qt.AlignmentFlag.AlignRight)

        self.setLayout(layout)

    def create_input_widget(self):
        widget_type = self.schema.get('type')
        # print(f"config_key: {self.config_key}, value: {self.value}, widget_type: {widget_type}")
        if widget_type == 'bool':
            return self.create_checkbox()
        elif widget_type == 'str' and 'options' in self.schema:
            return self.create_combobox()
        elif widget_type == 'int':
            return self.create_line_edit(QIntValidator())
        elif widget_type == 'float':
            return self.create_line_edit(QDoubleValidator())
        elif widget_type == 'int or null':
            return self.create_line_edit(QIntValidator(), allow_empty=True)
        elif widget_type == 'str':
            return self.create_line_edit()
        elif widget_type == 'list':
            return self.create_checkbox_list()
        elif widget_type == 'dir_path':
            return self.create_dir_path_widget()
        else:
            return QLabel(f"Unsupported type: {widget_type}")

    def create_checkbox_list(self):
        if self.config_key == 'global_options.active_apps':
            options = [app['name'] for app in ConfigManager.get_apps()]
        elif self.config_key.endswith('enabled_scripts'):
            options = self.get_available_scripts()
        else:
            options = self.schema.get('options', [])

        widget = CheckboxListWidget(options, self.value)
        widget.optionsChanged.connect(self.update_config)
        return widget

    def get_available_scripts(self):
        script_folder = 'scripts'  # Adjust this path as needed
        if os.path.exists(script_folder):
            return [f for f in os.listdir(script_folder) if f.endswith('.py')]
        return []

    def create_line_edit(self, validator=None, allow_empty=False):
        widget = QLineEdit()
        if validator:
            widget.setValidator(validator)
        if allow_empty:
            widget.setPlaceholderText("Auto")
        widget.setText(str(self.value) if self.value is not None else '')
        widget.editingFinished.connect(self.update_config)
        return widget

    def create_checkbox(self):
        widget = QCheckBox()
        widget.setChecked(bool(self.value))
        widget.stateChanged.connect(
            lambda state: self.update_config(state == Qt.CheckState.Checked)
        )
        return widget

    def create_combobox(self):
        widget = QComboBox()
        widget.addItems(self.schema['options'])
        widget.setCurrentText(str(self.value))
        widget.currentTextChanged.connect(self.update_config)
        return widget

    def create_dir_path_widget(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        line_edit = QLineEdit(self.value if self.value else '')
        browse_button = QPushButton("Browse")

        layout.addWidget(line_edit)
        layout.addWidget(browse_button)

        def browse_directory():
            directory = QFileDialog.getExistingDirectory(self, "Select Directory")
            if directory:
                line_edit.setText(directory)
                self.update_config(directory)

        browse_button.clicked.connect(browse_directory)
        line_edit.editingFinished.connect(lambda: self.update_config(line_edit.text()))

        return widget

    def update_config(self, value=None):
        if isinstance(self.input_widget, QWidget) and self.schema.get('type') == 'dir_path':
            line_edit = self.input_widget.findChild(QLineEdit)
            if line_edit:
                value = line_edit.text()
        elif isinstance(self.input_widget, CheckboxListWidget):
            if value is None:
                value = self.input_widget.get_selected_options()
        elif isinstance(self.input_widget, QCheckBox):
            value = self.input_widget.isChecked()
        elif isinstance(self.input_widget, QComboBox):
            value = self.input_widget.currentText()
        elif isinstance(self.input_widget, QLineEdit):
            if self.schema.get('type') == 'int':
                value = int(self.input_widget.text())
            elif self.schema.get('type') == 'float':
                value = float(self.input_widget.text())
            elif self.schema.get('type') == 'int or null':
                text_val = self.input_widget.text().strip()
                value = int(text_val) if text_val else None
            else:
                value = self.input_widget.text()

        print(f"setting {self.config_key} to {value}")
        ConfigManager.set_value(self.config_key, value)

    def show_help(self):
        """Still pops a MessageBox on click, but you already have the tooltip on hover."""
        QMessageBox.information(
            self, 
            "Help", 
            self.schema.get('description', 'No description available.')
        )


class CheckboxListWidget(QWidget):
    optionsChanged = pyqtSignal(list)

    def __init__(self, options, selected_options, parent=None):
        super().__init__(parent)
        self.options = options
        self.selected_options = selected_options
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.checkboxes = {}

        for option in self.options:
            checkbox = QCheckBox(option)
            checkbox.setChecked(option in self.selected_options)
            checkbox.stateChanged.connect(self.update_selected_options)
            self.checkboxes[option] = checkbox
            layout.addWidget(checkbox)

        self.setLayout(layout)

    def update_selected_options(self):
        self.selected_options = [option for option, checkbox in self.checkboxes.items()
                                 if checkbox.isChecked()]
        self.optionsChanged.emit(self.selected_options)

    def get_selected_options(self):
        return self.selected_options
