"""
Pagonic CLI Tests
=================
Test suite for Pagonic command-line interface.
"""

import os
import pytest
import tempfile
import json
import zipfile
from pathlib import Path
from click.testing import CliRunner

# Import CLI
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from Pagonic.cli.main import cli


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_files(tmp_path):
    """Create temporary test files."""
    # Create test files
    file1 = tmp_path / "test1.txt"
    file1.write_text("Hello World! This is a test file for compression.")
    
    file2 = tmp_path / "test2.txt"
    file2.write_text("Another test file with different content. " * 100)
    
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    
    file3 = subdir / "nested.txt"
    file3.write_text("Nested file content for testing directory handling.")
    
    return {
        'dir': tmp_path,
        'file1': file1,
        'file2': file2,
        'file3': file3,
        'subdir': subdir
    }


class TestVersionCommand:
    """Tests for --version option."""
    
    def test_version_shows_version(self, runner):
        """Test that --version shows version info."""
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert 'Pagonic' in result.output
        assert '0.3.0' in result.output


class TestHelpCommand:
    """Tests for --help option."""
    
    def test_help_shows_commands(self, runner):
        """Test that --help shows available commands."""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'compress' in result.output
        assert 'extract' in result.output
        assert 'list' in result.output
        assert 'info' in result.output
        assert 'inspect' in result.output
        assert 'verify' in result.output
        assert 'safe-extract' in result.output
        assert 'benchmark' in result.output
        assert 'config' in result.output
    
    def test_compress_help(self, runner):
        """Test compress command help."""
        result = runner.invoke(cli, ['compress', '--help'])
        assert result.exit_code == 0
        assert '--output' in result.output or '-o' in result.output
        assert '--level' in result.output or '-l' in result.output
    
    def test_extract_help(self, runner):
        """Test extract command help."""
        result = runner.invoke(cli, ['extract', '--help'])
        assert result.exit_code == 0
        assert '--output' in result.output or '-o' in result.output
        assert '--verbose' in result.output or '-v' in result.output


class TestCompressCommand:
    """Tests for compress command."""
    
    def test_compress_single_file(self, runner, temp_files):
        """Test compressing a single file."""
        with runner.isolated_filesystem():
            # Copy test file to isolated filesystem
            test_file = Path('test.txt')
            test_file.write_text("Test content for compression")
            
            result = runner.invoke(cli, [
                'compress', 
                str(test_file), 
                '-o', 'output.zip'
            ])
            
            # Should succeed (exit code 0 or output shows success)
            assert 'Success' in result.output or result.exit_code == 0
            assert Path('output.zip').exists()
    
    def test_compress_multiple_files(self, runner):
        """Test compressing multiple files."""
        with runner.isolated_filesystem():
            # Create test files
            Path('file1.txt').write_text("Content 1")
            Path('file2.txt').write_text("Content 2")
            
            result = runner.invoke(cli, [
                'compress',
                'file1.txt',
                'file2.txt',
                '-o', 'multi.zip'
            ])
            
            assert Path('multi.zip').exists()
    
    def test_compress_with_level(self, runner):
        """Test compression with custom level."""
        with runner.isolated_filesystem():
            Path('test.txt').write_text("Test content " * 100)
            
            result = runner.invoke(cli, [
                'compress',
                'test.txt',
                '-o', 'test.zip',
                '-l', '9'  # Max compression
            ])
            
            assert result.exit_code == 0 or 'Success' in result.output
    
    def test_compress_no_files_error(self, runner):
        """Test that compress with no files shows error."""
        result = runner.invoke(cli, ['compress', '-o', 'test.zip'])
        # Should show error about missing files
        assert result.exit_code != 0 or 'Error' in result.output or 'Missing' in result.output
    
    def test_compress_nonexistent_file_error(self, runner):
        """Test that compressing nonexistent file shows error."""
        result = runner.invoke(cli, [
            'compress',
            'nonexistent.txt',
            '-o', 'test.zip'
        ])
        assert result.exit_code != 0


