#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 Anthony Johnson
"""List the ACPI devices Windows enumerated, from an offline SYSTEM hive.

Usage: enum_acpi.py SYSTEM [PATTERN...]

SYSTEM is a copy of Windows/System32/config/SYSTEM from the machine's own
Windows install. Each PATTERN (case-insensitive substring of the device key,
e.g. MSHW0472 or DEV_55F0) limits the output to matching devices. For every
instance it prints the description, hardware and compatible IDs, the service
(driver) and the location. The control set is the one SYSTEM\\Select\\Current
names.

Needs regipy (https://github.com/mkorman90/regipy), for example in a venv:
  python3 -m venv ~/.venvs/regipy && ~/.venvs/regipy/bin/pip install regipy
See docs/windows-re.md.
"""
import sys

FIELDS = ('DeviceDesc', 'FriendlyName', 'HardwareID', 'CompatibleIDs', 'Service',
          'Driver', 'LocationInformation')


def current_control_set(hive):
    try:
        cur = hive.get_key('\\Select').get_value('Current')
        return 'ControlSet%03d' % int(cur)
    except Exception:
        return 'ControlSet001'


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        sys.exit(__doc__.strip())
    try:
        from regipy.registry import RegistryHive
    except ImportError:
        sys.exit('enum_acpi.py needs regipy: pip install regipy (in a venv)')
    hive = RegistryHive(sys.argv[1])
    cs = current_control_set(hive)
    base = hive.get_key('\\%s\\Enum\\ACPI' % cs)
    pat = [p.upper() for p in sys.argv[2:]]
    for dev in base.iter_subkeys():
        if pat and not any(p in dev.name.upper() for p in pat):
            continue
        for inst in dev.iter_subkeys():
            vals = {v.name: v.value for v in inst.iter_values()}
            print('== %s\\%s' % (dev.name, inst.name))
            for k in FIELDS:
                if k in vals:
                    print('   %s: %s' % (k, vals[k]))


if __name__ == '__main__':
    main()
