# `SERVER_MINIMAL` kernel profile — `sea`

Status: `BUILT_UNTESTED` kernel/modules at the Mission 007 checkpoint;
target `sea` DTB and boot integration remain `BLOCKED`.

The kernel checkpoint is frozen as
[`SEA_SERVER_MINIMAL_KERNEL_001`](../devices/xiaomi-sea/server-minimal/kernel-baseline.json).
The regression check is `python host-tools/verify_kernel_baseline.py`; it
compares source, toolchain, config fragment, patch hashes and preserved
artifact hashes/sizes without requiring ignored build outputs in CI.

The profile is now a reproducible external layer with a complete out-of-tree
kernel build. `VENDOR_REFERENCE` remains preserved and `BLOCKED`; its status is
not changed by this experiment.

## Product contract

`SERVER_MINIMAL` implements the reusable
[`TOPAZIO_SERVER_PROFILE`](../profiles/TOPAZIO_SERVER_PROFILE.json). The
server needs CPU/SMP, RAM, timers, interrupt handling, UFS/storage, USB,
Wi-Fi/networking, battery and charging, thermal protection, display,
touchscreen/input, filesystem and a console suitable for SSH bootstrap.

Bluetooth, microSD, hardware watchdog and RTC remain important. Cellular
modem/telephony, camera, audio, GPS/GNSS, NFC, FM, biometrics, vibration and
Android consumer features are initially optional. Optional does not mean
unsafe to remove without evidence; each removal remains tracked in the
[structured dependency graph](../devices/xiaomi-sea/server-minimal/manifests/dependency-graph.json).

## Dependency decisions

| Area | Config/source evidence | DT/firmware boundary | Decision |
|---|---|---|---|
| CPU, RAM, timers, IRQ | ARM64 core, SMP, timer and IRQ paths | official SoC DTS include chain | preserve; no profile delta |
| UFS/storage | `CONFIG_SCSI_UFSHCD`, platform and MediaTek UFS | `ufshci@11270000`, clocks, resets, regulators | preserve; DTB independently blocked |
| USB | MediaTek HDRC, OTG, USB networking and PD | official USB/OTG/PD nodes | preserve |
| Wi-Fi/network | `CFG80211`, MediaTek combo/Wi-Fi, IPv4 | vendor connectivity nodes and external driver/firmware context unresolved | preserve config; do not claim hardware-ready Wi-Fi |
| battery/charging | MTK charger, BQ2589X, USB-PD | charger, battery table and PMIC nodes | preserve |
| thermal/watchdog/RTC | thermal, CPU thermal, watchdog and MT6358 RTC | thermal zones and PMIC nodes | preserve; never disable thermal protection |
| display/touch/input | DRM/Mediatek and `CONFIG_TOUCHSCREEN_FTS` | DSI panel plus Focaltech i2c0/touch@0 | preserve; Focaltech auto-update only is disabled |
| console/filesystem | 8250 console and filesystem support | UART aliases and storage DT remain incomplete | preserve; rootfs integration remains blocked |
| CCCI/DPMAIF/modem | Kconfig makes CCCI the owner of its modem HIF path; ECCCI depends on it | modem firmware/nodes not imported | remove in SERVER_MINIMAL only; do not modify VENDOR_REFERENCE |

The exact symbols, source directories, DT dependencies, firmware status and
module relationships are kept in the JSON graph rather than inferred from a
single successful compile.

## Focaltech finding

The official Focaltech path has two separable responsibilities:

1. `focaltech_core.c` and the I2C/input registration read touch data from the
   controller and register the Linux input device.
2. `focaltech_flash.c` contains firmware-update support. Its boot-time work
   exits immediately when `FTS_AUTO_UPGRADE_EN` is disabled. The embedded arrays
   include `FTS_UPGRADE_FW_FILE`, which resolves to the unavailable
   `include/firmware/fw_sample.i`; the driver also has a separate
   `request_firmware()` path and manual update entry points.

Therefore the profile patch sets `FTS_AUTO_UPGRADE_EN=0` and conditionally
removes only the compile-time embedded-array include. It does not disable
`CONFIG_TOUCHSCREEN_FTS`, does not create an empty firmware file, and does not
redistribute proprietary firmware. This preserves touch operation using the
controller's existing firmware, subject to future hardware validation.

## Mission 007 compiler gate

The clean reproduction produced the seven recorded errors: six unused-variable
diagnostics in `mt6357-accdet.c` and one old-style prototype diagnostic in
`bq2589x_charger.c`. The MT6357 driver is an optional jack/accessory detector;
its Kconfig entry has no charging dependency and explicitly permits `N` when a
board has no jack. The paired MT6359 detector exposed the same optional debt in
the first controlled rebuild, so both ACCDET symbols are disabled locally. The
audio codec and charging framework are not globally disabled.

The BQ2589x error was fixed with the localized, reversible
`0002-bq2589x-prototype.patch`. Its exported `get_charger_type()` function is
consumed through an existing `get_charger_type(void)` declaration in the
charger-type detector. `CONFIG_MTK_CHARGER=y` and `CONFIG_CHARGER_BQ2589X=y`
remain enabled, and `bq2589x_charger.o` compiles. No global `-Werror` disable or
`-Wno-error` workaround was introduced.

