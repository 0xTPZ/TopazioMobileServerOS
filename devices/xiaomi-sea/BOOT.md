# Boot — `sea`

**Estado:** `BLOCKED` para instalação e para boot nativo nesta missão.

A auditoria local observou uma interface USB MediaTek sem driver associado
(erro 28) e nenhuma entrada em `adb devices` ou `fastboot devices`. Não foi
possível consultar `getvar`, estado do bootloader ou partições.

A árvore pública Xiaomi `sea-t-oss` prova disponibilidade de código-fonte
vendor, não uma imagem Topazio, um boot chain reproduzível ou suporte mainline.
`sea.dts` é um overlay e depende de arquivos vendor ausentes na branch pública;
o `Makefile` não gera um alvo `sea` diretamente. O perfil Android T correto é
Clang `clang-r433403b`; GCC 13 falha antes por incompatibilidade no
`always_inline` de `kernel/sched/tune.c`, e Clang depois encontra firmware e
warnings de código legado que ainda impedem um kernel completo.

O layout A/B/dynamic, `boot`, `vendor_boot`, `init_boot`, `dtbo`, `vbmeta`,
`super`, `vendor` e `recovery` da unidade permanece `UNKNOWN/BLOCKED`.

Veja a análise completa em [`docs/BOOT-ARTIFACTS.md`](../../docs/BOOT-ARTIFACTS.md).

## Próxima coleta permitida

Somente confirmar enumeração e executar consultas de leitura com ferramentas e
drivers de origem oficial. Não forçar `android_winusb.inf`, não desbloquear,
não apagar, não usar SP Flash Tool e não gravar partições.
