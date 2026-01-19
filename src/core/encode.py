def encode_data(compressed_data: bytes) -> bytes:
    ip = 0
    op = 0
    AK_LITERAL_LENGTH_MASK = ((1 << 4) - 1) & 0xFF
    AK_MATCH_LENGTH_MASK = (~AK_LITERAL_LENGTH_MASK) & 0xFF
    obfuscated_data = bytearray(compressed_data)

    while True:
        # 1. 读取原始LZ4的控制字节
        literal_length = obfuscated_data[ip] >> 4  # 原始高4位
        match_length = obfuscated_data[ip] & AK_LITERAL_LENGTH_MASK  # 原始低4位

        # 2. 交换控制字节的位顺序
        obfuscated_data[ip] = (match_length << 4 | literal_length) & 0xFF
        ip += 1

        # 3. 处理字面量长度
        if literal_length == 15:
            l, ip = read_long_length_no_check(obfuscated_data, ip)
            literal_length += l
        ip += literal_length

        # 4. 处理偏移量（改为大端序）
        offset = obfuscated_data[ip] | (obfuscated_data[ip + 1] << 8)
        obfuscated_data[ip] = (offset >> 8) & 0xFF
        obfuscated_data[ip + 1] = offset & 0xFF
        ip += 2

        # 5. 处理匹配长度
        if match_length == 15:
            m, ip = read_long_length_no_check(obfuscated_data, ip)
            match_length += m
        match_length += 4  # MINMATCH

        # 6. 检查是否结束
        if ip >= len(obfuscated_data):
            break

    return bytes(obfuscated_data)


def encode_data1(compressed_data: bytes) -> bytes:
    ip = 0
    AK_LITERAL_LENGTH_MASK = ((1 << 4) - 1) & 0xFF
    AK_MATCH_LENGTH_MASK = (~AK_LITERAL_LENGTH_MASK) & 0xFF
    obfuscated_data = bytearray(compressed_data)

    while ip < len(obfuscated_data):
        # 1. 读取原始LZ4的控制字节
        literal_length = obfuscated_data[ip] >> 4  # 原始高4位
        match_length = obfuscated_data[ip] & AK_LITERAL_LENGTH_MASK  # 原始低4位

        # 2. 交换控制字节的位顺序
        obfuscated_data[ip] = (match_length << 4 | literal_length) & 0xFF
        ip += 1

        # 3. 处理字面量长度
        if literal_length == 15:
            l, ip = read_long_length_no_check(obfuscated_data, ip)
            literal_length += l
        ip += literal_length

        # 4. 处理偏移量（改为大端序）
        if ip + 1 < len(obfuscated_data):  # 确保有足够的字节
            offset = obfuscated_data[ip] | (obfuscated_data[ip + 1] << 8)
            obfuscated_data[ip] = (offset >> 8) & 0xFF
            obfuscated_data[ip + 1] = offset & 0xFF
            ip += 2

        # 5. 处理匹配长度
        if match_length == 15:
            m, ip = read_long_length_no_check(obfuscated_data, ip)
            match_length += m
        match_length += 4  # MINMATCH

    return bytes(obfuscated_data)

a = encode_data(b'\x01\x07\x00\x00\x00\x00\x00\x00\x70\x00')  # 这里的输入数据需要根据实际情况进行调整
b = decode_data(a, 10)
print(a)
print(b)