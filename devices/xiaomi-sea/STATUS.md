# Status — `sea`

| Área | Estado | Evidência / limite |
|---|---|---|
| identidade comercial | CONFIRMED | auditoria local + FAQ Xiaomi |
| ARM64/SoC | CONFIRMED | auditoria local + especificação pública |
| kernel vendor público | CONFIRMED | `sea-t-oss`, commit fixado e arquivos `sea_*` presentes |
| versão da fonte | CONFIRMED | Linux `4.19.191` no Makefile vendor |
| kernel `sea_defconfig` | CONFIRMED | defconfig gera configuração out-of-tree |
| kernel/device DTB | BLOCKED | overlay, include vendor ausente, build para em `tune.c` |
| ADB/fastboot live | BLOCKED | transporte/driver indisponível |
| bootloader da unidade | UNKNOWN | nenhuma consulta acessível |
| Linux mainline | UNKNOWN | não há validação neste projeto |
| Core em PC | CONFIRMED | testes do repositório |
| boot chain/partições | UNKNOWN/BLOCKED | layout A/B/dynamic, AVB e imagens stock não observados |
| artefato de boot Topazio | BLOCKED | pipeline exige kernel/DTB/boot image reais e hashes |
| instalação segura | BLOCKED | recovery e transporte não comprovados |

O pacote permanece em `RESEARCH` até haver evidência reproduzível de boot e
serviços mínimos com recuperação.
