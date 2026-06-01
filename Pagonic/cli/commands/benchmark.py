"""
Pagonic CLI - Benchmark Command
================================
Performance benchmarking for Pagonic compression engine.

Phase 3, Week 5: CLI Development
Days 31-35: Advanced Features
"""

import os
import time
import tempfile
import random
import string
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from rich import box

from Pagonic.cli.utils import format_size, format_time

console = Console()


def generate_test_data(size_mb: int) -> bytes:
    """Generate compressible test data."""
    # Mix of random and repetitive data (realistic compression scenario)
    chunk_size = 1024 * 1024  # 1 MB chunks
    data = bytearray()
    
    for i in range(size_mb):
        if i % 3 == 0:
            # Highly compressible: repeated text
            text = "The quick brown fox jumps over the lazy dog. " * 23000
            data.extend(text.encode('utf-8')[:chunk_size])
        elif i % 3 == 1:
            # Medium compressible: code-like
            lines = []
            for j in range(5000):
                lines.append(f"def function_{j}(x, y): return x + y * {j}")
            code = "\n".join(lines)
            data.extend(code.encode('utf-8')[:chunk_size])
        else:
            # Low compressible: random data
            random_bytes = bytes([random.randint(0, 255) for _ in range(chunk_size)])
            data.extend(random_bytes)
    
    return bytes(data)


