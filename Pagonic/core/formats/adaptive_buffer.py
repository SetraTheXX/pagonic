"""
Adaptive Buffer Sizing Algorithm
===============================

Bu modül dosya boyutu, sıkıştırma oranı ve sistem kaynaklarına göre
optimal tampon boyutunu dinamik olarak belirler.

Hedef: Dosya boyutuna göre optimal tampon seçimi
"""

import os
import psutil
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class FileMetrics:
    """Dosya için hesaplanan metrikler"""
    file_size: int
    compression_ratio: float
    estimated_uncompressed_size: int
    file_type: str  # 'small', 'medium', 'large', 'huge'

@dataclass
class SystemResources:
    """Sistem kaynak durumu"""
    available_memory_mb: int
    cpu_percent: float
    memory_percent: float
    is_memory_pressure: bool

class AdaptiveBufferSizer:
    """
    Dosya özelliklerine ve sistem durumuna göre optimal tampon boyutu hesaplayıcı
    
    Algoritma:
    1. Dosya boyutu analizi (small/medium/large/huge)
    2. Sistem bellek durumu kontrolü
    3. Sıkıştırma oranı tahmini
    4. Optimal chunk size ve buffer size hesaplama
    """
    
    def __init__(self):
        # Buffer size thresholds (bytes)
        self.buffer_sizes = {
            'small': 64 * 1024,      # 64KB - <1MB files
            'medium': 256 * 1024,    # 256KB - 1-10MB files
            'large': 1024 * 1024,    # 1MB - 10-100MB files
            'huge': 4 * 1024 * 1024  # 4MB - >100MB files
        }
        
        # File size thresholds (bytes)
        self.size_thresholds = {
            'small': 1024 * 1024,      # 1MB
            'medium': 10 * 1024 * 1024, # 10MB
            'large': 100 * 1024 * 1024  # 100MB
        }
        
        # Compression ratio estimates by file type
        self.compression_estimates = {
            '.txt': 0.3,    # Text files compress well
            '.log': 0.4,    # Log files compress well
            '.csv': 0.5,    # CSV files moderate compression
            '.json': 0.6,   # JSON moderate compression
            '.xml': 0.5,    # XML moderate compression
            '.zip': 0.98,   # Already compressed
            '.jpg': 0.95,   # Already compressed
            '.png': 0.95,   # Already compressed
            '.mp3': 0.98,   # Already compressed
            '.mp4': 0.98,   # Already compressed
            'default': 0.7  # Default estimate
        }
        
        # Memory pressure thresholds
        self.memory_pressure_threshold = 85.0  # %85 memory usage
    
    def analyze_file(self, file_path: str, compressed_size: Optional[int] = None) -> FileMetrics:
        """
        Dosyayı analiz et ve metriklerini hesapla
        
        Args:
            file_path: Analiz edilecek dosya yolu
            compressed_size: Bilinen sıkıştırılmış boyut (ZIP entry'den)
            
        Returns:
            FileMetrics: Dosya metrikleri
        """
        try:
            # Dosya boyutunu al
            if compressed_size is not None:
                file_size = compressed_size
            else:
                file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            
            # Dosya uzantısından compression ratio tahmin et
            file_ext = os.path.splitext(file_path)[1].lower()
            compression_ratio = self.compression_estimates.get(file_ext, self.compression_estimates['default'])
            
            # Uncompressed size tahmin et
            estimated_uncompressed_size = int(file_size / compression_ratio)
            
            # Dosya tipini belirle
            file_type = self._classify_file_size(estimated_uncompressed_size)
            
            return FileMetrics(
                file_size=file_size,
                compression_ratio=compression_ratio,
                estimated_uncompressed_size=estimated_uncompressed_size,
                file_type=file_type
            )
            
        except Exception as e:
            logger.warning(f"Failed to analyze file {file_path}: {e}")
            # Fallback metrics
            return FileMetrics(
                file_size=compressed_size or 1024,
                compression_ratio=0.7,
                estimated_uncompressed_size=int((compressed_size or 1024) / 0.7),
                file_type='small'
            )
    
    def get_system_resources(self) -> SystemResources:
        """
        Mevcut sistem kaynaklarını analiz et
        
        Returns:
            SystemResources: Sistem kaynak durumu
        """
        try:
            # Memory info
            memory = psutil.virtual_memory()
            available_memory_mb = memory.available // (1024 * 1024)
            memory_percent = memory.percent
            
            # CPU info
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory pressure detection
            is_memory_pressure = memory_percent > self.memory_pressure_threshold
            
            return SystemResources(
                available_memory_mb=available_memory_mb,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                is_memory_pressure=is_memory_pressure
            )
            
        except Exception as e:
            logger.warning(f"Failed to get system resources: {e}")
            # Fallback conservative values
            return SystemResources(
                available_memory_mb=1024,  # 1GB
                cpu_percent=50.0,
                memory_percent=60.0,
                is_memory_pressure=False
            )
    
    def calculate_optimal_buffer_size(self, file_metrics: FileMetrics, system_resources: SystemResources) -> Tuple[int, int]:
        """
        Optimal buffer size ve chunk size hesapla
        
        Args:
            file_metrics: Dosya metrikleri
            system_resources: Sistem kaynak durumu
            
        Returns:
            Tuple[int, int]: (buffer_size, chunk_size)
        """
        # Base buffer size from file type
        base_buffer_size = self.buffer_sizes[file_metrics.file_type]
        
        # Memory pressure adjustments
        if system_resources.is_memory_pressure:
            # Memory pressure varsa buffer size'ı küçült
            buffer_size = base_buffer_size // 2
            logger.info(f"Memory pressure detected, reducing buffer size to {buffer_size//1024}KB")
        elif system_resources.available_memory_mb > 4096:  # 4GB+ available
            # Bol memory varsa buffer size'ı büyüt
            buffer_size = min(base_buffer_size * 2, 8 * 1024 * 1024)  # Max 8MB
            logger.debug(f"Abundant memory, increasing buffer size to {buffer_size//1024}KB")
        else:
            buffer_size = base_buffer_size
        
        # Chunk size calculation
        # Chunk size genelde buffer size'ın 1/4'ü veya 1/8'i olur
        if file_metrics.file_type == 'huge':
            chunk_size = buffer_size // 4  # Büyük dosyalar için daha büyük chunk
        else:
            chunk_size = buffer_size // 8  # Küçük dosyalar için daha küçük chunk
        
        # Minimum chunk size (8KB)
        chunk_size = max(chunk_size, 8 * 1024)
        
        # Maximum chunk size (1MB)
        chunk_size = min(chunk_size, 1024 * 1024)
        
        logger.debug(f"Calculated buffer_size={buffer_size//1024}KB, chunk_size={chunk_size//1024}KB for {file_metrics.file_type} file")
        
        return buffer_size, chunk_size
    
    def _classify_file_size(self, size: int) -> str:
        """Dosya boyutuna göre sınıflandır"""
        if size < self.size_thresholds['small']:
            return 'small'
        elif size < self.size_thresholds['medium']:
            return 'medium'
        elif size < self.size_thresholds['large']:
            return 'large'
        else:
            return 'huge'
    
    def get_strategy_recommendation(self, file_metrics: FileMetrics, system_resources: SystemResources) -> Dict:
        """
        Dosya için optimal strateji önerisi
        
        Returns:
            Dict: Strateji önerileri
        """
        buffer_size, chunk_size = self.calculate_optimal_buffer_size(file_metrics, system_resources)
        
        # Decompression strategy
        if file_metrics.file_type in ['small', 'medium']:
            strategy = 'direct_memory'  # Direkt memory'de aç
        else:
            strategy = 'streaming'  # Streaming ile aç
        
        # Threading recommendation
        if file_metrics.file_type == 'huge' and not system_resources.is_memory_pressure:
            use_threading = True
        else:
            use_threading = False
        
        return {
            'buffer_size': buffer_size,
            'chunk_size': chunk_size,
            'strategy': strategy,
            'use_threading': use_threading,
            'file_type': file_metrics.file_type,
            'estimated_memory_usage_mb': (buffer_size * 2) // (1024 * 1024),  # Buffer + decompressed data
            'recommendations': self._generate_recommendations(file_metrics, system_resources)
        }
    
    def _generate_recommendations(self, file_metrics: FileMetrics, system_resources: SystemResources) -> List[str]:
        """Optimization önerileri oluştur"""
        recommendations = []
        
        if system_resources.is_memory_pressure:
            recommendations.append(" Memory pressure detected - using smaller buffers")
        
        if file_metrics.compression_ratio > 0.9:
            recommendations.append("📦 File already compressed - expect minimal compression benefit")
        
        if file_metrics.file_type == 'huge':
            recommendations.append("🚀 Large file detected - using streaming decompression")
        
        if system_resources.available_memory_mb > 8192:  # 8GB+
            recommendations.append("💾 Abundant memory - using larger buffers for speed")
        
        if system_resources.cpu_percent > 80:
            recommendations.append("⚡ High CPU usage - limiting parallel processing")
        
        return recommendations


