"""Pagonic command-line interface."""

import os
import time
from pathlib import Path
from typing import Tuple

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel
from rich import box

from Pagonic import __version__
from Pagonic.cli.utils import format_size, format_time, format_ratio

console = Console()
VERSION = __version__


@click.group()
@click.version_option(version=VERSION, prog_name="Pagonic")
def cli():
    """
     Pagonic - ZIP Compression Tool
    
    A professional ZIP compression tool with security features,
    archive utilities, and a terminal interface.
    
    \b
    Examples:
        pagonic compress file1.txt file2.txt archive.zip
        pagonic extract archive.zip ./output/
        pagonic list archive.zip
        pagonic benchmark -s 10
        pagonic config list
    """
    pass


# Register subcommands from commands module
from Pagonic.cli.commands.benchmark import benchmark
from Pagonic.cli.commands.config import config

cli.add_command(benchmark)
cli.add_command(config)

@cli.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--output', '-o', type=click.Path(), required=True, help='Output archive path')
@click.option('--level', '-l', default=6, type=click.IntRange(0, 9), help='Compression level (0-9)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def compress(files: Tuple[str, ...], output: str, level: int, verbose: bool):
    """
     Compress files into a ZIP archive.
    
    \b
    Examples:
        pagonic compress file1.txt file2.txt -o archive.zip
        pagonic compress *.txt -o docs.zip -l 9
        pagonic compress folder/ -o backup.zip -v
    """
    from Pagonic.core.formats.zip_writer import ZipWriter
    
    if not files:
        console.print("[red] Error:[/] No files specified!")
        raise SystemExit(1)
    
    # Ensure output has .zip extension
    if not output.lower().endswith('.zip'):
        output = output + '.zip'
    
    # Header panel
    console.print()
    console.print(Panel.fit(
        f"[bold blue] Pagonic Compression[/]",
        subtitle=f"Level: {level} | Files: {len(files)}",
        border_style="blue"
    ))
    console.print()
    
    try:
        # Create writer
        writer = ZipWriter(output, compression_level=level)
        
        # Collect all files (expand directories)
        all_files = []
        for f in files:
            path = Path(f)
            if path.is_dir():
                # Add all files in directory recursively
                for child in path.rglob('*'):
                    if child.is_file():
                        all_files.append(str(child))
            else:
                all_files.append(str(path))
        
        total_size = 0
        start_time = time.time()
        
        # Progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Compressing...", total=len(all_files))
            
            for file_path in all_files:
                # Get file size
                file_size = os.path.getsize(file_path)
                total_size += file_size
                
                # Add to archive
                writer.add_file(file_path)
                progress.update(task, advance=1)
                
                if verbose:
                    console.print(f"   Added: [cyan]{file_path}[/] ({format_size(file_size)})")
        
        # Finalize archive
        stats = writer.finalize()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Get archive size
        archive_size = os.path.getsize(output)
        
        # Results table
        console.print()
        table = Table(title=" Compression Results", box=box.ROUNDED)
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        table.add_row(" Archive", output)
        table.add_row(" Files", str(len(all_files)))
        table.add_row(" Original Size", format_size(total_size))
        table.add_row(" Compressed Size", format_size(archive_size))
        table.add_row(" Ratio", format_ratio(total_size, archive_size))
        table.add_row(" Duration", format_time(duration))
        table.add_row(" Speed", f"{total_size / duration / 1024 / 1024:.1f} MB/s" if duration > 0 else "N/A")
        table.add_row(" Status", "[bold green]Success![/]")
        
        console.print(table)
        console.print()
        
    except Exception as e:
        console.print(f"\n[red] Error:[/] {str(e)}")
        raise SystemExit(1)


@cli.command()
@click.argument('archive', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), default='.', help='Output directory')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def extract(archive: str, output: str, verbose: bool):
    """
     Extract files from a ZIP archive.
    
    \b
    Examples:
        pagonic extract archive.zip
        pagonic extract archive.zip -o ./output/
        pagonic extract archive.zip -v
    """
    from Pagonic.core.formats.zip_reader import ZipReader
    
    # Ensure output directory exists
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Header panel
    console.print()
    console.print(Panel.fit(
        f"[bold green] Pagonic Extraction[/]",
        subtitle=f"Archive: {archive}",
        border_style="green"
    ))
    console.print()
    
    try:
        # Create reader
        reader = ZipReader(archive)
        entries = reader._get_entries()  # Use internal method
        total_files = len(entries)
        
        console.print(f"[dim]Found {total_files} files in archive[/]\n")
        
        start_time = time.time()
        extracted_size = 0
        
        # Progress callback
        extracted_files = []
        
        def progress_callback(current: int, total: int, filename: str):
            nonlocal extracted_size
            if verbose:
                console.print(f"   Extracted: [cyan]{filename}[/]")
            extracted_files.append(filename)
        
        # Extract with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Extracting...", total=total_files)
            
            # Custom callback to update progress
            def update_progress(current: int, total: int, filename: str):
                progress.update(task, completed=current)
                if verbose:
                    console.print(f"   Extracted: [cyan]{filename}[/]")
            
            # Extract all files
            result = reader.extract_all(str(output_path), progress_callback=update_progress)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate extracted size
        for f in result.get('success', []):
            file_path = output_path / f
            if file_path.exists():
                extracted_size += file_path.stat().st_size
        
        # Results table
        console.print()
        table = Table(title=" Extraction Results", box=box.ROUNDED)
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        table.add_row(" Archive", archive)
        table.add_row(" Files Extracted", str(len(result.get('success', []))))
        table.add_row(" Total Size", format_size(extracted_size))
        table.add_row(" Output Directory", str(output_path.absolute()))
        table.add_row(" Duration", format_time(duration))
        table.add_row(" Speed", f"{extracted_size / duration / 1024 / 1024:.1f} MB/s" if duration > 0 else "N/A")
        
        # Check for errors
        if result.get('errors'):
            table.add_row(" Errors", f"[yellow]{len(result['errors'])} files[/]")
        else:
            table.add_row(" Status", "[bold green]Success![/]")
        
        console.print(table)
        console.print()
        
        # Show errors if any
        if result.get('errors'):
            console.print("[yellow] Some files had errors:[/]")
            for error in result['errors'][:5]:  # Show first 5
                console.print(f"   {error}")
            if len(result['errors']) > 5:
                console.print(f"  ... and {len(result['errors']) - 5} more")
            console.print()
        
    except Exception as e:
        console.print(f"\n[red] Error:[/] {str(e)}")
        raise SystemExit(1)


