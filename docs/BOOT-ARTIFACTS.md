# Boot chain e artefatos do DSP `sea`

## Cadeia conhecida e desconhecida

| Componente | Estado | O que falta |
|---|---|---|
| MediaTek Boot ROM | INFERRED | evidência específica da unidade |
| preloader | UNKNOWN | pacote stock ou dump autorizado |
| LK/bootloader/fastboot | BLOCKED | transporte e estado do bootloader |
| `boot.img` | UNKNOWN | formato, cmdline, ramdisk e hash stock |
| `vendor_boot.img` | UNKNOWN | header/ramdisk vendor e módulos |
| `init_boot.img` | UNKNOWN | presença e papel no SKU |
| `dtbo.img`/DTB | UNKNOWN | inventário e correspondência exata |
| `vbmeta`/AVB | UNKNOWN | chaves, rollback index e política da unidade |
| `super`, system, vendor, product | UNKNOWN | partições e grupo dynamic |
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
