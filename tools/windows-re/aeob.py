#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 Anthony Johnson
"""Pretty-print a Qualcomm 'AeoB' (ACPI extension object) resource file.

Usage: aeob.py FILE.bin

The camera drivers in a Windows-on-Snapdragon driver store ship board wiring
(GPIOs, regulators and their voltages, power-up order, delays) as AeoB files,
for example CAMI_RES_<subsystem>.bin and CAMP_RES_<subsystem>.bin. The format
is a 12-byte header ('AeoB', total size, 4 more bytes) followed by TLV items:
a little-endian u16 tag and u16 length, then the body. Tag 0 is an integer,
tag 1 a NUL-terminated string, tag 3 a package of nested items. Other tags are
printed as hex. See docs/windows-re.md.
"""
import struct
import sys


def parse(buf, off, end):
    items = []
    while off + 4 <= end:
        tag, ln = struct.unpack_from('<HH', buf, off)
        off += 4
        body = buf[off:off + ln]
        if tag == 0:
            items.append(int.from_bytes(body, 'little'))
        elif tag == 1:
            items.append(body.rstrip(b'\0').decode('ascii', 'replace'))
        elif tag == 3:
            items.append(parse(buf, off, off + ln))
        else:
            items.append(('tag%d' % tag, body.hex()))
        off += ln
    return items


def fmt(v):
    if isinstance(v, int):
        return str(v) if v < 4096 else '%d (0x%x)' % (v, v)
    return repr(v)


def show(x, ind=0):
    pad = '  ' * ind
    if isinstance(x, list):
        if all(not isinstance(i, list) for i in x) and len(repr(x)) < 110:
            print(pad + '{' + ', '.join(fmt(i) for i in x) + '}')
        else:
            print(pad + '{')
            for i in x:
                show(i, ind + 1)
            print(pad + '}')
    else:
        print(pad + fmt(x))


def main():
    if len(sys.argv) != 2 or sys.argv[1] in ('-h', '--help'):
        sys.exit(__doc__.strip())
    with open(sys.argv[1], 'rb') as f:
        buf = f.read()
    magic, size = struct.unpack_from('<4sI', buf, 0)
    if magic != b'AeoB':
        sys.exit('%s: not an AeoB file (magic %r)' % (sys.argv[1], magic))
    print('# size', size, 'hdr', buf[8:12].hex())
    show(parse(buf, 12, min(size, len(buf))))


if __name__ == '__main__':
    main()