# Global singleton
_adaptive_sizer: Optional[AdaptiveBufferSizer] = None

def get_adaptive_sizer() -> AdaptiveBufferSizer:
    """Global adaptive sizer instance döndür"""
    global _adaptive_sizer
    if _adaptive_sizer is None:
        _adaptive_sizer = AdaptiveBufferSizer()
    return _adaptive_sizer

def get_optimal_buffer_config(file_path: str, compressed_size: Optional[int] = None) -> Dict:
    """
    Dosya için optimal buffer konfigürasyonu al
    
    Args:
        file_path: Dosya yolu
        compressed_size: Bilinen sıkıştırılmış boyut
        
    Returns:
        Dict: Optimal konfigürasyon
    """
    sizer = get_adaptive_sizer()
    file_metrics = sizer.analyze_file(file_path, compressed_size)
    system_resources = sizer.get_system_resources()
    
    return sizer.get_strategy_recommendation(file_metrics, system_resources)


if __name__ == "__main__":
    # Test ve demo
    print("=== Adaptive Buffer Sizing Test ===")
    
    sizer = get_adaptive_sizer()
    
    # Test files
    test_files = [
        ("small_file.txt", 50 * 1024),      # 50KB
        ("medium_file.csv", 5 * 1024 * 1024),   # 5MB
        ("large_file.log", 50 * 1024 * 1024),   # 50MB
        ("huge_file.data", 500 * 1024 * 1024),  # 500MB
        ("compressed.zip", 10 * 1024 * 1024),   # 10MB ZIP
    ]
    
    print("📊 System Resources:")
    system_resources = sizer.get_system_resources()
    print(f"  Available Memory: {system_resources.available_memory_mb:,} MB")
    print(f"  Memory Usage: {system_resources.memory_percent:.1f}%")
    print(f"  CPU Usage: {system_resources.cpu_percent:.1f}%")
    print(f"  Memory Pressure: {' YES' if system_resources.is_memory_pressure else ' NO'}")
    
    print(f"\n🎯 Buffer Size Recommendations:")
    for file_name, size in test_files:
        config = get_optimal_buffer_config(file_name, size)
        
        print(f"\n📁 {file_name} ({size//1024:,}KB)")
        print(f"  File Type: {config['file_type'].upper()}")
        print(f"  Buffer Size: {config['buffer_size']//1024:,}KB")
        print(f"  Chunk Size: {config['chunk_size']//1024:,}KB")
        print(f"  Strategy: {config['strategy']}")
        print(f"  Threading: {' YES' if config['use_threading'] else '❌ NO'}")
        print(f"  Est. Memory: {config['estimated_memory_usage_mb']}MB")
        
        if config['recommendations']:
            print(f"  Recommendations:")
            for rec in config['recommendations']:
                print(f"    {rec}")
    
    print(f"\n🏆 Adaptive buffer sizing ready for integration!")
