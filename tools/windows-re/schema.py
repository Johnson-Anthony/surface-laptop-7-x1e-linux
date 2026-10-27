#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 Anthony Johnson
"""List the schema of a Qualcomm Chromatix sensor module (.bin).

Usage: schema.py com.<vendor>.sensormodule.<name>.bin

Camera sensor modules in a Windows-on-Snapdragon driver store (CamX parameter
parser layout, seen with version 3.4) carry a schema table and a data section.
The header at 0xa8 holds six u32: ?, schema offset, schema length, ?, data
offset, data length. Each schema row is 56 bytes: u32 field id, a 32-byte
NUL-padded field name, then five s32; the last two are the field's offset into
the data section and its size in bytes. This prints one line per row:
file offset, id, name and the five numbers. chromatix_regs.py uses the same
table to decode the register settings. See docs/windows-re.md.
"""
import struct
import sys

HEADER = 0xa8
ROW = 56


def main():
    if len(sys.argv) != 2 or sys.argv[1] in ('-h', '--help'):
        sys.exit(__doc__.strip())
    with open(sys.argv[1], 'rb') as f:
        b = f.read()
    sch_off, sch_len = struct.unpack_from('<II', b, HEADER + 4)
    off, end = sch_off, min(sch_off + sch_len, len(b))
    n = 0
    while off + ROW <= end:
        fid = struct.unpack_from('<I', b, off)[0]
        name = b[off + 4:off + 36].split(b'\0')[0].decode('ascii', 'replace')
        f = struct.unpack_from('<5i', b, off + 36)
        print('%05x id=%-4d %-36s %s' % (off, fid, name, ' '.join('%6d' % x for x in f)))
        off += ROW
        n += 1
    print('# entries', n, 'leftover', end - off)


if __name__ == '__main__':
    main()
