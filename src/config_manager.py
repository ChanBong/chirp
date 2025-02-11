import yaml
import os
import subprocess
from typing import Any, Dict, List, Optional
from event_bus import EventBus
from rich import print as rprint
from utils import list_good_audio_input_devices

class ConfigValidator:
    @staticmethod
    def validate_and_update(config: Dict, schema: Dict) -> Dict:
        ConfigValidator._validate_section(config, schema, [])
        return config

    @staticmethod
    def _validate_section(config: Dict, schema: Dict, path: List[str]):
        # Special handling for apps list
        if isinstance(schema, list):
            if not isinstance(config, list):
                config = []
            for item in config:
                ConfigValidator._validate_section(item, schema[0], path)
            return

        for key, value in schema.items():
            if key in ['transcription_backends', 'llm_backends', 'activation_backends']:
                continue  # Skip validating these backend sections directly
            current_path = path + [key]
            
            if key not in config:
                rprint(f"[yellow]Adding missing key:[/yellow] {'.'.join(current_path)}")
                config[key] = ConfigValidator._get_default_value(value)
            elif isinstance(value, dict) and 'value' not in value:
                if not isinstance(config[key], dict):
                    rprint(f"[red]Replacing invalid value for[/red] {'.'.join(current_path)} [red]with default[/red]")
                    config[key] = {}
                ConfigValidator._validate_section(config[key], value, current_path)
            elif not ConfigValidator._validate_value(config[key], value):
                rprint(f"[red]Replacing invalid value for[/red] {'.'.join(current_path)} [red]with default[/red]")
                config[key] = ConfigValidator._get_default_value(value)

        # Only remove spurious keys for non-backend sections
        if not any(p.endswith('_backends') for p in path):
            keys_to_remove = [key for key in config if key not in schema]
            for key in keys_to_remove:
                rprint(f"[yellow]Removing spurious key:[/yellow] {'.'.join(path + [key])}")
                del config[key]

    @staticmethod
    def _validate_value(value: Any, schema: Dict) -> bool:
        if 'type' in schema:
            if schema['type'] == 'str' and not isinstance(value, str):
                return False
            elif schema['type'] == 'int' and not isinstance(value, int):
                return False
            elif schema['type'] == 'float' and not isinstance(value, (int, float)):
                return False
            elif schema['type'] == 'bool' and not isinstance(value, bool):
                return False
            elif schema['type'] == 'list' and not isinstance(value, list):
                return False
            elif schema['type'] == 'int or null' and not (isinstance(value, int) or value is None):
                return False
            elif schema['type'] == 'dir_path':
                return isinstance(value, str) and (value == '' or os.path.isdir(value))
        if 'options' in schema and value not in schema['options']:
            return False
        return True

    @staticmethod
    def _get_default_value(schema: Dict) -> Any:
        if 'value' in schema:
            return schema['value']
        elif schema.get('type') == 'str':
            return ''
        elif schema.get('type') == 'int':
            return 0
        elif schema.get('type') == 'float':
            return 0.0
        elif schema.get('type') == 'bool':
            return False
        elif schema.get('type') == 'list':
            return []
        elif schema.get('type') == 'int or null':
            return None
        else:
            return {}


