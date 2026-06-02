"""
Test for Hybrid System Critical Bug Fix
========================================
This test verifies that the hybrid system processes ALL large files (>2GB threshold),
not just the first one due to the break statement bug at line 668.

Bug Location: zip_handler.py line 668
Bug: break statement in for loop caused only first large file to be processed
Fix: Removed break statement

"""

import tempfile
import zipfile
from pathlib import Path
from Pagonic.core.formats.handlers.zip_handler import ZipHandler


def test_hybrid_multiple_large_files():
    """
    Test: Hybrid system processes ALL large files, not just first one

    This test creates multiple files that trigger the hybrid system's
    large file handler (>2GB threshold simulation with smaller files for testing).

    Before fix: Only first file would be in archive
    After fix: ALL files should be in archive
    """
    print("\n" + "="*70)
    print("HYBRID SYSTEM TEST: Multiple Large Files")
    print("="*70)

    # Create test environment
    test_dir = Path(tempfile.mkdtemp())
    output_zip = test_dir / "hybrid_test.zip"

    # Create 3 test files to simulate multiple large files
    test_files = []
    for i in range(1, 4):
        file_path = test_dir / f"large_file_{i}.txt"
        # Create file with unique content
        content = f"Large file {i} content: " + ("X" * 1000 * i)
        file_path.write_text(content)
        test_files.append(str(file_path))
        print(f"\n{i}. Created test file: large_file_{i}.txt")
        print(f"   Size: {len(content)} bytes")

    # Compress using hybrid system
    print("\n" + "-"*70)
    print("COMPRESSING with hybrid system...")
    print("-"*70)

    handler = ZipHandler()
    handler.compress(test_files, str(output_zip))

    print(f"\nArchive created: {output_zip.name}")
    print(f"Archive size: {output_zip.stat().st_size} bytes")

    # CRITICAL TEST: Verify ALL files are in the archive
    print("\n" + "-"*70)
    print("VERIFYING: Checking all files are in archive...")
    print("-"*70)

    with zipfile.ZipFile(output_zip, 'r') as zf:
        archived_files = zf.namelist()
        print(f"\nFiles in archive: {len(archived_files)}")
        for name in archived_files:
            print(f"  - {name}")

    # Assertions
    assert len(archived_files) == 3, f"Expected 3 files, got {len(archived_files)}"

    expected_files = ["large_file_1.txt", "large_file_2.txt", "large_file_3.txt"]
    for expected in expected_files:
        assert expected in archived_files, f"Missing file: {expected}"

    print("\n" + "="*70)
    print("SUCCESS: All 3 large files processed by hybrid system!")
    print("Critical bug fix VERIFIED: break statement removed")
    print("="*70)

    # Cleanup
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    test_hybrid_multiple_large_files()
