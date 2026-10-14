#!/usr/bin/env python3
"""
EN-818 / AK3760 boot logo converter + patcher
============================================

Converts a PNG into the exact boot-logo format used by the ANYKA A60
bootloader and patches it into `a60.bin`.

Boot logo format (reverse-engineered from a60.bin):
  - Stored in a fixed 64 KB slot at offset 0x10EA00 (partition "LOGO").
  - LZMA compressed (FORMAT_ALONE / .lzma), 0xFF padding fills the slot.
  - Decompresses to a BMP: 240x320, 16-bit RGB565, BI_BITFIELDS,
    bottom-up row order, white background.

Burn-info table (inside the bootloader):
  - 0x7824 : compressed size (uint32 LE)
  - 0x782C : offset in 256-byte sectors (uint32 LE, stays 0x10EA)

Usage:
  python convert_boot_logo.py <input.png> [firmware.bin] [--out output.bin]
                              [--mode fit|stretch] [--bg RRGGBB]
"""

import argparse
import struct
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required:  pip install Pillow")

# ---- Firmware layout constants (verified) ----
LOGO_OFFSET = 0x10EA00          # start of the 64 KB logo slot
LOGO_SLOT   = 0x10000           # 64 KB
SIZE_FIELD  = 0x7824            # burn-info compressed-size field
OFFSET_FIELD = 0x782C           # burn-info offset field (256-byte sectors)

# ---- Target logo geometry ----
W = 240
H = 320
BPP = 16
OFFBITS = 70                    # 14 (file hdr) + 56 (DIB w/ bitfields)

# RGB565 masks (BI_BITFIELDS, little-endian order in DIB)
R_MASK = 0xF800
G_MASK = 0x07E0
B_MASK = 0x001F


def rgb565(r, g, b):
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


def parse_bg(s):
    s = s.lstrip('#')
    if len(s) == 6:
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
    raise argparse.ArgumentTypeError("background must be RRGGBB hex")


def build_bmp(img: Image.Image, bg=(255, 255, 255)) -> bytes:
    """Render a 240x320 RGB565 bottom-up BMP (BI_BITFIELDS)."""
    # Composite onto solid background so alpha is handled correctly
    base = Image.new('RGB', img.size, bg)
    if img.mode in ('RGBA', 'LA'):
        base.paste(img.convert('RGBA'), (0, 0), img.convert('RGBA'))
    else:
        base = img.convert('RGB')

    canvas = Image.new('RGB', (W, H), bg)
    # center the (possibly letterboxed) image on the 240x320 canvas
    ox = (W - base.width) // 2
    oy = (H - base.height) // 2
    canvas.paste(base, (ox, oy))

    # Build pixel buffer in top-down order
    pixels = bytearray()
    for y in range(H):
        for x in range(W):
            r, g, b = canvas.getpixel((x, y))
            pixels += struct.pack('<H', rgb565(r, g, b))

    # BMP stores rows bottom-to-top for positive height
    row_bytes = W * (BPP // 8)
    rows = [pixels[i:i + row_bytes] for i in range(0, len(pixels), row_bytes)]
    pixel_data = b''.join(reversed(rows))

    size_image = len(pixel_data) + 2  # original biSizeImage = 153602 (pixels + 2 pad)
    file_size = OFFBITS + size_image   # original bfSize = 153672

    # BITMAPFILEHEADER (14 bytes)
    bmp = b'BM'
    bmp += struct.pack('<I', file_size)
    bmp += struct.pack('<HH', 0, 0)
    bmp += struct.pack('<I', OFFBITS)

    # DIB header, 56 bytes (BITMAPINFOHEADER + 3 masks + 4 pad)
    bmp += struct.pack('<IiiHHIIiiII', 56, W, H, 1, BPP, 3, size_image,
                       3937, 3937, 0, 0)
    bmp += struct.pack('<III', R_MASK, G_MASK, B_MASK)
    bmp += b'\x00' * 4

    bmp += pixel_data
    bmp += b'\x00\x00'  # trailing padding, matches original logo
    assert len(bmp) == file_size, (len(bmp), file_size)
    return bmp


def main():
    ap = argparse.ArgumentParser(description="Patch EN-818/AK3760 boot logo")
    ap.add_argument('input', help="Input PNG image")
    ap.add_argument('firmware', nargs='?', default='a60.bin',
                    help="Firmware to patch (default: a60.bin)")
    ap.add_argument('--out', default=None,
                    help="Output firmware path (default: <firmware>_modified.bin)")
    ap.add_argument('--mode', choices=['fit', 'stretch'], default='fit',
                    help="fit = letterbox preserving aspect (default); stretch = fill")
    ap.add_argument('--bg', type=parse_bg, default=(255, 255, 255),
                    help="Letterbox background RRGGBB (default: FFFFFF)")
    ap.add_argument('--rotate', type=int, choices=[0, 90, 180, 270], default=0,
                    help="Rotate the source image before scaling (default: 0)")
    args = ap.parse_args()

    fw_path = Path(args.firmware)
    if not fw_path.exists():
        sys.exit(f"Firmware not found: {fw_path}")
    fw = bytearray(fw_path.read_bytes())

    if len(fw) <= LOGO_OFFSET + LOGO_SLOT:
        sys.exit("Firmware too small to contain the LOGO slot")

    # 1. Load + scale the PNG
    img = Image.open(args.input)
    img = img.convert('RGBA')
    if args.rotate:
        img = img.rotate(args.rotate, expand=True)
    if args.mode == 'fit':
        ratio = min(W / img.width, H / img.height)
        nw, nh = round(img.width * ratio), round(img.height * ratio)
        img = img.resize((nw, nh), Image.LANCZOS)
    else:
        img = img.resize((W, H), Image.LANCZOS)

    # 2. Build the BMP
    bmp = build_bmp(img, args.bg)
    print(f"BMP: {len(bmp)} bytes ({W}x{H} RGB565)")

    # 3. LZMA compress (FORMAT_ALONE) -- matches bootloader's decoder
    import lzma
    comp = lzma.compress(bmp, format=lzma.FORMAT_ALONE, preset=6)
    print(f"LZMA: {len(comp)} bytes (was 10497)")

    if len(comp) > LOGO_SLOT - 4:
        sys.exit("Compressed logo exceeds 64 KB slot -- try a simpler image")

    # 4. Patch the logo slot (0xFF pad, same erase-style fill as original)
    slot = bytearray(b'\xff' * LOGO_SLOT)
    slot[:len(comp)] = comp
    fw[LOGO_OFFSET:LOGO_OFFSET + LOGO_SLOT] = slot

    # 5. Update burn-info size field; offset field unchanged
    struct.pack_into('<I', fw, SIZE_FIELD, len(comp))
    struct.pack_into('<I', fw, OFFSET_FIELD, LOGO_OFFSET // 256)
    print(f"Patched size field @ 0x{SIZE_FIELD:X} -> {len(comp)}")

    # 6. Write output (keep original untouched)
    out = Path(args.out) if args.out else fw_path.with_name(
        fw_path.stem + '_modified' + fw_path.suffix)
    out.write_bytes(fw)
    print(f"Wrote: {out}")

    # 7. Save intermediate/preview artifacts
    Path('_new_logo.bmp').write_bytes(bmp)
    Image.open('_new_logo.bmp').convert('RGB').save('_new_logo_preview.png')
    print("Artifacts: _new_logo.bmp, _new_logo_preview.png")


if __name__ == '__main__':
    main()