The structured gate report is
[`build-gate.json`](../devices/xiaomi-sea/server-minimal/build-gate.json). The
final PC/WSL result is `BUILT_UNTESTED`, with `Image` and `Image.gz`,
`System.map`, `.config`, `Module.symvers` and five modules preserved under the
ignored build output directory. The two generated DTBs are generic
`auto2712p1v1` outputs, not evidence for `sea`, so the DTB gate remains
blocked. The bounded result is `SEA_CONTINUE`; a second device with a public
target DTB and recovery evidence is recommended.

## CCCI/DPMAIF decision

The audited Kconfig and Makefile relationship is explicit: the CCCI device
option owns the CCCI code and the ECCCI driver builds the DPMAIF HIF objects.
The Kconfig help states that disabling the CCCI device option disables the CCCI
code, including its dummy API. The inspected critical UFS, USB, combo-Wi-Fi,
power, thermal, DRM and Focaltech paths do not select CCCI as a required
dependency. That is sufficient for an architectural `SERVER_MINIMAL` decision:
the initial Topazio server does not need cellular connectivity, so CCCI,
ECCCI/DPMAIF and MD1 are disabled by the explicit fragment.

It is not proof that every vendor runtime is independent, nor does it prove a
bootable phone. No DPMAIF cast was changed to silence a compiler warning, and
the modem firmware is not imported.

## Reproducible configuration

The base is the official Xiaomi `sea_defconfig` at commit
`6f6b84e0e2fa8d474db66798a051ec1835257729`. The derivation tool applies only
the four entries in
[`topazio_sea_server_defconfig`](../devices/xiaomi-sea/server-minimal/config/topazio_sea_server_defconfig),
then checks that critical symbols remain enabled and modem symbols are absent.

| Symbol | SERVER_MINIMAL value | Reason |
|---|---:|---|
| `CONFIG_MTK_CCCI_DEVICES` | `n` | modem CCCI/DPMAIF is outside the initial product |
| `CONFIG_MTK_ECCCI_DRIVER` | `n` | depends on CCCI modem HIF |
| `CONFIG_MTK_ECCCI_C2K` | `n` | modem/C2K path |
| `CONFIG_MTK_MD1_SUPPORT` | `0` | no cellular modem support |

All critical symbols are inherited from the base and tested: UFS, USB and USB
networking, `CFG80211`/MediaTek combo Wi-Fi, battery/charging, thermal,
DRM/display, input/touch and serial console. The generic IP stack symbols are
selected by the kernel's dependency model rather than repeated in this vendor
defconfig. The number of differing options is therefore
four in the explicit fragment; a final generated `.config` may contain normal
Kconfig dependency normalization and must be reported separately.

## DT, Wi-Fi and build boundary

The official `sea.dts` and `mt6781.dts` expose useful evidence for UFS, USB,
charger, thermal, DSI and touch, but the public source still references missing
vendor `sea/cust.dtsi` and `k6781v1_64_k419/cust.dtsi` inputs. A device tree
cannot be completed by inventing GPIOs, addresses, regulators or phandles.
Consequently `DTB = BLOCKED` independently of the kernel profile.

Mission 008 completed a separate static device-tree audit in
[`dt-analysis.json`](../devices/xiaomi-sea/reconstruction/dt-analysis.json).
Both official project files are overlays. The community `sea/cust.dtsi` is
recorded as `STRONG_CANDIDATE`; the `k6781v1_64_k419/cust.dtsi` remains
unknown. The existing 67,869-byte DTBO candidate was decompiled, checked for
fixups/symbols, and applied offline to a public `mt6781.dtb` generated from
the official SoC tree. The merge and structural round trip pass, but the base
is not proven to be the unit's stock sea DTB, so the maximum overall level is
`DT_STRUCTURALLY_VALID`, never `DT_SEA_CANDIDATE` or `DT_WORKING`.

Wi-Fi remains enabled in the configuration through MediaTek combo and
`cfg80211`, but the vendor WLAN driver/firmware acquisition context is not
complete and no blob is in this repository. A future build/installer contract
must acquire a license-compatible artifact externally and record its hash.

The selected compiler remains `clang-r433403b`. The final `Image` is 27,455,504
bytes with SHA-256
`1913c3c0c659784eb7c6d8204a84923d9d5bc07be5d84e474d2919575e246adc`; the
`Image.gz` is 11,482,091 bytes with SHA-256
`d58c2bfdf13c71cd3ed2c505ed767adbb651728cf388394066d23db0205468bd`.
`DTB` is still blocked, `DTBO` remains non-installable research/source state,
and no `boot.img` is created.

## Rootfs hand-off contract

Connecting a future kernel to the Topazio rootfs still requires a complete,
evidence-backed DTB/boot integration, stable UFS enumeration, the correct
console mapping, USB or Wi-Fi networking with permitted firmware, and any
out-of-tree modules installed under `/lib/modules`. The rootfs itself must
mount the actual block device, expose thermal/battery telemetry, start SSH and
provide the `admin@sea` server console. None of that authorizes a write to the
phone in this mission.

Recovery Readiness remains `BLOCKED`. This mission performed no flash, erase,
format, unlock, partition operation, SP Flash Tool action, payload, exploit or
bypass. The project is not authorized or ready to write anything to the device.