class TestExtractCommand:
    """Tests for extract command."""
    
    def test_extract_to_directory(self, runner):
        """Test extracting to a directory."""
        with runner.isolated_filesystem():
            # Create a zip file first
            Path('source.txt').write_text("Source content for extraction test")
            
            runner.invoke(cli, [
                'compress',
                'source.txt',
                '-o', 'test.zip'
            ])
            
            # Extract
            result = runner.invoke(cli, [
                'extract',
                'test.zip',
                '-o', 'output'
            ])
            
            assert 'Success' in result.output or result.exit_code == 0
            assert Path('output').exists()
    
    def test_extract_nonexistent_archive_error(self, runner):
        """Test that extracting nonexistent archive shows error."""
        result = runner.invoke(cli, [
            'extract',
            'nonexistent.zip'
        ])
        assert result.exit_code != 0


class TestListCommand:
    """Tests for list command."""
    
    def test_list_archive_contents(self, runner):
        """Test listing archive contents."""
        with runner.isolated_filesystem():
            # Create test archive
            Path('file1.txt').write_text("Content 1")
            Path('file2.txt').write_text("Content 2")
            
            runner.invoke(cli, [
                'compress',
                'file1.txt', 'file2.txt',
                '-o', 'test.zip'
            ])
            
            result = runner.invoke(cli, ['list', 'test.zip'])
            
            assert result.exit_code == 0
            assert 'file1.txt' in result.output
            assert 'file2.txt' in result.output
    
    def test_list_long_format(self, runner):
        """Test list with long format."""
        with runner.isolated_filesystem():
            Path('test.txt').write_text("Test content")
            runner.invoke(cli, ['compress', 'test.txt', '-o', 'test.zip'])
            
            result = runner.invoke(cli, ['list', 'test.zip', '-l'])
            
            assert result.exit_code == 0
            # Long format should show more columns
            assert 'Compressed' in result.output or 'Ratio' in result.output

    def test_list_tree_format(self, runner):
        """Test list with tree output."""
        with runner.isolated_filesystem():
            Path('docs').mkdir()
            Path('docs/readme.txt').write_text("Readme")
            Path('docs/guide.txt').write_text("Guide")
            runner.invoke(cli, ['compress', 'docs', '-o', 'docs.zip'])

            result = runner.invoke(cli, ['list', 'docs.zip', '--tree'])

            assert result.exit_code == 0
            assert 'docs.zip' in result.output
            assert 'readme.txt' in result.output
            assert 'guide.txt' in result.output


class TestInfoCommand:
    """Tests for info command."""
    
    def test_info_shows_archive_details(self, runner):
        """Test info command shows archive details."""
        with runner.isolated_filesystem():
            Path('test.txt').write_text("Information test content " * 50)
            runner.invoke(cli, ['compress', 'test.txt', '-o', 'test.zip'])
            
            result = runner.invoke(cli, ['info', 'test.zip'])
            
            assert result.exit_code == 0
            assert 'test.zip' in result.output
            # Should show statistics
            assert 'Files' in result.output or 'Size' in result.output


