from enum import Enum, auto
class CompressionMethod(Enum):
    """压缩方法枚举"""
    NONE = None
    LZ4 = "lz4"
    ZSTD = "zstd"
    LZMA = "lzma"
    LZ4HC = "lz4hc"
    LZHAM = "lzham"
    LZ4HC_OLD = "lz4hc_old"
    LZ4_FAST = "lz4_fast"
    LZ4_HIGH = "lz4_high"