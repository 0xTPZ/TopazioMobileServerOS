# Status — `sea`

| Área | Estado | Evidência / limite |
|---|---|---|
| identidade comercial | CONFIRMED | auditoria local + FAQ Xiaomi |
| ARM64/SoC | CONFIRMED | auditoria local + especificação pública |
| kernel vendor público | CONFIRMED | `sea-t-oss`, commit fixado e arquivos `sea_*` presentes |
| versão da fonte | CONFIRMED | Linux `4.19.191` no Makefile vendor |
| kernel `sea_defconfig` | CONFIRMED | defconfig gera configuração out-of-tree |
| kernel/device DTB | PARTIAL / DT_STRUCTURALLY_VALID | overlay e merge offline no `mt6781.dtb` público são válidos estruturalmente; o DTB stock `sea` continua não provado |
| contexto vendor público | PARTIAL | um candidato `sea/cust.dtsi`, nenhum `k6781v1_64_k419/cust.dtsi`, firmware Focaltech real ausente |
| perfil VENDOR_REFERENCE | BLOCKED | manifesto controlado preserva a árvore Xiaomi sem substituições silenciosas |
| perfil SERVER_MINIMAL | BUILT_UNTESTED / DTB BLOCKED | baseline kernel preservado; `sea` DTB, firmware, boot artifact e rootfs continuam bloqueados |
| ADB/fastboot live | BLOCKED | transporte/driver indisponível |
| bootloader da unidade | UNKNOWN | nenhuma consulta acessível |
| Linux mainline | UNKNOWN | não há validação neste projeto |
| Core em PC | CONFIRMED | testes do repositório |
| boot chain/partições | PARTIAL | OTA stock confirmou A/B, Virtual A/B, dynamic/main e AVB; base DTB e procedimento da unidade continuam ausentes |
| artefato de boot Topazio | BLOCKED | pipeline exige kernel/DTB/boot image reais e hashes |
| instalação segura | BLOCKED | recovery e transporte não comprovados |
| firmware stock / forensics | PARTIAL | manifest oficial ranged confirmou identidade, A/B/Virtual A/B/dynamic, `dtbo` e família `vbmeta`; pacote completo e base DTB não foram baixados |

O pacote permanece em `RESEARCH` até haver evidência reproduzível de boot e
serviços mínimos com recuperação.

Missão 004 identificou `clang-r433403b` como perfil Android T da própria
árvore Xiaomi. Um DTBO candidato foi compilado apenas para validação estática
com include comunitário externo; ele não é artefato de boot.

Missão 005 adicionou o [mapa do ecossistema](../../docs/SEA-ECOSYSTEM.md) e o
banco estruturado de proveniência. O `fw_sample.i` comunitário é um placeholder
de zero bytes, não firmware; `Recovery Readiness` continua `BLOCKED`.

Missão 007 reproduziu os sete erros do gate, resolveu os seis erros de ACCDET
desativando somente os módulos opcionais de detecção de jack e corrigiu a
assinatura C do BQ2589x sem remover charging. O kernel `SERVER_MINIMAL` foi
construído como `BUILT_UNTESTED`; o relatório completo está em
`server-minimal/build-gate.json`. A decisão é `SEA_CONTINUE`, com recomendação
de buscar um segundo dispositivo com DTB e recuperação publicamente verificáveis.

Missão 008 preservou esse kernel como
[`SEA_SERVER_MINIMAL_KERNEL_001`](server-minimal/kernel-baseline.json), com
hashes, tamanhos, patches e procedimento validados por
`host-tools/verify_kernel_baseline.py`. O DTBO externo foi reaplicado offline
ao candidato público `mt6781.dtb`, mas a ausência do `cust.dtsi` oficial e do
base stock impede `DT_SEA_CANDIDATE`. Recovery continua `BLOCKED` e nenhuma
operação de escrita foi executada.

Missão 009 confirmou offline um `boot.img` stock correspondente ao `sea`
Global OS2.0.209.0.VHZMIXM por fingerprint, build property e hash local. O
header é v3, o kernel é `6.6.58-android15` e o ramdisk é CPIO comprimido em
LZ4 Android. Como o pacote completo não foi versionado nem totalmente
baixado, `vendor_boot`, DTB, DTBO, vbmeta, partições e recuperação continuam
`UNKNOWN/BLOCKED`; nenhuma operação no telefone foi executada.

Missão 010 confirmou por leituras HTTP ranged do Recovery OTA oficial que o
pacote é `ota-type=AB`, usa Virtual A/B com grupo dynamic `main` e contém
`boot`, `dtbo`, `vbmeta`, `vbmeta_system`, `vbmeta_vendor` e as partições
lógicas. O `dtbo.img` de entrada única e os três blobs AVB foram reconstruídos
offline e tiveram seus hashes conferidos contra o manifest `CrAU`. O pacote
integral não foi baixado por limitação de taxa; `STOCK_MERGED_DT` continua
bloqueado porque o base DTB não apareceu no payload. Recovery avançou para
`NOT_READY`, sem qualquer escrita no aparelho. O relatório está em
[`firmware-forensics/mission-010.json`](firmware-forensics/mission-010.json).

Missão 011 analisou o contrato Android 15: nenhum FDT válido foi encontrado
no `boot.img`, kernel ou ramdisk; o DTBO stock exige 60 símbolos-base e o
kernel é `GKI_LIKELY`, sem KMI exato confirmado. `vendor_dlkm` foi reconstruído
seletivamente como EROFS, com 209 módulos inventariados sem versionar blobs.
O relatório está em
[`firmware-forensics/mission-011.json`](firmware-forensics/mission-011.json).

Missão 012 autorizou o primeiro inventário físico, mas o host não possui
`adb` nem `fastboot` disponíveis e o PnP não mostrou Android/Xiaomi/MediaTek.
O coletor fail-closed não executou comandos no telefone; o relatório
sanitizado está em
[`firmware-forensics/mission-012.json`](firmware-forensics/mission-012.json)
e [`unit-observation.json`](unit-observation.json). Recovery permanece
`BLOCKED` e a origem do DTB continua `UNKNOWN`.

Missão 012-B corrigiu a descoberta das Platform Tools: `adb` e `fastboot`
37.0.1 foram encontrados em `C:\AndroidTools\platform-tools`, sem alterar o
PATH. O Windows identificou o Redmi Note 12S como WPD/MTP (`VID_2717`,
driver Microsoft `wpdmtp.inf`, problema 0), mas `adb devices` e
`fastboot devices` ficaram vazios. Nenhum shell ou `getvar` foi executado;
Recovery segue `BLOCKED`. O relatório está em
[`firmware-forensics/mission-012b.json`](firmware-forensics/mission-012b.json).
