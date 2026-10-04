# Status — `sea`

| Área | Estado | Evidência / limite |
|---|---|---|
| identidade comercial | CONFIRMED | auditoria local + FAQ Xiaomi |
| ARM64/SoC | CONFIRMED | auditoria local + especificação pública |
| kernel vendor público | CONFIRMED | `sea-t-oss`, commit fixado e arquivos `sea_*` presentes |
| versão da fonte | CONFIRMED | Linux `4.19.191` no Makefile vendor |
| kernel `sea_defconfig` | CONFIRMED | defconfig gera configuração out-of-tree |
| kernel/device DTB | BLOCKED | Clang correto supera `tune.c`, mas faltam firmware cliente, `cust.dtsi` vendor e target DTS |
| contexto vendor público | PARTIAL | um candidato `sea/cust.dtsi`, nenhum `k6781v1_64_k419/cust.dtsi`, firmware Focaltech real ausente |
| perfil VENDOR_REFERENCE | BLOCKED | manifesto controlado preserva a árvore Xiaomi sem substituições silenciosas |
| perfil SERVER_MINIMAL | SOURCE_ONLY / BLOCKED | camada externa formalizada; CCCI/DPMAIF removido no fragmento, kernel/DTB ainda não produzidos |
| ADB/fastboot live | BLOCKED | transporte/driver indisponível |
| bootloader da unidade | UNKNOWN | nenhuma consulta acessível |
| Linux mainline | UNKNOWN | não há validação neste projeto |
| Core em PC | CONFIRMED | testes do repositório |
| boot chain/partições | UNKNOWN/BLOCKED | layout A/B/dynamic, AVB e imagens stock não observados |
| artefato de boot Topazio | BLOCKED | pipeline exige kernel/DTB/boot image reais e hashes |
| instalação segura | BLOCKED | recovery e transporte não comprovados |

O pacote permanece em `RESEARCH` até haver evidência reproduzível de boot e
serviços mínimos com recuperação.

Missão 004 identificou `clang-r433403b` como perfil Android T da própria
árvore Xiaomi. Um DTBO candidato foi compilado apenas para validação estática
com include comunitário externo; ele não é artefato de boot.

Missão 005 adicionou o [mapa do ecossistema](../../docs/SEA-ECOSYSTEM.md) e o
banco estruturado de proveniência. O `fw_sample.i` comunitário é um placeholder
de zero bytes, não firmware; `Recovery Readiness` continua `BLOCKED`.
