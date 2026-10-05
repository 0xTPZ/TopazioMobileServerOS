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
| boot chain/partições | UNKNOWN/BLOCKED | layout A/B/dynamic, AVB e imagens stock não observados |
| artefato de boot Topazio | BLOCKED | pipeline exige kernel/DTB/boot image reais e hashes |
| instalação segura | BLOCKED | recovery e transporte não comprovados |
| firmware stock / forensics | PARTIAL | `sea` boot component OS2.0.209 Global analisado offline; pacote completo, DTB/DTBO, AVB e layout ainda desconhecidos |

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
