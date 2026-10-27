# Firmware

Every firmware file the tested Surface Laptop 7 (13.8", X1E80100 platform) loads on Linux,
where it comes from, and where it goes. This repo ships none of them. Files from
linux-firmware are listed with the upstream commit and tag; files from Windows have to be
copied from your own Windows installation. The SHA-256 sums are of the files installed on the
tested machine, so you can check that you have the same ones.

"7.3" means the [7.3.0-sl7 kernel](kernel-7.3.md); "7.0" means the older 7.0.0-rc4 kernel
this machine ran before it. The device-tree paths are the same on both, except that 7.0's
device tree has the video codec disabled.

## Summary

| File (under `/lib/firmware/`) | For | Source | Redistributable | Kernel |
|---|---|---|---|---|
| `qcom/x1e80100/microsoft/Romulus/qcadsp8380.mbn`, `adsp_dtbs.elf` | Audio DSP (ADSP): sound, battery and USB-C through pmic_glink | Windows | No | 7.0, 7.3 |
| `qcom/x1e80100/microsoft/Romulus/qccdsp8380.mbn`, `cdsp_dtbs.elf` | Compute DSP (CDSP) | Windows | No | 7.0, 7.3 |
| `qcom/x1e80100/X1E80100-Romulus-tplg.bin` | Sound card topology | linux-firmware | Yes | 7.0, 7.3 |
| `qcom/gen70500_sqe.fw`, `qcom/gen70500_gmu.bin` | GPU (Adreno X1-85) microcode and GMU | linux-firmware | Yes | 7.0, 7.3 |
| `qcom/x1e80100/microsoft/qcdxkmsuc8380.mbn` | GPU zap shader, Microsoft-signed | Windows | No | 7.0, 7.3 |
| `updates/qcom/x1e80100/microsoft/Romulus/qcvss8380.mbn` | Iris video codec | Windows | No | 7.3 only |
| `updates/7.3.0-sl7/ath12k/WCN7850/hw2.0/{amss,m3,board-2}.bin` | Wi-Fi, firmware `WLAN.HMT.1.1.c7-00108` | linux-firmware | Yes | 7.3 only |
| `ath12k/WCN7850/hw2.0/{amss,m3,board-2}.bin` | Wi-Fi, firmware `WLAN.HMT.1.0.c5-00481` | Debian `firmware-atheros` | Yes | 7.0 only |
| `qca/hmtbtfw20.tlv`, `qca/hmtnv20.bin` | Bluetooth (WCN7850) patch and NVM | linux-firmware | Yes | 7.0, 7.3 |
| `vd55g0-surface.bin` | IR sensor patch, optional fallback | Windows | No | 7.0, 7.3 |

## Audio and compute DSPs (from Windows)

| File | SHA-256 |
|---|---|
| `qcadsp8380.mbn` | `3a0240f9a1c0c43b657959b1bf10433a1a9793eb5c4af9f6beff8644c174f5a0` |
| `adsp_dtbs.elf` | `b03f066e2645dbe35a33a08a91312842f5cee3676cac3e111f1f3dabd1cf4e9e` |
| `qccdsp8380.mbn` | `3df4de099b23df0969c172fa2660e02c1ba4e1b5c280eb0198a89194f400d875` |
| `cdsp_dtbs.elf` | `664758a227f38043cb5fc21ad56154e57449a759e703d3b1d84b41c8ce138914` |

Installed in `/lib/firmware/qcom/x1e80100/microsoft/Romulus/`, the path the device tree's
`firmware-name` gives. They are signed for Microsoft's devices. The `qcom/x1e80100/adsp.mbn`
in linux-firmware is built for other X1E machines and was not tried here.

`qcom_q6v5_pas` starts both DSPs from the initramfs, before the root file system is mounted,
and does not retry. So the four files must also be in the initramfs, or the sound card never
registers. An initramfs-tools hook does that; extraction from Windows and the hook are in
[audio.md](audio.md).

The `.jsn` files that often sit next to them (`adspr.jsn`, `battmgr.jsn` and others) are for
the user-space `pd-mapper`. Both kernels use the in-kernel `qcom_pd_mapper` instead.

## Sound card topology (linux-firmware)

`qcom/x1e80100/X1E80100-Romulus-tplg.bin`, SHA-256
`aa303397750f883ecaeed874d7547da658500596247676a6d405bf1ec43290b5`. Last changed in
linux-firmware commit
[`bfc1d7433ddd`](https://gitlab.com/kernel-firmware/linux-firmware/-/commit/bfc1d7433ddd92302d2c59287a5c00477c8a8bd7)
(2026-01-10) and the same in tag `20261019`. Licence: LICENCE.linaro. Debian 13's
`firmware-qcom-soc` (20250410-2) does not have it, so on the tested machine it was copied in
by hand. See [audio.md](audio.md).

## GPU

| File | Source | SHA-256 |
|---|---|---|
| `qcom/gen70500_sqe.fw` | linux-firmware (Debian `firmware-qcom-soc` 20250410-2; the same blob as tag `20261019`) | `05ae89e6dea62268cec3f4abb5d7d6db2c95270ff105fd056f77262e39d2e527` |
| `qcom/gen70500_gmu.bin` | same; the kernel reports "GMU firmware v4.3.17" | `5dfba247d548cabcb892ffa716e8dc82a345fd54b5dbae46ba523230e7ae37dd` |
| `qcom/x1e80100/microsoft/qcdxkmsuc8380.mbn` | Windows, the GPU driver package (`qcdx8380.inf_arm64_*` in the DriverStore) | `f2f6dd1d7b2dc6e8019f85d9a17a16bb3bc3605fb0bebc632ec615c1b404b86b` |

The zap shader has to be the Microsoft-signed one; linux-firmware's
`qcom/x1e80100/gen70500_zap.mbn` is not used. Licence of the two linux-firmware files:
LICENSE.qcom.

The GPU firmware is not in the initramfs, so every boot logs three
`Direct firmware load for qcom/gen70500_sqe.fw failed with error -2` lines before the root file
system is mounted. The GPU starts a few seconds later. Harmless.

## Video codec (Iris, 7.3 only)

`qcvss8380.mbn`, SHA-256 `3ee65bc056f47a03ef9c5ac78e3cd8b2aa4f97f3827739c94445251c0b8d4f32`,
installed as `/lib/firmware/updates/qcom/x1e80100/microsoft/Romulus/qcvss8380.mbn`. It comes
from the same Windows GPU driver package as the zap shader (`qcdx8380.inf_arm64_e13ac55ddce2b10f`
on the tested machine). Kit patch 0019 enables the codec on 7.3 and points it at this file;
7.0's device tree leaves the codec disabled. The kit takes the same approach and does not
redistribute the file either.

## Wi-Fi (WCN7850)

The two kernels need different Wi-Fi firmware. On 7.3, the older `WLAN.HMT.1.0.c5-00481` boots
but every WMI command times out when the interface comes up. 7.3 works with the current
upstream `WLAN.HMT.1.1.c7-00108`. To give each kernel its own, the 7.3 files go in the
per-release directory `/lib/firmware/updates/<kver>/`, which the kernel searches first and only
that release sees. Remember to copy it for each new kernel release (see "After any kernel
update" in [kernel-7.3.md](kernel-7.3.md)). If you no longer run 7.0, you can install the
upstream files in `/lib/firmware/ath12k/WCN7850/hw2.0/` instead.

7.3: `/lib/firmware/updates/7.3.0-sl7/ath12k/WCN7850/hw2.0/`, from linux-firmware (licence
LICENSE.QualcommAtheros_ath10k, see `Notice.txt`). All three are as in tag `20261019`:

| File | Last changed upstream | SHA-256 |
|---|---|---|
| `amss.bin` | [`6fb33265`](https://gitlab.com/kernel-firmware/linux-firmware/-/commit/6fb33265936075ee1bb5a31786a4fe1b30fdd001) (2026-03-17, c7-00108) | `43aadfd3df887f27de74020273aee484bac6a31dd53068f91baf2a9b094d6a68` |
| `m3.bin` | same commit | `0e72f44df7defc269fe92dcea25d4d409046c04b77d41c510c52879b3dfc1055` |
| `board-2.bin` | [`575bbe3f`](https://gitlab.com/kernel-firmware/linux-firmware/-/commit/575bbe3f83565d18caa73e9b9458f754dd286f48) (2026-10-08) | `6a98237c743d864773a547e81e23f0c6dc721dcd7331926bee7381e2152e00fd` |
| `Notice.txt` | | `515bf4c9d620a87458e4447fe01a0e9bc384d1c3e0037cc4c3d2037b1ff25525` |

```sh
D=/lib/firmware/updates/7.3.0-sl7/ath12k/WCN7850/hw2.0
U=https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git/plain/ath12k/WCN7850/hw2.0
sudo mkdir -p "$D"
for f in amss.bin m3.bin board-2.bin Notice.txt; do sudo curl -fLo "$D/$f" "$U/$f?h=20261019"; done
sha256sum "$D"/*
```

On 7.3 the kernel then logs `fw_build_id QC_IMAGE_VERSION_STRING=WLAN.HMT.1.1.c7-00108-...`.

7.0: `/lib/firmware/ath12k/WCN7850/hw2.0/`. `amss.bin` and `m3.bin` are from Debian 13's
`firmware-atheros` 20250410-2, which still ships the 2023 `WLAN.HMT.1.0.c5-00481`. The
`board-2.bin` there differs from the package's; it was replaced by hand at some point.
SHA-256 for reference:
`amss.bin` `b15b21fd99baafd5dad81b6d6fa054df023363029821eb67dd674a438b9fd78d`, `m3.bin`
`97eca0829a1da06bfcb000863f585e2c64ee7febae29f4822097dea1986d919b`, `board-2.bin`
`196598d5841419574d99d56d2dd7453d492befb2d0c5a3174f16d310e85f8bb9`.

## Bluetooth (WCN7850)

From Debian 13's `firmware-atheros` 20250410-2, the same blobs as linux-firmware tag
`20261019`. Licence: LICENSE.qcom. The kernel reports `BTFW.HAMILTON.2.0.1-00349`.

| File | SHA-256 |
|---|---|
| `qca/hmtbtfw20.tlv` | `f1c00f4640a5c4e5dc36a2574d3d1d0afcfd1ab58a84f217dce4b1bb73cba981` |
| `qca/hmtnv20.bin` | `c26b340bbc8b617304610c774627ac4879194705eea7a7c7b13e3593903befd9` |

## IR camera sensor patch (optional)

`/lib/firmware/vd55g0-surface.bin`, 552 bytes, SHA-256
`5c07088c8871792e48a3d75d5b9af1cb3725739b8d6aaed229be6f7c0126b321`. The Windows sensor patch
for the VD55G0. The driver normally uses ST's own patch, which is built into it, and this
sensor (revision `0x1111`) accepts that. The Windows file is only a fallback for unknown sensor
revisions, or with `vd55g0.fw_patch=1`. See [ir-camera.md](ir-camera.md).

## What needs no firmware file

The display controller, the camera subsystem (CAMSS), the touchpad and touchscreen, and the
audio codecs and speaker amplifiers load no firmware on this machine. USB-C and the battery
run through the ADSP.

## Checking what loaded

```sh
sudo dmesg | grep -E 'remoteproc.*Booting fw|fw_build_id|QCA Downloading|GMU firmware'
for f in $(find /proc/device-tree/ -name firmware-name); do
	printf '%s: ' "${f#/proc/device-tree/}"; tr '\0' ' ' < "$f"; echo
done
```
