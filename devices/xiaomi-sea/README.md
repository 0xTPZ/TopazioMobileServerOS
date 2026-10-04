# Device Support Package — Xiaomi Redmi Note 12S (`sea`)

**Estado:** `RESEARCH` — Missão 003: fonte oficial identificada; bring-up e
artefato de boot continuam bloqueados.

Este pacote descreve o dispositivo de referência #001 sem declarar suporte de
boot. O telefone não foi apagado, desbloqueado, particionado ou flasheado na
Missão 001.

## Identidade conhecida

- fabricante: Xiaomi;
- modelo: Redmi Note 12S;
- codename de pesquisa: `sea`;
- SoC: MediaTek Helio G96 / MT6781V-CD;
- arquitetura: ARM64.

O DSP fixa a branch oficial `sea-t-oss`, o commit analisado, o defconfig e os
DTS em [`device.json`](device.json). A matriz de capacidades está em
[`capabilities.json`](capabilities.json).

Consulte `HARDWARE.md`, `BOOT.md` e `STATUS.md` para limites e evidências.
