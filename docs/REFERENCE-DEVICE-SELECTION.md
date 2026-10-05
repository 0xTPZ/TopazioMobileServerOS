# Reference-device selection

This rubric prevents choosing a phone only because its SoC is fast or its
kernel source is visible. A candidate is useful to Topazio Mobile Server OS
only when its boot chain, device tree, firmware boundary and recovery path can
be audited without writing to a device.

## Criteria and score

Score every criterion from 0 to 5 using public, reproducible evidence:

| Criterion | Weight | 0 | 3 | 5 |
|---|---:|---|---|---|
| Exact model/board identity | 2 | ambiguous | likely | confirmed by multiple sources |
| Kernel source and reproducible toolchain | 4 | absent | partial | pinned source, defconfig and toolchain |
| Target DTS/DTB completeness | 5 | absent | partial includes | target DTB or complete public source |
| Firmware availability/licensing | 4 | unknown/proprietary | partial | redistributable or documented external artifact |
| Boot-artifact documentation | 4 | unknown | partial | verified format, offsets and hashes |
| Recovery and unbrick evidence | 5 | none | vendor-only | documented, reversible and independently checked |
| Storage and console suitability | 3 | unclear | one path | UFS/eMMC plus serial/USB evidence |
| USB networking | 2 | absent | generic | target controller/config/DT evidence |
| Wi-Fi and thermal support | 2 | absent | config only | driver, firmware and DT evidence |
| Mainline/community maintenance | 2 | none | dormant | active, reproducible maintenance |

Calculate:

```text
weighted_score = sum(score_i * weight_i) / sum(weight_i)
```

Record the raw score, evidence URL or file, date checked, and unresolved
assumption for every criterion. Do not award a 5 for a symbol appearing in a
defconfig alone; hardware readiness requires matching DT and firmware
evidence.

## Decision bands

- `4.0–5.0`: primary reference candidate, subject to a separate recovery gate.
- `3.0–3.9`: research candidate; keep a second device in parallel.
- `2.0–2.9`: hold; use only for source or static analysis.
- `<2.0`: reject as a reference device.

Hard stops override the average: no confirmed identity, no target DT evidence,
unknown recovery, or a required proprietary blob with no lawful acquisition
path means `BLOCKED`, regardless of score.

## Reusable record

```json
{
  "device": "vendor-model-board",
  "checked_at": "YYYY-MM-DD",
  "scores": {
    "identity": {"score": 0, "evidence": "", "assumption": ""},
    "kernel_toolchain": {"score": 0, "evidence": "", "assumption": ""},
    "target_dtb": {"score": 0, "evidence": "", "assumption": ""},
    "firmware": {"score": 0, "evidence": "", "assumption": ""},
    "boot_artifact": {"score": 0, "evidence": "", "assumption": ""},
    "recovery": {"score": 0, "evidence": "", "assumption": ""},
    "storage_console": {"score": 0, "evidence": "", "assumption": ""},
    "usb_network": {"score": 0, "evidence": "", "assumption": ""},
    "wifi_thermal": {"score": 0, "evidence": "", "assumption": ""},
    "maintenance": {"score": 0, "evidence": "", "assumption": ""}
  },
  "weighted_score": 0.0,
  "hard_stop": "",
  "decision": "PRIMARY|RESEARCH|HOLD|REJECT"
}
```

For `sea`, the current evidence supports source research and a green kernel
build, but the missing target `cust.dtsi` inputs, firmware context and recovery
evidence trigger hard stops for hardware deployment. A second device with a
public target DTB and recovery procedure is therefore recommended.
