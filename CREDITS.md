# Credits

This repo builds on a lot of other people's work. Each piece is also credited where it is used.

## Kernel and board support

- **ItsLucas**, [surface-laptop-7-ubuntu-kernel](https://github.com/ItsLucas/surface-laptop-7-ubuntu-kernel):
  the Surface Laptop 7 patch kit the 7.3 kernel is built from. It adds the touchpad,
  touchscreen, cameras and SPI HID fixes to the `romulus15` device tree, and diagnosed the
  embedded-controller "posture events" gate behind the dead touchpad
  ([004e91d](https://github.com/ItsLucas/surface-laptop-7-ubuntu-kernel/commit/004e91d), fixed by
  its patch 0020). The kit's
  [PROVENANCE.md](https://github.com/ItsLucas/surface-laptop-7-ubuntu-kernel/blob/2ce3083fa76855225465f809760dc7185c74a80c/PROVENANCE.md)
  credits the upstream authors of its patches, among them: the Microsoft SPI HID driver,
  [bryce-hoehn/linux-surface-laptop-7](https://github.com/bryce-hoehn/linux-surface-laptop-7)
  (ath12k rfkill workaround), [dwhinham/linux-sp11](https://github.com/dwhinham/linux-sp11)
  (DisplayPort audio and Iris device-tree shape), Oliver White's Romulus camera series,
  Jens Glathe's [PS883x series](https://patchwork.kernel.org/series/1171308/) and
  Bartosz Golaszewski's [QCE series](https://patchwork.kernel.org/series/1191131/).
- **murkurie** and **ProgrammerIn-wonderland**, [ELLX-Kernel](https://github.com/murkurie/ELLX-Kernel):
  the 7.0 kernel this laptop first ran Linux on.
- The **Ubuntu kernel team**, for the [linux 7.3.0-9.9](https://launchpad.net/ubuntu/+source/linux/7.3.0-9.9)
  source the kernel starts from.
- Upstream **Linux** Qualcomm X1E work, in particular the system idle-state commit
  [95f827ceb21e](https://git.kernel.org/torvalds/c/95f827ceb21e), and the PDC wakeup series by
  **Mukesh Ojha** and **Maulik Shah**
  ([v4](https://lore.kernel.org/all/20260707-hamoa_pdc_v3-v4-0-dfd1f4a3ae89%40oss.qualcomm.com/)).
- **linux-surface**, for community tracking
  ([issue 1590](https://github.com/linux-surface/linux-surface/issues/1590)),
  [acpidumps](https://github.com/linux-surface/acpidumps) and
  [iptsd](https://github.com/linux-surface/iptsd).
- **aarch64-laptops**, [build](https://github.com/aarch64-laptops/build): DSDT dumps and
  bring-up notes for Snapdragon laptops.

## Deep sleep

- **justririll**, [x1e-sleep](https://github.com/justririll/x1e-sleep): the `qcom_adsp_pwr_lmts`
  module, used unmodified, which cut ADSP wakeups during suspend.
- **TravMurav**, [slbounce](https://github.com/TravMurav/slbounce), and
  [sp11-el2](https://github.com/ramonjesusmiranda-debug/sp11-el2): the EL2 research route
  (studied, not needed in the end).

## IR camera and face unlock

- **STMicroelectronics**, [vd55g0-linux-driver](https://github.com/STMicroelectronics/vd55g0-linux-driver):
  the sensor driver this repo patches.
- **petm5**, [vd55g-firmware](https://github.com/petm5/vd55g-firmware): packaging of ST's
  VD55G firmware patch.
- **Peter Marshall**, for the upstream VD55G0 support series for the `vd55g1` driver.
- **boltgolt**, [Howdy](https://github.com/boltgolt/howdy): the face-unlock framework this repo
  adds a camera reader to.
- [regipy](https://github.com/mkorman90/regipy) and [dlib](https://github.com/davisking/dlib),
  used by the decoders and by Howdy.

## Audio and networking

- **Val Packett** and **Srinivas Kandagatla**, [alsa-ucm-conf](https://github.com/alsa-project/alsa-ucm-conf):
  the upstream UCM configuration the audio overrides derive from.
- [qcom-firmware-extract](https://tracker.debian.org/pkg/qcom-firmware-extract): getting the
  DSP firmware from a Windows install.
- [linux-firmware](https://gitlab.com/kernel-firmware/linux-firmware): Wi-Fi firmware and the
  audio topology.
- **Valeriy Mironov**, [sl7-mac](https://github.com/valeronm/sl7-mac): factory Wi-Fi and Bluetooth
  MAC addresses.

## Tools

The work itself was done with [Claude Code](https://claude.com/claude-code); see
[docs/agentic-workflow.md](docs/agentic-workflow.md) for how.
