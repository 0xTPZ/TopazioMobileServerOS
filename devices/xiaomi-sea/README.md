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

A auditoria de firmware stock da Missão 009 está em
[`firmware-forensics/mission-009.json`](firmware-forensics/mission-009.json).
Ela contém somente metadados, hashes e conclusões; os arquivos de firmware
permanecem no cache ignorado do host.

A investigação profunda da Missão 010 está em
[`firmware-forensics/mission-010.json`](firmware-forensics/mission-010.json).
Ela confirmou, por metadata e manifest OTA oficial, A/B, Virtual A/B,
partições dinâmicas, `dtbo` e AVB. O pacote integral e o base DTB permanecem
fora do repositório; `STOCK_MERGED_DT` e recovery continuam não prontos.

A Missão 011 registrou o contrato Android 15 em
[`firmware-forensics/mission-011.json`](firmware-forensics/mission-011.json).

A Missão 012 realizou o audit do host e tentou o inventário físico em modo
fail-closed. Como `adb` e `fastboot` não estavam disponíveis e nenhum Android
foi detectado pelo PnP, nenhum comando foi executado no telefone. O resultado
sanitizado está em
[`firmware-forensics/mission-012.json`](firmware-forensics/mission-012.json)
e [`unit-observation.json`](unit-observation.json).
