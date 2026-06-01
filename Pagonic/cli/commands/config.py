"""
Pagonic CLI - Config Command
=============================
Configuration management for Pagonic settings.

Phase 3, Week 5: CLI Development
Days 31-35: Advanced Features
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


@click.group()
def config():
    """
     Manage Pagonic configuration.
    
    \b
    Examples:
        pagonic config list             # Show all settings
        pagonic config get theme        # Get specific setting
        pagonic config set theme dark   # Set a value
        pagonic config reset            # Reset to defaults
    """
    pass


@config.command('list')
def list_config():
    """ List all configuration settings."""
    from Pagonic.core.config_manager import get_config
    
    console.print()
    
    try:
        cfg = get_config()
        settings = cfg.to_dict()
        
        # Create table
        table = Table(
            title=" Pagonic Configuration",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        table.add_column("Type", style="dim")
        
        for key, value in sorted(settings.items()):
            value_str = str(value)
            if len(value_str) > 50:
                value_str = value_str[:47] + "..."
            
            type_str = type(value).__name__
            
            # Color code based on type
            if isinstance(value, bool):
                value_display = f"[{'green' if value else 'red'}]{value}[/]"
            elif isinstance(value, (int, float)):
                value_display = f"[yellow]{value}[/]"
            elif isinstance(value, list):
                value_display = f"[magenta]{len(value)} items[/]"
            elif value is None:
                value_display = "[dim]None[/]"
            else:
                value_display = f"[white]{value_str}[/]"
            
            table.add_row(key, value_display, type_str)
        
        console.print(table)
        
        # Show config file path
        console.print()
        console.print(f"[dim]Config file: {cfg.config_path}[/]")
        console.print()
        
    except Exception as e:
        console.print(f"\n[red] Error:[/] {str(e)}")
        raise SystemExit(1)


@config.command('get')
@click.argument('key')
def get_config_value(key: str):
    """ Get a configuration value."""
    from Pagonic.core.config_manager import get_config
    
    try:
        cfg = get_config()
        value = cfg.get(key)
        
        if value is None and key not in cfg.to_dict():
            console.print(f"\n[yellow] Setting '{key}' not found[/]")
            console.print("[dim]Use 'pagonic config list' to see available settings[/]\n")
            raise SystemExit(1)
        
        console.print()
        console.print(Panel.fit(
            f"[bold cyan]{key}[/] = [bold green]{value}[/]",
            border_style="dim"
        ))
        console.print()
        
    except SystemExit:
        raise
    except Exception as e:
        console.print(f"\n[red] Error:[/] {str(e)}")
        raise SystemExit(1)


@config.command('set')
@click.argument('key')
@click.argument('value')
def set_config_value(key: str, value: str):
    """ Set a configuration value."""
    from Pagonic.core.config_manager import get_config
    
    try:
        cfg = get_config()
        
        # Check if key exists
        if key not in cfg.to_dict():
            console.print(f"\n[yellow] Creating new setting: '{key}'[/]")
        
        # Try to convert value to appropriate type
        old_value = cfg.get(key)
        
        if old_value is not None:
            # Convert to same type as existing value
            if isinstance(old_value, bool):
                value = value.lower() in ('true', '1', 'yes', 'on')
            elif isinstance(old_value, int):
                value = int(value)
            elif isinstance(old_value, float):
                value = float(value)
            # str stays as str
        else:
            # Try to infer type
            if value.lower() in ('true', 'false'):
                value = value.lower() == 'true'
            elif value.isdigit():
                value = int(value)
            else:
                try:
                    value = float(value)
                except ValueError:
                    pass  # Keep as string
        
        cfg.set(key, value)
        
        console.print()
        console.print(Panel.fit(
            f"[bold green] Set:[/] [cyan]{key}[/] = [green]{value}[/]",
            border_style="green"
        ))
        console.print()
        
    except ValueError as e:
        console.print(f"\n[red] Invalid value:[/] {str(e)}")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"\n[red] Error:[/] {str(e)}")
        raise SystemExit(1)


@config.command('reset')
@click.option('--key', '-k', default=None, help='Reset specific key only')
@click.confirmation_option(prompt='Are you sure you want to reset configuration?')
def reset_config(key: str):
    """ Reset configuration to defaults."""
    from Pagonic.core.config_manager import get_config
    
    try:
        cfg = get_config()
        
        if key:
            cfg.reset(key)
            console.print(f"\n[green] Reset '{key}' to default value[/]\n")
        else:
            cfg.reset()
            console.print("\n[green] All settings reset to defaults[/]\n")
        
    except Exception as e:
        console.print(f"\n[red] Error:[/] {str(e)}")
        raise SystemExit(1)


@config.command('path')
def show_config_path():
    """ Show configuration file path."""
    from Pagonic.core.config_manager import get_config
    
    try:
        cfg = get_config()
        
        console.print()
        console.print(Panel.fit(
            f"[bold] Config Location[/]\n\n"
            f"[cyan]{cfg.config_path}[/]\n\n"
            f"[dim]Exists: {' Yes' if cfg.config_path.exists() else ' No'}[/]",
            border_style="dim"
        ))
        console.print()
        
    except Exception as e:
        console.print(f"\n[red] Error:[/] {str(e)}")
        raise SystemExit(1)


if __name__ == '__main__':
    config()
