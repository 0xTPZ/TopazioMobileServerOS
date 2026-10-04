# SERVER_MINIMAL patches

Patch order is recorded in `../manifests/build-plan.json`.

`0001-focaltech-no-auto-upgrade.patch` is based on the official Xiaomi source
commit `6f6b84e0e2fa8d474db66798a051ec1835257729`. It removes the compile-time
dependency on the unavailable embedded `fw_sample.i` only when the same patch
sets `FTS_AUTO_UPGRADE_EN=0`. The controller's existing firmware is not read
from Git, and the normal touch-data/input registration remains enabled.

No patch changes pointer casts in DPMAIF. The entire CCCI/DPMAIF path is
disabled by the separate configuration fragment because cellular modem support
is outside the initial server contract.
