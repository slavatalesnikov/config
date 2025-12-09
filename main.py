import sys
import re

def parse_register(token):
    if token.startswith('r') and token[1:].isdigit():
        return int(token[1:])
    else:
        raise ValueError(f"Invalid register: {token}")

def parse_memory_ref(expr):
    expr = expr.strip()
    if not (expr.startswith('[') and expr.endswith(']')):
        raise ValueError(f"Invalid memory reference: {expr}")
    inner = expr[1:-1].strip()
    if '+' in inner:
        parts = inner.split('+')
        if len(parts) != 2:
            raise ValueError(f"Invalid memory expression: {expr}")
        base, offset = parts[0].strip(), parts[1].strip()
        base_reg = parse_register(base)
        offset_val = int(offset)
        return base_reg, offset_val
    else:
        reg = parse_register(inner)
        return reg, 0

def parse_line(line):
    line = line.strip()
    if not line or line.startswith('#'):
        return None

    if line.startswith('load '):
        m = re.match(r'load\s+(r\d+)\s*=\s*(\d+)', line)
        if not m:
            raise ValueError(f"Invalid load syntax: {line}")
        reg = parse_register(m.group(1))
        const = int(m.group(2))
        return ('load', {'A': 49, 'B': reg, 'C': const})

    elif line.startswith('read '):
        m = re.match(r'read\s+(r\d+)\s*=\s*(\[[^\]]+\])', line)
        if not m:
            raise ValueError(f"Invalid read syntax: {line}")
        dst_reg = parse_register(m.group(1))
        base_reg, offset = parse_memory_ref(m.group(2))
        return ('read', {'A': 37, 'B': base_reg, 'C': offset, 'D': dst_reg})

    elif line.startswith('write '):
        m = re.match(r'write\s*(\[[^\]]+\])\s*=\s*(r\d+)', line)
        if not m:
            raise ValueError(f"Invalid write syntax: {line}")
        base_reg, offset = parse_memory_ref(m.group(1))
        src_reg = parse_register(m.group(2))
        return ('write', {'A': 11, 'B': offset, 'C': src_reg, 'D': base_reg})

    elif line.startswith('sgn '):
        m = re.match(r'sgn\s*(\[[^\]]+\])\s*->\s*(\[[^\]]+\])', line)
        if not m:
            raise ValueError(f"Invalid sgn syntax: {line}")
        src_addr, _ = parse_memory_ref(m.group(1))
        dst_addr, _ = parse_memory_ref(m.group(2))
        return ('sgn', {'A': 63, 'B': dst_addr, 'C': src_addr})

    else:
        raise ValueError(f"Unknown command: {line}")
def encode_load(A, B, C):
    # A: 6 бит (0-5), B: 7 бит (6-12), C: 28 бит (13-40)  6 байт = 48 бит
    value = (C << 13) | (B << 6) | A
    return value.to_bytes(6, byteorder='little')

def encode_read(A, B, C, D):
    # A:6 (0-5), B:7 (6-12), C:6 (13-18), D:7 (19-25) 4 байта = 32 бит
    value = (D << 19) | (C << 13) | (B << 6) | A
    return value.to_bytes(4, byteorder='little')

def encode_write(A, B, C, D):
    # A:6 (0-5), B:6 (6-11), C:7 (12-18), D:7 (19-25) 4 байта = 32 бит
    value = (D << 19) | (C << 12) | (B << 6) | A
    return value.to_bytes(4, byteorder='little')

def encode_sgn(A, B, C):
    # A:6 (0-5), B:26 (6-31), C:26 (32-57)  8 байт = 64 бит
    value = (C << 32) | (B << 6) | A
    return value.to_bytes(8, byteorder='little')

def encode_instruction(op, fields):
    if op == 'load':
        return encode_load(fields['A'], fields['B'], fields['C'])
    elif op == 'read':
        return encode_read(fields['A'], fields['B'], fields['C'], fields['D'])
    elif op == 'write':
        return encode_write(fields['A'], fields['B'], fields['C'], fields['D'])
    elif op == 'sgn':
        return encode_sgn(fields['A'], fields['B'], fields['C'])
    else:
        raise ValueError(f"Unknown operation: {op}")

def bytes_to_hex_str(b):
    return ", ".join(f"0x{byte:02X}" for byte in b)

def main():
    if len(sys.argv) < 4:
        print("python3 main.py <input.asm> <output.bin> [--test]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    test_mode = (len(sys.argv) >= 4 and sys.argv[3] == '--test')

    program = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                instr = parse_line(line)
                if instr:
                    program.append(instr)
            except ValueError as e:
                print(f"Error on line {line_num}: {e}", file=sys.stderr)
                sys.exit(1)

    #кодируем в байты
    binary_data = b''
    for op, fields in program:
        binary_data += encode_instruction(op, fields)
    #записываем в файл
    with open(output_path, 'wb') as f:
        f.write(binary_data)
    #размер файла
    total_size = len(binary_data)
    print(total_size)
    if test_mode:
        
        offset = 0 #Для каждой команды отдельно
        for op, fields in program:
            size = {'load': 6, 'read': 4, 'write': 4, 'sgn': 8}[op]
            chunk = binary_data[offset:offset + size]
            print(bytes_to_hex_str(chunk))
            offset += size

if __name__ == '__main__':
    main()