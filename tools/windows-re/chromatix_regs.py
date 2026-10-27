#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 Anthony Johnson
"""Decode the register settings in a Qualcomm Chromatix sensor module (.bin).

Usage: chromatix_regs.py [--patch OUT [--patch-addr ADDR]] SENSORMODULE.bin

Prints every regSetting block of the module (power-up/init sequence, mode
settings, gain tables), one register access per line:

  ADDR OP aN dN DATA [delay=Nus] [slave=...]

OP is W (write), WB (burst write), WS (sequential write), R (read) or POLL;
aN/dN are the address and data widths in bytes. The layout is the CamX
parameter parser one (see schema.py): each regSetting record is ten u32
(slave-address present, slave-address field, register address, count, data
field, address type, data type, operation, delay present, delay field).

--patch OUT writes the bytes of the first contiguous run of 1-byte writes that
starts at ADDR (default 0x2000) to OUT. For the ST VD55G0 module that run is
the sensor firmware patch the Windows driver loads, which the patched Linux
vd55g0 driver can load as vd55g0-surface.bin. See docs/windows-re.md and
docs/ir-camera.md.
"""
import argparse
import hashlib
import struct
import sys

HEADER = 0xa8
ROW = 56
RECORD = 40
OPS = {0: 'W', 1: 'WB', 2: 'WS', 3: 'R', 4: 'POLL'}


class Module:
    def __init__(self, data):
        self.b = data
        _, sch_off, sch_len, _, self.dat_off, _ = struct.unpack_from('<6I', data, HEADER)
        self.schema = {}
        self.order = []
        for off in range(sch_off, sch_off + sch_len - ROW + 1, ROW):
            fid = struct.unpack_from('<I', data, off)[0]
            name = data[off + 4:off + 36].split(b'\0')[0].decode('ascii', 'replace')
            f = struct.unpack_from('<5i', data, off + 36)
            self.schema[fid] = (name, f[3], f[4])
            self.order.append(fid)

    def val(self, fid):
        _, o, sz = self.schema[fid]
        raw = self.b[self.dat_off + o:self.dat_off + o + sz]
        return [int.from_bytes(raw[i:i + 4], 'little') for i in range(0, len(raw), 4)]

    def blocks(self):
        """Yield (field id, parent name, records) for each regSetting field."""
        parent = None
        for fid in self.order:
            name, o, sz = self.schema[fid]
            if name != 'regSetting':
                if sz and name not in ('slaveAddr', 'registerData', 'delayUs'):
                    parent = name
                continue
            base = self.dat_off + o
            recs = [struct.unpack_from('<10I', self.b, base + RECORD * r)
                    for r in range(sz // RECORD)]
            yield fid, parent, recs


def dump(m):
    for fid, parent, recs in m.blocks():
        print('### regSetting id=%d under %s: %d records' % (fid, parent, len(recs)))
        for sa_ex, sa_id, addr, cnt, data_id, atype, dtype, op, dl_ex, dl_id in recs:
            data = m.val(data_id)
            delay = m.val(dl_id) if dl_ex else []
            delay = delay[0] if delay else 0
            sa = ' slave=%s' % m.val(sa_id) if sa_ex else ''
            print('%04x %s a%d d%d %s%s%s' % (addr, OPS.get(op, op), atype, dtype,
                  ' '.join('%x' % d for d in data[:max(cnt, 1)]),
                  (' delay=%dus' % delay) if delay else '', sa))


def extract_patch(m, start):
    out = bytearray()
    for _, _, recs in m.blocks():
        nxt = None
        for _, _, addr, cnt, data_id, _, dtype, op, _, _ in recs:
            if nxt is None and addr != start:
                continue
            if addr != (start if nxt is None else nxt) or op not in (0, 1, 2) or dtype != 1:
                break
            vals = m.val(data_id)[:max(cnt, 1)]
            out += bytes(v & 0xff for v in vals)
            nxt = addr + len(vals)
        if out:
            return bytes(out)
    return b''


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('module', help='sensor module .bin from the driver store')
    ap.add_argument('--patch', metavar='OUT', help='write the firmware patch bytes to OUT')
    ap.add_argument('--patch-addr', metavar='ADDR', default='0x2000',
                    type=lambda s: int(s, 0), help='patch start address (default 0x2000)')
    args = ap.parse_args()
    with open(args.module, 'rb') as f:
        m = Module(f.read())
    if not args.patch:
        dump(m)
        return
    patch = extract_patch(m, args.patch_addr)
    if not patch:
        sys.exit('no byte writes starting at 0x%04x' % args.patch_addr)
    with open(args.patch, 'wb') as f:
        f.write(patch)
    print('wrote %d bytes (0x%04x-0x%04x) to %s, sha256 %s' % (
        len(patch), args.patch_addr, args.patch_addr + len(patch) - 1, args.patch,
        hashlib.sha256(patch).hexdigest()))


if __name__ == '__main__':
    main()