class ConfigLoader:
    @staticmethod
    def load_yaml(file_path: str) -> Dict:
        try:
            with open(file_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            return {}

    @staticmethod
    def save_yaml(data: Dict, file_path: str):
        with open(file_path, 'w') as file:
            yaml.dump(data, file, default_flow_style=False)


class AppManager:
    def __init__(self, config: Dict, schema: Dict):
        self.config = config
        self.schema = schema
        if 'apps' not in self.config:
            self.config['apps'] = []

    def get_apps(self, active_only: bool = False) -> List[Dict]:
        all_apps = self.config.get('apps', [])
        if active_only:
            active_app_names = self.config.get('global_options', {}).get('active_apps', [])
            return [app for app in all_apps if app['name'] in active_app_names]
        return all_apps
    

    def create_expandable_key(self, key: str, option: str) -> Dict:
        new_app = {}
        for option_key, option_value in self.schema[key][option].items():
            new_app[option_key] = self._get_default_value_from_schema(option_value)
        return new_app


    def create_app(self, name: str = 'Default') -> Dict:
        unique_name = self._generate_unique_name(name)
        new_app = {'name': unique_name}

        # Expandable keys are keys that can be expanded into a dictionary
        expandable_keys = ['activation_backend_type', 'transcription_backend_type', 'llm_backend_type']
        
        for key, schema_value in self.schema['apps'][0].items():
            if key in expandable_keys:
                new_app[key] = schema_value['value']
            elif key == 'activation_backend':
                new_app[key] = {}
            elif key == 'transcription_backend':
                new_app[key] = {}
            elif key == 'llm_backend':
                new_app[key] = {}
            elif key != 'name':
                new_app[key] = self._get_default_value_from_schema(schema_value)

        activation_backend_type = new_app['activation_backend_type']
        if activation_backend_type in self.schema['activation_backends']:
            new_app['activation_backend'] = self.create_expandable_key('activation_backends', activation_backend_type)
        
        transcription_backend_type = new_app['transcription_backend_type']
        if transcription_backend_type in self.schema['transcription_backends']:
            new_app['transcription_backend'] = self.create_expandable_key('transcription_backends', transcription_backend_type)
        
        llm_backend_type = new_app['llm_backend_type']
        if llm_backend_type in self.schema['llm_backends']:
            new_app['llm_backend'] = self.create_expandable_key('llm_backends', llm_backend_type)

        return new_app

    def add_app(self, name: str) -> Dict:
        new_app = self.create_app(name)
        if 'apps' not in self.config:
            self.config['apps'] = []
        self.config['apps'].append(new_app)
        return new_app

    def delete_app(self, name: str) -> bool:
        if len(self.config['apps']) <= 1:
            return False  # Prevent deleting the last app
        self.config['apps'] = [p for p in self.config['apps'] if p['name'] != name]
        active_apps = self.config.get('global_options', {}).get('active_apps', [])
        if name in active_apps:
            active_apps.remove(name)
        return True

    def rename_app(self, old_name: str, new_name: str) -> bool:
        if old_name == new_name:
            return True
        if any(app['name'] == new_name for app in self.config['apps']):
            return False
        for app in self.config['apps']:
            if app['name'] == old_name:
                app['name'] = new_name
                # Update active_apps if necessary
                active_apps = self.config.get('global_options', {}).get('active_apps', [])
                if old_name in active_apps:
                    active_apps[active_apps.index(old_name)] = new_name
                return True
        return False

    def _get_default_value_from_schema(self, schema_value: Dict) -> Any:
        if isinstance(schema_value, dict) and 'value' in schema_value:
            return schema_value['value']
        elif isinstance(schema_value, dict):
            # Create a section with nested defaults
            return {k: self._get_default_value_from_schema(v) for k, v in schema_value.items()}
        return None

    def _generate_unique_name(self, base_name: str) -> str:
        counter = 1
        new_name = base_name
        while any(app['name'] == new_name for app in self.config.get('apps', [])):
            new_name = f"{base_name} ({counter})"
            counter += 1
        return new_name


class ConfigManager:
    _config: Dict = {}
    _schema: Dict = {}
    _app_manager: Optional[AppManager] = None
    _event_bus: EventBus = None

    @classmethod
    def initialize(cls, event_bus: EventBus, verbose: bool = False):
        cls._event_bus = event_bus
        cls._verbose = verbose
        cls.update_ollama_models(verbose)
        cls.update_input_options(verbose)
        cls._schema = ConfigLoader.load_yaml('config_schema.yaml')
        # Initialize with empty apps list
        cls._app_manager = AppManager({'apps': []}, cls._schema)
        cls._config = cls._load_config()
        cls._validate_config()
        cls._app_manager.config = cls._config  # Update AppManager with loaded config

    @classmethod
    def get_apps(cls, active_only: bool = False) -> List[Dict]:
        return cls._app_manager.get_apps(active_only)

    @classmethod
    def rename_app(cls, old_name: str, new_name: str) -> bool:
        return cls._app_manager.rename_app(old_name, new_name)

    @classmethod
    def create_app(cls, name: str) -> Dict:
        unique_name = cls._app_manager._generate_unique_name(name)
        return cls._app_manager.add_app(unique_name)

    @classmethod
    def delete_app(cls, name: str) -> bool:
        return cls._app_manager.delete_app(name)

    @classmethod
    def get_section(cls, section_name: str, app_name: Optional[str] = None) -> Dict:
        if app_name:
            app = next((p for p in cls._config['apps'] if p['name'] == app_name), None)
            if not app:
                raise ValueError(f"App '{app_name}' not found")
            if section_name == 'apps':
                return app
            else:
                return app.get(section_name, {})
        return cls._config.get(section_name, {})

    @classmethod
    def get_value(cls, key: str, app_name: Optional[str] = None) -> Any:
        keys = key.split('.')
        if app_name or (keys[0] == 'apps' and len(keys) > 1):
            if not app_name:
                app_name = keys[1]
                keys = keys[2:]
            app = next((p for p in cls._config['apps'] if p['name'] == app_name), None)
            if not app:
                raise ValueError(f"App '{app_name}' not found")
            section = app
        else:
            section = cls._config

        for k in keys:
            if isinstance(section, dict):
                section = section.get(k, None)
            else:
                return None
        return section

    @classmethod
    def set_value(cls, key: str, value: Any, app_name: Optional[str] = None):
        keys = key.split('.')
        if app_name or (keys[0] == 'apps' and len(keys) > 1):
            if not app_name:
                app_name = keys[1]
                keys = keys[2:]
            # Find the app in the apps list
            app = next((p for p in cls._config['apps'] if p['name'] == app_name), None)
            if not app:
                raise ValueError(f"App '{app_name}' not found")
            target = app
        else:
            target = cls._config

        # Navigate to the target location
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        
        # Set the value
        target[keys[-1]] = value

        # Special handling for backend type changes
        if keys[-1] == 'transcription_backend_type':
            backend_schema = cls._schema['transcription_backends'][value]
            target['transcription_backend'] = {k: v['value'] for k, v in backend_schema.items() if 'value' in v}

        if keys[-1] == 'llm_backend_type':
            backend_schema = cls._schema['llm_backends'][value]
            target['llm_backend'] = {k: v['value'] for k, v in backend_schema.items() if 'value' in v}

        if keys[-1] == 'activation_backend_type':
            backend_schema = cls._schema['activation_backends'][value]
            target['activation_backend'] = {k: v['value'] for k, v in backend_schema.items() if 'value' in v}

        

    @classmethod
    def get_schema_for_key(cls, key: str) -> Dict:
        # print(f"key: {key}")
        schema = cls._schema
        parts = key.split('.')

        # Special handling for apps
        if parts[0] == 'apps':
            app_schema = schema.get('apps', [{}])[0]
            app_name = parts[1]
            remaining_parts = parts[2:]
            # print(f"app_schema: {app_schema}, app_name: {app_name}, remaining_parts: {remaining_parts}")
            # Handle backend options specially
            if remaining_parts[0] == 'activation_backend' and len(remaining_parts) > 1:
                activation_backend_type = cls.get_value(f"apps.{app_name}.activation_backend_type")
                if activation_backend_type:
                    activation_schema = cls._schema.get('activation_backends', {}).get(activation_backend_type, {})
                    for part in remaining_parts[1:]:
                        activation_schema = activation_schema.get(part, {})
                    return activation_schema
            elif remaining_parts[0] == 'transcription_backend' and len(remaining_parts) > 1:
                transcription_backend_type = cls.get_value(f"apps.{app_name}.transcription_backend_type")
                if transcription_backend_type:
                    transcription_backend_schema = cls._schema.get('transcription_backends', {}).get(transcription_backend_type, {})
                    for part in remaining_parts[1:]:
                        transcription_backend_schema = transcription_backend_schema.get(part, {})
                    return transcription_backend_schema
            elif remaining_parts[0] == 'llm_backend' and len(remaining_parts) > 1:  
                llm_backend_type = cls.get_value(f"apps.{app_name}.llm_backend_type")
                # print(f"llm_backend_type: {llm_backend_type}")
                if llm_backend_type:
                    llm_backend_schema = cls._schema.get('llm_backends', {}).get(llm_backend_type, {})
                    # print(f"llm_backend_schema: {llm_backend_schema}")
                    for part in remaining_parts[1:]:
                        llm_backend_schema = llm_backend_schema.get(part, {})
                    return llm_backend_schema
            else:
                # Navigate through the app schema
                for part in remaining_parts:
                    app_schema = app_schema.get(part, {})
                return app_schema

        # For non-app keys, navigate through the schema normally
        for part in parts:
            if isinstance(schema, dict):
                schema = schema.get(part, {})
            else:
                return {}

        return schema

    @classmethod
    def save_config(cls):
        ConfigLoader.save_yaml(cls._config, 'config.yaml')
        cls._event_bus.emit("config_changed")

    @classmethod
    def reload_config(cls):
        cls._config = cls._load_config()
        cls._validate_config()
        cls._app_manager = AppManager(cls._config, cls._schema)

    @classmethod
    def log_print(cls, message: str):
        if cls._config.get('global_options', {}).get('print_to_terminal', False):
            rprint(message)

    @classmethod
    def _load_config(cls) -> Dict:
        config = ConfigLoader.load_yaml('config.yaml')
        if not config:
            config = cls._create_default_config()
            ConfigLoader.save_yaml(config, 'config.yaml')
        return config

    @classmethod
    def _create_default_config(cls) -> Dict:
        default_config = {'apps': []}
        for section, content in cls._schema.items():
            if section == 'apps':
                default_app = cls._app_manager.create_app()
                default_config['apps'].append(default_app)
            elif section in ['transcription_backends', 'llm_backends', 'activation_backends']:
                # Skip this section as it's not part of the actual config
                continue
            else:
                default_config[section] = cls._create_default_section(content)
        return default_config

    @classmethod
    def _create_default_section(cls, schema_section: Dict) -> Dict:
        section = {}
        for key, value in schema_section.items():
            if isinstance(value, dict) and 'value' in value:
                section[key] = value['value']
            elif isinstance(value, dict):
                if value.get('type') == 'int or null':
                    section[key] = None
                else:
                    section[key] = cls._create_default_section(value)
        return section

    @classmethod
    def _get_default_value_from_schema(cls, schema_value: Dict) -> Any:
        if isinstance(schema_value, dict) and 'value' in schema_value:
            return schema_value['value']
        elif isinstance(schema_value, dict):
            # Create a section with nested defaults
            return cls._create_default_section(schema_value)
        return None

    @classmethod
    def _validate_config(cls):
        cls._config = ConfigValidator.validate_and_update(cls._config, cls._schema)

    @classmethod
    def get_available_backends(cls, backend_type: str) -> Dict:
        """Get available backends for a specific type (transcription or llm)"""
        if backend_type == 'transcription':
            return cls._schema.get('transcription_backends', {})
        elif backend_type == 'llm':
            return cls._schema.get('llm_backends', {})
        elif backend_type == 'activation':
            return cls._schema.get('activation_backends', {})
        return {}

    def update_ollama_models(verbose: bool = False):
        try:
            # Run ollama models command and get output
            output = subprocess.check_output(["ollama", "list"], text=True).splitlines()
            
            default_model_names = ['llama3.2:3b', 'deepseek-r1:7b', 'mistral:7b', 'qwen:7b']
            model_names = []
            for line in output[1:]:  # Skip the header line
                if line.strip():  # Skip empty lines
                    # Split by whitespace and take first column (NAME)
                    model_name = line.split()[0].strip()
                    model_names.append(model_name)

            if len(model_names) == 0:
                if verbose:
                    rprint("[red]No Ollama models found. Adding default model...[/red]")
                model_names = default_model_names
            
            with open('config_schema.yaml', 'r') as file:
                schema = yaml.safe_load(file)
            
            if 'llm_backends' in schema and 'ollama' in schema['llm_backends']:
                if 'model' in schema['llm_backends']['ollama']:
                    schema['llm_backends']['ollama']['model']['options'] = model_names
            
            # Save the updated schema
            with open('config_schema.yaml', 'w') as file:
                yaml.dump(schema, file, default_flow_style=False)
            
            if verbose:
                rprint("[green]Ollama models updated successfully[/green]")
            
        except subprocess.CalledProcessError as e:
            rprint("[red]Error running 'ollama list' command[/red]. Check your Ollama installation.")
        except Exception as e:
            rprint(f"[red]Error updating Ollama models: {str(e)}[/red]")

    def update_input_options(verbose: bool = False):
        try:
            input_options = []
            input_devices = list_good_audio_input_devices()
            default_device = None
            for dev in input_devices:
                if dev['is_default']:
                    default_device = dev
                    break
            
            if not default_device:
                if verbose:
                    rprint("[red]No default device found. Setting to the first device.[/red]")
                default_device = input_devices[0]
            
            if input_devices:
                for dev in input_devices:
                    input_options.append(f"{dev['index']}: {dev['name']}")

            with open('config_schema.yaml', 'r') as file:
                schema = yaml.safe_load(file)
            
            # Update the schema for recording_options.sound_device
            if 'apps' in schema and len(schema['apps']) > 0:
                recording_options = schema['apps'][0].get('recording_options', {})
                if 'sound_device' in recording_options:
                    recording_options['sound_device']['type'] = 'str'
                    recording_options['sound_device']['options'] = input_options
                    if 'value' not in recording_options['sound_device'] or recording_options['sound_device']['value'] not in input_options:
                        recording_options['sound_device']['value'] = f"{default_device['index']}: {default_device['name']} - {default_device['host_api']}"
            
            with open('config_schema.yaml', 'w') as file:
                yaml.dump(schema, file, default_flow_style=False)
            
            if verbose:
                rprint("[green]Input device options updated successfully[/green]")
            
        except Exception as e:
            rprint(f"[red]Error updating input device options: {str(e)}[/red]")


