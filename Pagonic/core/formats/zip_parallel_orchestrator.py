import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from .zip_structs import ZipAyrıştırıcı, ZipParseError, CompressionMethods
from .simd_crc32 import fast_crc32
from .buffer_pool import get_buffer_pool
from .simd_memory import fast_memcpy
import time
import numpy as np  # Alignment için

dir_creation_lock = threading.Lock()

def safe_makedirs(path):
    """Thread-safe directory creation."""
    with dir_creation_lock:
        os.makedirs(path, exist_ok=True)

class ZipParallelOrchestrator:
    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or os.cpu_count() or 4
        self.dir_lock = threading.Lock()  # Directory creation için global lock
        self.buffer_pool = get_buffer_pool()

    def decompress_parallel(self, archive_path: str, extract_dir: str, progress_callback=None) -> Dict[str, Any]:
        results = {
            "total_entries": 0,
            "success": [],
            "failed": [],
            "metrics": {}
        }
        start_time = time.time()
        try:
            with open(archive_path, 'rb') as f:
                parser = ZipAyrıştırıcı(f)
                eocd = parser.find_eocd()
                cd_entries = parser.parse_cd_entries(eocd)
                results["total_entries"] = len(cd_entries)

                # Her entry için extraction task'ı oluştur
                tasks = []
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_entry = {}
                    for cd_entry in cd_entries:
                        # Her thread kendi file handle'ı ile çalışacak
                        future = executor.submit(
                            self._extract_entry_threadsafe,
                            archive_path,
                            extract_dir,
                            cd_entry
                        )
                        future_to_entry[future] = cd_entry.filename
                    for future in as_completed(future_to_entry):
                        filename = future_to_entry[future]
                        try:
                            result = future.result()
                            if result["success"]:
                                results["success"].append(filename)
                            else:
                                results["failed"].append({"file": filename, "error": result["error"]})
                        except Exception as exc:
                            results["failed"].append({"file": filename, "error": str(exc)})
                        if progress_callback:
                            progress_callback(filename)
        except Exception as e:
            results["failed"].append({"file": "__archive__", "error": str(e)})

        end_time = time.time()
        results["metrics"] = {
            "duration_sec": end_time - start_time,
            "thread_count": self.max_workers,
            "success_count": len(results["success"]),
            "fail_count": len(results["failed"]),
        }
        return results

    def _extract_entry_threadsafe(self, archive_path: str, extract_dir: str, cd_entry) -> Dict[str, Any]:
        try:
            with open(archive_path, 'rb') as f:
                parser = ZipAyrıştırıcı(f)
                local_header = parser.parse_local_file_header(cd_entry)
                # Dosya çıkış yolu
                output_file_path = os.path.join(extract_dir, cd_entry.filename)
                # Klasör ise oluştur ve çık
                if cd_entry.filename.endswith('/'):
                    safe_makedirs(output_file_path)
                    return {"success": True}
                # Klasörleri thread-safe oluştur
                safe_makedirs(os.path.dirname(output_file_path))
                # Sıkıştırılmış veriye seek et
                f.seek(local_header.data_offset)
                compressed_data = f.read(cd_entry.compressed_size)
                # Açma işlemi (deflate/store)
                if cd_entry.compression_method == CompressionMethods.STORE:
                    decompressed_data = compressed_data
                elif cd_entry.compression_method == CompressionMethods.DEFLATE:
                    import zlib
                    decompressor = zlib.decompressobj(-15)
                    decompressed_data = decompressor.decompress(compressed_data)
                    decompressed_data += decompressor.flush()
                else:
                    return {"success": False, "error": f"Unsupported compression method: {cd_entry.compression_method}"}
                # Boyut ve CRC32 doğrulama
                if len(decompressed_data) != cd_entry.uncompressed_size:
                    return {"success": False, "error": f"Size mismatch: expected {cd_entry.uncompressed_size}, got {len(decompressed_data)}"}
                calculated_crc = fast_crc32(decompressed_data, performance_mode=False) & 0xffffffff
                if calculated_crc != cd_entry.crc32:
                    return {"success": False, "error": f"CRC32 mismatch: expected 0x{cd_entry.crc32:08x}, got 0x{calculated_crc:08x}"}
                # Dosyayı yaz
                if len(decompressed_data) >= 4 * 1024 * 1024:  # 4MB+
                    chunk_size = 4 * 1024 * 1024  # 4MB chunk
                    with open(output_file_path, 'wb') as out_f:
                        buffer = np.empty(chunk_size, dtype=np.uint8)
                        assert buffer.ctypes.data % 32 == 0  # 32 byte aligned
                        mv = memoryview(buffer.data)
                        for i in range(0, len(decompressed_data), chunk_size):
                            chunk = decompressed_data[i:i+chunk_size]
                            fast_memcpy(mv, chunk, len(chunk))
                            out_f.write(mv[:len(chunk)])
                else:
                    with open(output_file_path, 'wb') as out_f:
                        buffer = bytearray(len(decompressed_data))
                        fast_memcpy(buffer, decompressed_data, len(decompressed_data))
                        out_f.write(buffer)
                return {"success": True}
        except Exception as e:
            print(f"[ERROR][Thread] Extract failed: {output_file_path} - {e}")
            raise
            return {"success": False, "error": str(e)} 