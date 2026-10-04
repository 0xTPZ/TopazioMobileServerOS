# Boot — `sea`

**Estado:** `BLOCKED` para instalação nesta missão.

A auditoria local observou uma interface USB MediaTek sem driver associado
(erro 28) e nenhuma entrada em `adb devices` ou `fastboot devices`. Não foi
possível consultar `getvar`, estado do bootloader ou partições.

A árvore pública Xiaomi `sea-t-oss` prova disponibilidade de código-fonte
vendor, não uma imagem Topazio, um boot chain reproduzível ou suporte mainline.

## Próxima coleta permitida

Somente confirmar enumeração e executar consultas de leitura com ferramentas e
drivers de origem oficial. Não forçar `android_winusb.inf`, não desbloquear,
não apagar, não usar SP Flash Tool e não gravar partições.
