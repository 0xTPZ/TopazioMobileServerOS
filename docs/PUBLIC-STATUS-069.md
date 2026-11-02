# Public status boundary — 069

This document describes the evidence available in `main` and does not authorize hardware flashing.

| Capability | Classification | Evidence or limit |
|---|---|---|
| ARM64 userspace contracts and services | IMPLEMENTED | `core/`, `services/`, and repository tests |
| ARM64 boot smoke test | IMPLEMENTED IN QEMU | The documented `virt` machine only |
| Redmi Note 12S native boot | RESEARCH / BLOCKED | No bootloader or device support package has been proven |
| Installation planning | EXPERIMENTAL | Read-only planner with fail-safe aborts |
| Physical flashing | NOT AVAILABLE | No partition, firmware or device operation is authorized |

Use the QEMU instructions in [`docs/QEMU-LAB.md`](QEMU-LAB.md) and the repository's verification commands. Hardware support must not be inferred from the ARM64 architecture alone.