class TestInspectCommand:
    """Tests for inspect command."""

    def test_inspect_clean_archive(self, runner):
        with runner.isolated_filesystem():
            Path('safe.txt').write_text("Safe content")
            runner.invoke(cli, ['compress', 'safe.txt', '-o', 'safe.zip'])

            result = runner.invoke(cli, ['inspect', 'safe.zip'])

            assert result.exit_code == 0
            assert 'ZIP Inspection' in result.output
            assert 'OK' in result.output

    def test_inspect_json_output(self, runner):
        with runner.isolated_filesystem():
            Path('safe.txt').write_text("Safe content")
            runner.invoke(cli, ['compress', 'safe.txt', '-o', 'safe.zip'])

            result = runner.invoke(cli, ['inspect', 'safe.zip', '--json'])

            assert result.exit_code == 0
            payload = json.loads(result.output)
            expected_report_keys = {
                'archive_path',
                'file_count',
                'total_compressed_size',
                'total_uncompressed_size',
                'global_compression_ratio',
                'risk_level',
                'risk_flags',
                'warnings',
                'errors',
                'recommended_action',
                'entries',
            }
            expected_entry_keys = {
                'original_name',
                'normalized_name',
                'safe_name',
                'compressed_size',
                'uncompressed_size',
                'compression_method',
                'compression_ratio',
                'crc32',
                'risk_flags',
            }
            assert expected_report_keys.issubset(payload)
            assert payload['risk_level'] == 'ok'
            assert payload['risk_flags'] == []
            assert payload['recommended_action']
            assert expected_entry_keys.issubset(payload['entries'][0])
            assert payload['entries'][0]['original_name'] == 'safe.txt'
            assert payload['entries'][0]['safe_name'] == 'safe.txt'

    def test_inspect_markdown_output(self, runner):
        with runner.isolated_filesystem():
            Path('safe.txt').write_text("Safe content")
            runner.invoke(cli, ['compress', 'safe.txt', '-o', 'safe.zip'])

            result = runner.invoke(cli, ['inspect', 'safe.zip', '--markdown'])

            assert result.exit_code == 0
            assert '# ZIP Inspection Report' in result.output
            assert '## Archive Summary' in result.output
            assert '## Risk Flags' in result.output
            assert '## Entries' in result.output
            assert 'Recommended action' in result.output
            assert 'safe.txt' in result.output

    def test_inspect_reports_risky_archive(self, runner):
        with runner.isolated_filesystem():
            with zipfile.ZipFile('risky.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('../../evil.txt', 'nope')
                archive.writestr(r'C:\Users\Admin\file.doc', 'data')

            result = runner.invoke(cli, ['inspect', 'risky.zip', '--json'])

            assert result.exit_code == 0
            payload = json.loads(result.output)
            flags = {flag for entry in payload['entries'] for flag in entry['risk_flags']}
            assert payload['risk_level'] == 'high'
            assert 'path_traversal' in payload['risk_flags']
            assert 'windows_drive_path' in payload['risk_flags']
            assert 'path_traversal' in flags
            assert 'windows_drive_path' in flags

    def test_inspect_rejects_multiple_output_formats(self, runner):
        with runner.isolated_filesystem():
            Path('safe.txt').write_text("Safe content")
            runner.invoke(cli, ['compress', 'safe.txt', '-o', 'safe.zip'])

            result = runner.invoke(cli, ['inspect', 'safe.zip', '--json', '--markdown'])

            assert result.exit_code == 1
            assert 'Use only one output format' in result.output


class TestVerifyCommand:
    """Tests for verify command."""

    def test_verify_clean_archive_exits_zero(self, runner):
        with runner.isolated_filesystem():
            Path('safe.txt').write_text("Safe content")
            runner.invoke(cli, ['compress', 'safe.txt', '-o', 'safe.zip'])

            result = runner.invoke(cli, ['verify', 'safe.zip'])

            assert result.exit_code == 0
            assert 'OK' in result.output

    def test_verify_risky_archive_exits_one(self, runner):
        with runner.isolated_filesystem():
            with zipfile.ZipFile('risky.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('../../evil.txt', 'nope')

            result = runner.invoke(cli, ['verify', 'risky.zip'])

            assert result.exit_code == 1
            assert 'FAILED' in result.output
            assert 'path_traversal' in result.output

    def test_verify_medium_risk_exits_one(self, runner):
        with runner.isolated_filesystem():
            with zipfile.ZipFile('suspicious.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('payload.exe', 'MZ')

            result = runner.invoke(cli, ['verify', 'suspicious.zip'])

            assert result.exit_code == 1
            assert 'suspicious_extension' in result.output

    def test_verify_accepts_configured_max_risk(self, runner):
        with runner.isolated_filesystem():
            with zipfile.ZipFile('suspicious.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('payload.exe', 'MZ')

            result = runner.invoke(cli, ['verify', 'suspicious.zip', '--max-risk', 'medium'])

            assert result.exit_code == 0
            assert 'OK' in result.output
            assert 'max risk' in result.output


class TestSafeExtractCommand:
    """Tests for safe-extract command."""

    def test_safe_extract_clean_archive(self, runner):
        with runner.isolated_filesystem():
            Path('safe.txt').write_text("Safe content")
            runner.invoke(cli, ['compress', 'safe.txt', '-o', 'safe.zip'])

            result = runner.invoke(cli, ['safe-extract', 'safe.zip', 'out'])

            assert result.exit_code == 0
            assert 'Extracted' in result.output
            assert Path('out/safe.txt').exists()

    def test_safe_extract_refuses_high_risk_by_default(self, runner):
        with runner.isolated_filesystem():
            with zipfile.ZipFile('risky.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('../../evil.txt', 'nope')

            result = runner.invoke(cli, ['safe-extract', 'risky.zip', 'out'])

            assert result.exit_code == 1
            assert 'Refused' in result.output
            assert not Path('out/evil.txt').exists()

    def test_safe_extract_override_keeps_output_inside_target(self, runner):
        with runner.isolated_filesystem():
            with zipfile.ZipFile('risky.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('../../evil.txt', 'nope')

            result = runner.invoke(cli, ['safe-extract', 'risky.zip', 'out', '--allow-risk', 'high'])

            assert result.exit_code == 0
            assert Path('out/evil.txt').exists()
            assert not Path('evil.txt').exists()

    def test_safe_extract_dry_run_does_not_write_files(self, runner):
        with runner.isolated_filesystem():
            Path('safe.txt').write_text("Safe content")
            runner.invoke(cli, ['compress', 'safe.txt', '-o', 'safe.zip'])

            result = runner.invoke(cli, ['safe-extract', 'safe.zip', 'out', '--dry-run'])

            assert result.exit_code == 0
            assert 'Dry run OK' in result.output
            assert not Path('out').exists()


class TestConfigCommand:
    """Tests for config command."""
    
    def test_config_list(self, runner):
        """Test config list command."""
        result = runner.invoke(cli, ['config', 'list'])
        
        assert result.exit_code == 0
        assert 'compression_level' in result.output
        assert 'theme' in result.output
    
    def test_config_get(self, runner):
        """Test config get command."""
        result = runner.invoke(cli, ['config', 'get', 'compression_level'])
        
        assert result.exit_code == 0
        assert 'compression_level' in result.output
    
    def test_config_get_invalid_key(self, runner):
        """Test config get with invalid key."""
        result = runner.invoke(cli, ['config', 'get', 'invalid_key_xyz'])
        
        # Should show warning or error
        assert 'not found' in result.output.lower() or result.exit_code != 0
    
    def test_config_path(self, runner):
        """Test config path command."""
        result = runner.invoke(cli, ['config', 'path'])
        
        assert result.exit_code == 0
        assert 'config' in result.output.lower()


class TestBenchmarkCommand:
    """Tests for benchmark command."""
    
    def test_benchmark_help(self, runner):
        """Test benchmark command help."""
        result = runner.invoke(cli, ['benchmark', '--help'])
        
        assert result.exit_code == 0
        assert '--size' in result.output or '-s' in result.output
        assert '--level' in result.output or '-l' in result.output
    
    # Note: Actual benchmark tests are slow, so we skip in CI
    @pytest.mark.slow
    def test_benchmark_runs(self, runner):
        """Test benchmark command runs (slow test)."""
        result = runner.invoke(cli, ['benchmark', '-s', '1', '-i', '1'])
        
        assert 'Benchmark' in result.output


# Quick test runner
if __name__ == '__main__':
    print("🧪 Running CLI Tests...")
    
    runner = CliRunner()
    
    # Test version
    result = runner.invoke(cli, ['--version'])
    print(f"  Version: {'✅' if 'Pagonic' in result.output else '❌'}")
    
    # Test help
    result = runner.invoke(cli, ['--help'])
    print(f"  Help: {'✅' if 'compress' in result.output else '❌'}")
    
    # Test commands exist
    for cmd in ['compress', 'extract', 'list', 'info', 'config', 'benchmark']:
        result = runner.invoke(cli, [cmd, '--help'])
        status = '✅' if result.exit_code == 0 else '❌'
        print(f"  {cmd}: {status}")
    
    print("\n🎉 CLI tests complete!")
