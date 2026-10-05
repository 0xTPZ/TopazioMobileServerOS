# `SERVER_MINIMAL` — `sea`

This is an external, experimental profile layered on the pinned Xiaomi
`sea-t-oss` source. It does not replace or mutate `VENDOR_REFERENCE`.

The profile starts from `arch/arm64/configs/sea_defconfig`, applies the
explicit fragment in `config/topazio_sea_server_defconfig`, and then applies
the ordered patches in `patches/`. The fragment removes the CCCI/DPMAIF modem
path and keeps the hardware required by `TOPAZIO_SERVER_PROFILE`: CPU/SMP,
RAM, timers, interrupt handling, UFS, USB, Wi-Fi support, battery/charging,
thermal protection, DRM/display, touchscreen/input, console and networking.

The profile is source-only at this checkpoint. The public source still lacks
the vendor `cust.dtsi` inputs required to produce a trustworthy `sea` DTB,
and the public Wi-Fi vendor driver/firmware context is not redistributed here.
Those are independent blockers; they are not solved by disabling critical
hardware.

## Layer

```text
official Xiaomi source @ 6f6b84e0e2fa8d474db66798a051ec1835257729
  + config/topazio_sea_server_defconfig
  + patches/0001-focaltech-no-auto-upgrade.patch
  + patches/0002-bq2589x-prototype.patch
  = reproducible SERVER_MINIMAL build tree (PC/WSL only)
```

The Focaltech patch disables only the boot-time embedded-firmware auto-update
path. The BQ2589x patch corrects one old-style C prototype without changing
charging logic. `CONFIG_SND_SOC_MT6357_ACCDET` and
`CONFIG_SND_SOC_MT6359_ACCDET` are disabled as optional audio jack detection;
the charging symbols remain enabled.

Mission 007 gate result: `BUILT_UNTESTED` kernel and modules, with persistent
artifacts in `build/out/sea-server-minimal-gate-007-final/`. A target `sea`
DTB, firmware contract, boot artifact and rootfs remain blocked.

See [the profile report](../../../docs/SERVER-MINIMAL.md), the structured
[build manifest](manifests/build-plan.json), and the generic
[`TOPAZIO_SERVER_PROFILE`](../../../profiles/TOPAZIO_SERVER_PROFILE.json).
