def obfuscate_lz4(data: bytes) -> bytes:
    """
    对LZ4格式的数据进行混淆：
    1. 将token字节的高4位和低4位互换
    2. 将匹配偏移量改为大端序（高位在前）
    """
    ip = 0
    obf = bytearray(data)
    
    while ip < len(obf):
        # 1. 交换token字节的高4位和低4位
        val = obf[ip]
        low = val & 0x0F
        high = (val & 0xF0) >> 4
        obf[ip] = (low << 4) | high
        ip += 1
        
        # 跳过字面量部分
        if high == 15:  # 如果字面量长度是15，需要读取扩展长度
            while ip < len(obf) and obf[ip] == 255:
                ip += 1
            ip += 1
        ip += high
        
        # 2. 将偏移量改为大端序
        if ip + 1 < len(obf):
            offset = (obf[ip] << 8) | obf[ip + 1]  # 读取小端序的偏移量
            obf[ip] = offset & 0xFF  # 低字节
            obf[ip + 1] = (offset >> 8) & 0xFF  # 高字节
            ip += 2
            
        # 跳过匹配部分
        if low == 15:  # 如果匹配长度是15，需要读取扩展长度
            while ip < len(obf) and obf[ip] == 255:
                ip += 1
            ip += 1
            
    return bytes(obf) 