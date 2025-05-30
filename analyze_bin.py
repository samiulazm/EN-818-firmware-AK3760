#!/usr/bin/env python3
import struct
import os

def analyze_binary(filename):
    print(f"Analyzing {filename}...")
    
    if not os.path.exists(filename):
        print(f"File {filename} not found!")
        return
    
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data)} bytes ({len(data) / (1024*1024):.2f} MB)")
    
    # Show first 128 bytes in hex
    print("\nFirst 128 bytes (hex):")
    for i in range(0, min(128, len(data)), 16):
        hex_part = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data[i:i+16])
        print(f"{i:08x}: {hex_part:<48} |{ascii_part}|")
    
    # Check for common file signatures
    print("\nFile signature analysis:")
    if len(data) >= 4:
        header = data[:4]
        if header == b'\x7fELF':
            print("- ELF executable/library")
        elif header[:2] == b'MZ':
            print("- PE/DOS executable")
        elif header == b'\x89PNG':
            print("- PNG image")
        elif header[:3] == b'GIF':
            print("- GIF image")
        elif header[:2] == b'\xff\xd8':
            print("- JPEG image")
        elif header == b'RIFF':
            print("- RIFF container (possibly AVI/WAV)")
        elif header[:4] == b'\x00\x00\x00\x14' or header[:4] == b'\x00\x00\x00\x18':
            print("- Possible MP4/MOV video")
        elif header[:4] == b'ftyp':
            print("- MP4/MOV video")
        else:
            print(f"- Unknown format, header: {header.hex()}")
    
    # Look for readable strings
    strings = []
    current_string = b''
    for byte in data[:1024]:  # Check first 1KB for strings
        if 32 <= byte <= 126:  # Printable ASCII
            current_string += bytes([byte])
        else:
            if len(current_string) >= 4:
                try:
                    strings.append(current_string.decode('ascii'))
                except:
                    pass
            current_string = b''
    
    if strings:
        print(f"\nFound {len(strings)} readable strings in first 1KB:")
        for s in strings[:10]:  # Show first 10
            print(f"  '{s}'")
    else:
        print("\nNo readable strings found in first 1KB")
    
    # Check entropy (randomness) of the data
    byte_counts = [0] * 256
    for byte in data[:10000]:  # Sample first 10KB
        byte_counts[byte] += 1
    
    entropy = 0
    total = sum(byte_counts)
    if total > 0:
        for count in byte_counts:
            if count > 0:
                p = count / total
                entropy -= p * (p.bit_length() - 1) if p > 0 else 0
    
    print(f"\nEntropy (first 10KB): {entropy:.2f} (0=ordered, 8=random)")
    if entropy > 7:
        print("- High entropy: possibly encrypted/compressed data")
    elif entropy < 2:
        print("- Low entropy: possibly contains patterns or repeated data")
    else:
        print("- Medium entropy: typical for executable or structured data")

if __name__ == "__main__":
    analyze_binary("a60.bin")