def run_compression_benchmark(size_mb: int, level: int, iterations: int) -> dict:
    """Run compression benchmark."""
    from Pagonic.core.formats.zip_writer import ZipWriter
    
    results = {
        'compress_times': [],
        'compress_speeds': [],
        'ratios': [],
        'output_sizes': []
    }
    
    # Generate test data once
    console.print(f"[dim]Generating {size_mb} MB test data...[/]")
    test_data = generate_test_data(size_mb)
    original_size = len(test_data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test file
        test_file = Path(tmpdir) / "benchmark_data.bin"
        test_file.write_bytes(test_data)
        
        for i in range(iterations):
            output_zip = Path(tmpdir) / f"benchmark_{i}.zip"
            
            # Compress
            start = time.perf_counter()
            writer = ZipWriter(str(output_zip), compression_level=level)
            writer.add_file(str(test_file))
            writer.finalize()
            end = time.perf_counter()
            
            compress_time = end - start
            output_size = output_zip.stat().st_size
            compress_speed = original_size / compress_time / 1024 / 1024  # MB/s
            ratio = (1 - output_size / original_size) * 100
            
            results['compress_times'].append(compress_time)
            results['compress_speeds'].append(compress_speed)
            results['output_sizes'].append(output_size)
            results['ratios'].append(ratio)
            
            # Cleanup
            output_zip.unlink()
    
    # Calculate averages
    results['avg_compress_time'] = sum(results['compress_times']) / len(results['compress_times'])
    results['avg_compress_speed'] = sum(results['compress_speeds']) / len(results['compress_speeds'])
    results['avg_ratio'] = sum(results['ratios']) / len(results['ratios'])
    results['avg_output_size'] = sum(results['output_sizes']) / len(results['output_sizes'])
    results['original_size'] = original_size
    
    return results


def run_decompression_benchmark(size_mb: int, level: int, iterations: int) -> dict:
    """Run decompression benchmark."""
    from Pagonic.core.formats.zip_writer import ZipWriter
    from Pagonic.core.formats.zip_reader import ZipReader
    
    results = {
        'decompress_times': [],
        'decompress_speeds': []
    }
    
    # Generate and compress test data
    console.print(f"[dim]Preparing compressed archive...[/]")
    test_data = generate_test_data(size_mb)
    original_size = len(test_data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test file and archive
        test_file = Path(tmpdir) / "benchmark_data.bin"
        test_file.write_bytes(test_data)
        
        archive_path = Path(tmpdir) / "benchmark.zip"
        writer = ZipWriter(str(archive_path), compression_level=level)
        writer.add_file(str(test_file))
        writer.finalize()
        
        # Remove original file
        test_file.unlink()
        
        for i in range(iterations):
            output_dir = Path(tmpdir) / f"output_{i}"
            output_dir.mkdir()
            
            # Decompress
            start = time.perf_counter()
            reader = ZipReader(str(archive_path))
            reader.extract_all(str(output_dir))
            end = time.perf_counter()
            
            decompress_time = end - start
            decompress_speed = original_size / decompress_time / 1024 / 1024  # MB/s
            
            results['decompress_times'].append(decompress_time)
            results['decompress_speeds'].append(decompress_speed)
            
            # Cleanup
            for f in output_dir.iterdir():
                f.unlink()
            output_dir.rmdir()
    
    # Calculate averages
    results['avg_decompress_time'] = sum(results['decompress_times']) / len(results['decompress_times'])
    results['avg_decompress_speed'] = sum(results['decompress_speeds']) / len(results['decompress_speeds'])
    results['original_size'] = original_size
    
    return results


@click.command()
@click.option('--size', '-s', default=10, type=click.IntRange(1, 500), 
              help='Test data size in MB (1-500)')
@click.option('--level', '-l', default=6, type=click.IntRange(0, 9), 
              help='Compression level (0-9)')
@click.option('--iterations', '-i', default=3, type=click.IntRange(1, 10), 
              help='Number of benchmark iterations (1-10)')
@click.option('--compress-only', is_flag=True, help='Run only compression benchmark')
@click.option('--decompress-only', is_flag=True, help='Run only decompression benchmark')
def benchmark(size: int, level: int, iterations: int, compress_only: bool, decompress_only: bool):
    """
     Run performance benchmark.
    
    Tests compression and decompression speed with generated test data.
    
    \b
    Examples:
        pagonic benchmark                    # Default: 10MB, level 6, 3 iterations
        pagonic benchmark -s 50 -l 9         # 50MB with max compression
        pagonic benchmark -s 100 -i 5        # 100MB with 5 iterations
        pagonic benchmark --compress-only    # Only test compression
    """
    console.print()
    console.print(Panel.fit(
        f"[bold magenta] Pagonic Performance Benchmark[/]",
        subtitle=f"Size: {size}MB | Level: {level} | Iterations: {iterations}",
        border_style="magenta"
    ))
    console.print()
    
    try:
        # Compression benchmark
        if not decompress_only:
            console.print("[bold cyan] Compression Benchmark[/]")
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Running compression tests...", total=None)
                compress_results = run_compression_benchmark(size, level, iterations)
                progress.update(task, description="[green]Compression tests complete![/]")
        
        # Decompression benchmark
        if not compress_only:
            console.print()
            console.print("[bold green] Decompression Benchmark[/]")
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Running decompression tests...", total=None)
                decompress_results = run_decompression_benchmark(size, level, iterations)
                progress.update(task, description="[green]Decompression tests complete![/]")
        
        # Results table
        console.print()
        table = Table(title=" Benchmark Results", box=box.ROUNDED)
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        table.add_column("Notes", style="dim")
        
        table.add_row(" Test Size", format_size(size * 1024 * 1024), f"{size} MB")
        table.add_row(" Compression Level", str(level), "0=fastest, 9=best")
        table.add_row(" Iterations", str(iterations), "")
        table.add_row("", "", "")  # Separator
        
        if not decompress_only:
            table.add_row(
                " Compress Speed", 
                f"[bold]{compress_results['avg_compress_speed']:.1f} MB/s[/]",
                f"{max(compress_results['compress_speeds']) - min(compress_results['compress_speeds']):.1f}"
            )
            table.add_row(
                " Compression Ratio",
                f"{compress_results['avg_ratio']:.1f}%",
                f"{format_size(compress_results['avg_output_size'])} output"
            )
            table.add_row(
                " Compress Time",
                format_time(compress_results['avg_compress_time']),
                f"per {size}MB"
            )
        
        if not compress_only:
            if not decompress_only:
                table.add_row("", "", "")  # Separator
            table.add_row(
                " Decompress Speed",
                f"[bold]{decompress_results['avg_decompress_speed']:.1f} MB/s[/]",
                f"{max(decompress_results['decompress_speeds']) - min(decompress_results['decompress_speeds']):.1f}"
            )
            table.add_row(
                " Decompress Time",
                format_time(decompress_results['avg_decompress_time']),
                f"per {size}MB"
            )
        
        console.print(table)
        
        # Summary panel
        console.print()
        console.print(Panel.fit(
            f"[bold] Performance Summary[/]\n\n"
            f"Pagonic achieves [bold green]{compress_results['avg_compress_speed']:.0f} MB/s[/] compression "
            f"and [bold green]{decompress_results['avg_decompress_speed']:.0f} MB/s[/] decompression "
            f"for this local benchmark run.",
            border_style="green"
        ) if not compress_only and not decompress_only else None)
        
        console.print()
        console.print("[bold green] Benchmark complete![/]")
        console.print()
        
    except Exception as e:
        console.print(f"\n[red] Benchmark error:[/] {str(e)}")
        raise SystemExit(1)


if __name__ == '__main__':
    benchmark()
