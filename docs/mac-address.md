# Wi-Fi and Bluetooth MAC addresses

The Surface Laptop 7's Wi-Fi and Bluetooth chip (Qualcomm WCN7850) has no addresses burned
in. On Linux, without help (as described by sl7-mac, below):

- **Wi-Fi:** `ath12k` makes up a random address in Qualcomm's `00:03:7f` range at every boot.
  DHCP reservations, router allow-lists and anything else keyed on the address break.
- **Bluetooth:** the controller comes up *unconfigured*, with no public address. BlueZ does
  not use it until someone sets one. The kernel log on this machine says
  `hci0: unconfigured, needs address`.

The factory addresses do exist. The Surface firmware gives each machine one base address in
Microsoft's range and uses three consecutive addresses:

| Address | Used for |
|---|---|
| base + 0 | Wi-Fi |
| base + 1 | Bluetooth |
| base + 2 | Ethernet pass-through (Surface docks and adapters) |

The UEFI variable `MacAddressEmulationAddress` (under a vendor GUID, so it appears as
`/sys/firmware/efi/efivars/MacAddressEmulationAddress-*`) holds base + 2: 4 bytes of efivarfs
attributes, then the 6-byte address. From that, the other two follow.

## sl7-mac

[sl7-mac](https://github.com/valeronm/sl7-mac) by valeronm (Valeriy Mironov), MIT license,
applies these addresses at boot. This repo only links to it. Install it from the project's
release `.deb`, or build the package from the repository (`dpkg-buildpackage -us -uc -b`). Its
only runtime dependency is `python3`.

How it works (read from the version installed here):

- `sl7-mac wifi|bt|eth|all` prints the derived addresses. `sl7-mac status` shows the units, the
  staged link file, and whether the live addresses match.
- It checks the base address before using it: not all zeros, not broadcast, not multicast, and
  large enough that subtracting 2 stays inside the vendor range.
- If the UEFI variable is missing, `ETH_MAC=` in `/etc/default/sl7-mac` supplies base + 2
  by hand.
- **`sl7-wifi-mac.service`** runs early in boot (`DefaultDependencies=no`,
  `Before=systemd-udev-trigger.service sysinit.target`, wanted by `sysinit.target`). It calls
  `sl7-mac write-link`, which writes `/run/systemd/network/05-sl7-wifi-mac.link`: match
  `Type=wlan` and `Driver=ath12k*`, set `MACAddress=` to base + 0. udev applies it when the
  Wi-Fi interface appears.
- **`sl7-bt-mac.service`** is started by the udev rule `99-sl7-bt-mac.rules` when `hci0` is
  added (`TAG+="systemd"`, `ENV{SYSTEMD_WANTS}`), ordered before `bluetooth.service`. It calls
  `sl7-mac apply-bt`, which runs a small helper (`/usr/lib/sl7-mac/mgmt-set-addr.py`). The
  helper sets the public address through the BlueZ management socket ("Set Public Address").
  Unlike `btmgmt` it needs no terminal. It waits while the kernel is still loading the
  controller's firmware, and it handles a controller that is still unconfigured.
- Both units run only if the UEFI variable or `/etc/default/sl7-mac` exists, and both are
  sandboxed (`ProtectSystem=strict`, no new privileges, a small capability set).
- Base + 2 is printed but not applied: nothing on Linux uses it.

## On this machine

In use on the 13.8" model since August 2026 (7.0 kernel). On 7.3.0-sl7 (2026-10-27) the
Wi-Fi address matches the derived one (`addr_assign_type` 3, set by userspace), and
`sl7-bt-mac.service` logged `hci0: public address set to ...` at boot. On 7.3 the Wi-Fi driver
is named `ath12k_wifi7_pci`, which `Driver=ath12k*` still matches.

Notes from this install:

- **The man page is missing.** sl7-mac was installed by hand, not from the `.deb`, so the
  upstream `sl7-mac.1` was never installed. `man sl7-mac`, the "See sl7-mac(1)" line in
  `sl7-mac --help`, and `Documentation=man:sl7-mac(1)` in `sl7-bt-mac.service` point nowhere.
  This is minor. Installing the `.deb` fixes it.
- **Duplicate units.** Copies of both units and the udev rule were also put in
  `/etc/systemd/system/` and `/etc/udev/rules.d/`. Copies in `/etc` take precedence over
  `/usr/lib`, so an sl7-mac upgrade would not take effect until they are removed. Install it
  in one place only.
- **A persistent link file.** On this install the runtime link file in `/run` lost a race at
  boot: the note written at the time says `ath12k` probed before the generator had finished.
  So a copy was saved as `/etc/systemd/network/05-sl7-wifi-mac.link`, which takes precedence
  over the `/run` copy. initramfs-tools also copies it into the initramfs. That
  file holds the machine's real address: never publish it, and update it if the board is
  replaced. The race has not been re-tested on 7.3. A likely cause is that
  `Before=systemd-udev-trigger.service` orders the unit only against the coldplug trigger,
  not against uevents udev handles before it (for example a PCIe link that comes up while
  udev is already running). This is a guess, not verified.

Never post the output of `sl7-mac all`, `sl7-mac status`, `ip link` or `bluetoothctl show`
without masking the addresses.
