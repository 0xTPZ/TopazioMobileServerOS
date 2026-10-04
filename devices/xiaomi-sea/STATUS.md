# Status — `sea`

| Área | Estado | Evidência / limite |
|---|---|---|
| identidade comercial | CONFIRMED | auditoria local + FAQ Xiaomi |
| ARM64/SoC | CONFIRMED | auditoria local + especificação pública |
| kernel vendor público | CONFIRMED | `sea-t-oss` na tabela Xiaomi |
| ADB/fastboot live | BLOCKED | transporte/driver indisponível |
| bootloader da unidade | UNKNOWN | nenhuma consulta acessível |
| Linux mainline | UNKNOWN | não há validação neste projeto |
| Core em PC | CONFIRMED | testes do repositório |
| boot Topazio | UNKNOWN | nenhuma imagem existe |
| instalação segura | BLOCKED | recovery e transporte não comprovados |

O pacote permanece em `RESEARCH` até haver evidência reproduzível de boot e
serviços mínimos com recuperação.
