# Boot chain e artefatos do DSP `sea`

## Cadeia conhecida e desconhecida

| Componente | Estado | O que falta |
|---|---|---|
| MediaTek Boot ROM | INFERRED | evidência específica da unidade |
| preloader | UNKNOWN | pacote stock ou dump autorizado |
| LK/bootloader/fastboot | BLOCKED | transporte e estado do bootloader |
| `boot.img` | CONFIRMED_OFFLINE | v3, 4 KiB, gzip kernel, LZ4 ramdisk e hash stock |
| `vendor_boot.img` | ABSENT_FROM_VERIFIED_MANIFEST | container alternativo não identificado |
| `init_boot.img` | ABSENT_FROM_VERIFIED_MANIFEST | presença física da unidade ainda não enumerada |
| `dtbo.img`/DTB | DTBO_CONFIRMED / BASE_DTB_BLOCKED | DTBO stock analisado; base DTB não localizado |
| `vbmeta`/AVB | CONFIRMED_OFFLINE | família AVB reconstruída do payload; política da unidade não consultada |
| `super`, system, vendor, product | PARTIAL_CONFIRMED | grupo dynamic `main` e Virtual A/B confirmados por manifest |
| userdata/recovery | BLOCKED | enumeração somente leitura e recuperação |

Android moderno usa formatos de boot versionados e pode separar ramdisk
genérico, `vendor_boot` e DTB. A documentação AOSP é a referência de formato,
mas não substitui a leitura do layout stock deste aparelho. Não se infere A/B
ou partições dinâmicas de outro Xiaomi.

Fontes: [Android boot image header](https://source.android.com/docs/core/architecture/bootloader/boot-image-header),
[vendor boot partitions](https://source.android.com/docs/core/architecture/partitions/vendor-boot-partitions),
[generic boot](https://source.android.com/docs/core/architecture/partitions/generic-boot).

## Separação Core/DSP

O artefato Debian da Missão 002 é um rootfs/ext4 validado em QEMU `virt`.
Ele não contém o bootloader MediaTek, não é `boot.img`, não contém
`vendor_boot`, AVB, módulos proprietários ou firmware do `sea`. Um rootfs
Linux só pode ser conectado a um boot Android depois de fixar:

- header e cmdline aceitos pelo bootloader;
- ramdisk/init e política SELinux;
- DTB/DTBO da placa;
- módulos vendor e firmware com licença e versão compatíveis;
- esquema de partições e rollback/AVB.

## Pipeline reprodutível

`host-tools/device_artifact_pipeline.py` aceita somente caminhos explícitos
para kernel, DTB e imagem de boot já produzidos. Para cada entrada ele calcula
SHA-256. A ferramenta:

- bloqueia sem todos os inputs;
- bloqueia enquanto o DSP continuar `RESEARCH`/não instalável;
- nunca sintetiza `boot.img`;
- nunca chama ADB, fastboot ou utilitários de flash;
- não grava no aparelho.

O script `scripts/build-sea-kernel.sh` usa `O=` fora da árvore-fonte, registra
commit, log e motivo do bloqueio. A saída atual é apenas diagnóstico: não há
DTB `sea` autônomo nem kernel validado para o telefone.

## Boot não persistente — desenho futuro, não executado

Um eventual teste de boot não persistente só poderá ser desenhado depois de
identidade exata, backup verificável, recovery funcional, artefatos assinados
ou hashados e documentação do comando oficial. Ele deverá ser feito em uma
unidade dedicada, com rollback comprovado, e a falha deverá deixar o telefone
no estado stock. Esta missão não consulta nem executa esse caminho.

## Missão 009 — forensics stock

Foi analisado offline um componente `boot.img` do Redmi Note 12S `sea`, build
Global `OS2.0.209.0.VHZMIXM`, obtido por espelho com caminho upstream oficial.
O componente foi confirmado por fingerprint `Redmi/sea_global/sea`, header
Android v3, kernel GKI `6.6.58-android15` e ramdisk CPIO/LZ4. O relatório
machine-readable está em
[`devices/xiaomi-sea/firmware-forensics/mission-009.json`](../devices/xiaomi-sea/firmware-forensics/mission-009.json).

Isso não confirma o layout completo: o pacote integral não foi versionado, e
`vendor_boot`, DTB/DTBO, vbmeta, super e os metadados A/B continuam
desconhecidos. O Boot Header v3 não contém o DTB; a localização stock exata
precisa ser confirmada no `vendor_boot` ou em outro container. Recovery e
qualquer escrita física permanecem bloqueados.

## Missão 010 — pacote stock completo / deep forensics

Leituras ranged do Recovery OTA oficial `OS2.0.209.0.VHZMIXM` confirmaram
internamente `pre-device=sea`, `ota-type=AB`, Virtual A/B (`snapshot_enabled`
e `vabc_enabled`) e o grupo dynamic `main`. O payload contém `boot`, `dtbo`,
`vbmeta`, `vbmeta_system`, `vbmeta_vendor` e partições lógicas; não contém
entradas `vendor_boot`, `init_boot` ou `vendor_kernel_boot`.

O `dtbo.img` stock foi reconstruído sem instalar nada: 8 MiB, hash
`44b31ec3b3bfb82631a4e214fadafe109248ba880cb2a9dfe8d7b27bb47914c3`, uma
entrada FDT e hash de operação coincidente com o manifest. Os três blobs AVB
foram igualmente reconstruídos e validados por header/descriptors. Como o
payload não forneceu base DTB e o pacote integral não foi baixado, não foi
gerado `STOCK_MERGED_DT`; a comparação semântica com a Missão 008 permanece
fail-closed. Recovery está `NOT_READY`, e nenhuma escrita física foi feita.

Relatório: [`mission-010.json`](../devices/xiaomi-sea/firmware-forensics/mission-010.json).

## Missão 011 — origem do DTB e contrato Android 15

A análise estrutural de `boot.img`, kernel gzip, kernel descomprimido e
ramdisk LZ4 encontrou zero candidatos FDT válidos. O kernel
`6.6.58-android15-8-g19e0e8cef6b2-4k` contém IKCONFIG, `CONFIG_MODULES=y`,
`CONFIG_MODVERSIONS=y` e sinais fortes de GKI, mas o KMI exato não foi
confirmado. O DTBO stock exige 60 símbolos-base; o inventário está em
[`stock-required-base-symbols.json`](../devices/xiaomi-sea/reconstruction/stock-required-base-symbols.json).

Uma faixa seletiva do `vendor_dlkm` oficial foi reconstruída offline, validou
o hash EROFS e permitiu contar 209 módulos e registrar `modules.alias`,
`modules.dep`, `modules.load` e `modules.softdep`, sem copiar binários
proprietários ao repositório. O plano futuro de consultas somente leitura está
em [`SEA-READONLY-INVENTORY-PLAN.md`](SEA-READONLY-INVENTORY-PLAN.md); ele não
foi executado. O relatório completo é
[`mission-011.json`](../devices/xiaomi-sea/firmware-forensics/mission-011.json).

`STOCK_MERGED_DT`, geração de boot, instalação e recovery continuam bloqueados.
