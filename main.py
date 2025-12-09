import sys
import re

#проверяем,что строка начинается с r и остальное цифры
def parse_register(token):
    if token.startswith('r') and token[1:].isdigit():
        return int(token[1:])
    else:
        raise ValueError(f"Invalid register: {token}")

#yбираем квадратные скобки и разделяем по + и вызываем parse_register для регистра и конвертирует смещение в число
def parse_memory_ref(expr):
    expr = expr.strip()
    if not (expr.startswith('[') and expr.endswith(']')):
        raise ValueError(f"Invalid memory reference: {expr}")
    inner = expr[1:-1]
    inner = inner.strip()
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
        return reg, 0  # offset=0 но на самом деле sgn не использует offset

def parse_line(line): #Преобразовывaем одну строку ассемблера в промежуточное представление 
    line = line.strip()
    if not line or line.startswith('#'):
        return None

    if line.startswith('load '):
        # load r125 = 818
        m = re.match(r'load\s+(r\d+)\s*=\s*(\d+)', line)
        if not m:
            raise ValueError(f"Invalid load syntax: {line}")
        reg = parse_register(m.group(1))
        const = int(m.group(2))
        return ('load', {'A': 49, 'B': reg, 'C': const})

    elif line.startswith('read '):
        # read r124 = [r2 + 28]
        m = re.match(r'read\s+(r\d+)\s*=\s*(\[[^\]]+\])', line)
        if not m:
            raise ValueError(f"Invalid read syntax: {line}")
        dst_reg = parse_register(m.group(1))
        base_reg, offset = parse_memory_ref(m.group(2))
        return ('read', {'A': 37, 'B': base_reg, 'C': offset, 'D': dst_reg})

    elif line.startswith('write '):
        # write [r58 + 44] = r79
        m = re.match(r'write\s*(\[[^\]]+\])\s*=\s*(r\d+)', line)
        if not m:
            raise ValueError(f"Invalid write syntax: {line}")
        base_reg, offset = parse_memory_ref(m.group(1))
        src_reg = parse_register(m.group(2))
        return ('write', {'A': 11, 'B': offset, 'C': src_reg, 'D': base_reg})

    elif line.startswith('sgn '):
        # sgn [r161] -> [r346]
        m = re.match(r'sgn\s*(\[[^\]]+\])\s*->\s*(\[[^\]]+\])', line)
        if not m:
            raise ValueError(f"Invalid sgn syntax: {line}")
        src_addr, _ = parse_memory_ref(m.group(1))  # C
        dst_addr, _ = parse_memory_ref(m.group(2))  # B
        return ('sgn', {'A': 63, 'B': dst_addr, 'C': src_addr})

    else:
        raise ValueError(f"Неизвестная комманда: {line}")

#делаем из словаря строку
def format_fields(fields):
    parts = []
    for key in sorted(fields.keys()):
        parts.append(f"{key}={fields[key]}")
    return ", ".join(parts)

def main():
    if len(sys.argv) < 4:
        print("пишем: python3 main.py <input.asm> <output.bin> [--test]")
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


    if test_mode:
        for op, fields in program:
            print(format_fields(fields))

if __name__ == '__main__':
    main()