@cli.command('list')
@click.argument('archive', type=click.Path(exists=True))
@click.option('--long', '-l', is_flag=True, help='Show detailed information')
def list_contents(archive: str, long: bool):
    """
     List contents of a ZIP archive.
    
    \b
    Examples:
        pagonic list archive.zip
        pagonic list archive.zip -l
    """
    from Pagonic.core.formats.zip_reader import ZipReader
    
    console.print()
    
    try:
        # Create reader
        reader = ZipReader(archive)
        entries = reader._get_entries()  # Use internal method
        
        # Calculate totals
        total_uncompressed = sum(e.uncompressed_size for e in entries)
        total_compressed = sum(e.compressed_size for e in entries)
        
        # Create table
        table = Table(
            title=f" {Path(archive).name}",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        
        table.add_column("File", style="white", no_wrap=False)
        table.add_column("Size", justify="right", style="green")
        
        if long:
            table.add_column("Compressed", justify="right", style="yellow")
            table.add_column("Ratio", justify="right", style="magenta")
            table.add_column("Method", justify="center", style="dim")
        
        # Add rows
        for entry in entries:
            if long:
                method = "Deflate" if entry.compression_method == 8 else "Store"
                table.add_row(
                    entry.filename,
                    format_size(entry.uncompressed_size),
                    format_size(entry.compressed_size),
                    format_ratio(entry.uncompressed_size, entry.compressed_size),
                    method
                )
            else:
                table.add_row(
                    entry.filename,
                    format_size(entry.uncompressed_size)
                )
        
        console.print(table)
        
        # Summary
        console.print()
        console.print(Panel.fit(
            f"[bold] Summary[/]\n"
            f"Files: [cyan]{len(entries)}[/] | "
            f"Total: [green]{format_size(total_uncompressed)}[/] | "
            f"Compressed: [yellow]{format_size(total_compressed)}[/] | "
            f"Ratio: [magenta]{format_ratio(total_uncompressed, total_compressed)}[/]",
            border_style="dim"
        ))
        console.print()
        
    except Exception as e:
        console.print(f"\n[red] Error:[/] {str(e)}")
        raise SystemExit(1)


@cli.command()
@click.argument('archive', type=click.Path(exists=True))
def info(archive: str):
    """
     Show detailed information about a ZIP archive.
    
    \b
    Examples:
        pagonic info archive.zip
    """
    from Pagonic.core.formats.zip_reader import ZipReader
    
    console.print()
    
    try:
        # Create reader
        reader = ZipReader(archive)
        entries = reader._get_entries()  # Use internal method
        
        # Calculate stats
        total_uncompressed = sum(e.uncompressed_size for e in entries)
        total_compressed = sum(e.compressed_size for e in entries)
        archive_size = os.path.getsize(archive)
        
        # File type distribution
        extensions = {}
        for entry in entries:
            ext = Path(entry.filename).suffix.lower() or "(no ext)"
            extensions[ext] = extensions.get(ext, 0) + 1
        
        # Top 5 extensions
        top_extensions = sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Info panel
        console.print(Panel.fit(
            f"[bold cyan] Archive Information[/]\n\n"
            f"[dim]Path:[/] {archive}\n"
            f"[dim]Size:[/] {format_size(archive_size)}\n"
            f"[dim]Files:[/] {len(entries)}",
            title=f" {Path(archive).name}",
            border_style="cyan"
        ))
        
        # Stats table
        table = Table(title=" Statistics", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row(" Total Files", str(len(entries)))
        table.add_row(" Uncompressed Size", format_size(total_uncompressed))
        table.add_row(" Compressed Size", format_size(total_compressed))
        table.add_row(" Compression Ratio", format_ratio(total_uncompressed, total_compressed))
        table.add_row(" Archive Size", format_size(archive_size))
        
        console.print(table)
        
        # File types table
        if top_extensions:
            console.print()
            type_table = Table(title=" File Types", box=box.ROUNDED)
            type_table.add_column("Extension", style="cyan")
            type_table.add_column("Count", justify="right", style="green")
            
            for ext, count in top_extensions:
                type_table.add_row(ext, str(count))
            
            console.print(type_table)
        
        console.print()
        
    except Exception as e:
        console.print(f"\n[red] Error:[/] {str(e)}")
        raise SystemExit(1)


# Entry point
if __name__ == '__main__':
    cli()
