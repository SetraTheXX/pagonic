"""
Smoke Test: Motor çalışıyor mu?
Basic compress + decompress + verify workflow
"""
import os
import tempfile
import hashlib
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "Pagonic"))

from Pagonic.core.formats.handlers.zip_handler import ZipHandler

def test_basic_functionality():
    """Motor çalışıyor mu: Compress + Decompress + Verify"""
    print("=" * 60)
    print("SMOKE TEST: Basic ZIP Motor Functionality")
    print("=" * 60)

    # Create test data
    test_dir = tempfile.mkdtemp()
    test_file = Path(test_dir) / "test.txt"
    test_data = b"Test data for smoke test" * 1000  # ~25KB
    test_file.write_bytes(test_data)

    # Calculate original hash
    original_hash = hashlib.sha256(test_data).hexdigest()
    print(f"\n1. Test file created: {test_file}")
    print(f"   Size: {len(test_data)} bytes")
    print(f"   SHA256: {original_hash[:16]}...")

    # Compress
    handler = ZipHandler()
    archive = Path(test_dir) / "archive.zip"

    try:
        print(f"\n2. Compressing...")
        handler.compress([str(test_file)], str(archive))

        assert archive.exists(), "ZIP archive was not created!"

        print(f"   SUCCESS: Archive created")
        print(f"   Archive size: {archive.stat().st_size} bytes")

        # Decompress
        output_dir = Path(test_dir) / "output"
        print(f"\n3. Decompressing...")
        handler.decompress(str(archive), str(output_dir))

        # Verify decompressed file
        decompressed = output_dir / "test.txt"
        assert decompressed.exists(), "File was not decompressed!"

        print(f"   SUCCESS: File decompressed")

        # Byte-by-byte verification
        print(f"\n4. Verifying...")
        decompressed_hash = hashlib.sha256(decompressed.read_bytes()).hexdigest()

        assert original_hash == decompressed_hash, (
            f"Hash mismatch: original={original_hash[:16]}..., "
            f"decompressed={decompressed_hash[:16]}..."
        )

        print(f"   SUCCESS: Hash matches!")
        print(f"   SHA256: {decompressed_hash[:16]}...")
        print("\n" + "=" * 60)
        print("MOTOR ÇALIŞIYOR: Compress + Decompress + Verify SUCCESS")
        print("=" * 60)

    except Exception as e:
        print(f"\n   ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Cleanup
        import shutil
        try:
            shutil.rmtree(test_dir)
        except:
            pass

if __name__ == "__main__":
    test_basic_functionality()
