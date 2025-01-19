from rich.console import Console
from rich.theme import Theme
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.text import Text
from typing import Optional

class ConsoleManager:
    """Centralized console output manager using Rich formatting"""
    
    def __init__(self):
        # Custom theme for consistent colors
        custom_theme = Theme({
            'info': 'cyan',
            'success': 'green',
            'warning': 'yellow',
            'error': 'red',
            'highlight': 'blue',
            'process': 'magenta'
        })
        
        self.console = Console(theme=custom_theme)

    def setup_message(self, message: str):
        """Display setting up message"""
        self.console.print(f"[yellow]【🏗️】{message}[/yellow]")
        
    def info(self, message: str):
        """Display informational message"""
        self.console.print(f"ℹ️ {message}", style="info")
        
    def success(self, message: str):
        """Display success message"""
        self.console.print(f"✅ {message}", style="success")
        
    def warning(self, message: str):
        """Display warning message"""
        self.console.print(f"⚠️ {message}", style="warning")
        
    def error(self, message: str):
        """Display error message"""
        self.console.print(f"❌ {message}", style="error")
        
    def process(self, message: str):
        """Display process/status message"""
        self.console.print(f"⏳ {message}", style="process")
        
    def highlight(self, message: str):
        """Display highlighted message"""
        self.console.print(Panel(message, style="highlight"))
        
    def create_progress_bar(self, description: str) -> Progress:
        """Create and return a progress bar"""
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[process]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        )
        return progress
    
    def debug(self, message: str):
        """Display debug message (only in development)"""
        self.console.print(f"🔍 {message}", style="info", dim=True)

# Global console manager instance
console = ConsoleManager() 