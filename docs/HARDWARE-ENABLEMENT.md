# Missão 003 — hardware enablement do Xiaomi `sea`

Estado global: **PARTIAL**. O DSP continua `RESEARCH` e `installable: false`.
O Core executável em QEMU não é uma imagem para o Redmi Note 12S.

## Evidência oficial

A tabela oficial da Xiaomi associa `sea-t-oss` ao Redmi Note 12S, Android T e
à base `bsp-t-alps-release-s0.mp1.tc8sp2-cs1-xm-V1.0.13`. A cópia analisada
está registrada em [`devices/xiaomi-sea/device.json`](../devices/xiaomi-sea/device.json).

O código público contém `sea_defconfig`, `sea_debug_defconfig`, `sea.dts`,
`k6781v1_64_k419.dts` e a base `mt6781.dts`. A leitura do código mostra
configuração para USB/OTG, UFS MediaTek, conectividade, display DSI, touch,
energia, bateria e thermal. Isso é **SOURCE_AVAILABLE**, não prova de hardware
funcionando.

O `Makefile` da fonte declara Linux `4.19.191`. O `sea_defconfig` ainda mostra
uma combinação que precisa do contexto vendor (`CONFIG_MACH_MT6781=y` junto
com `CONFIG_MTK_PLATFORM="mt6785"`); isso foi preservado como evidência, não
“corrigido” no repositório oficial.

Há duas limitações relevantes na fonte pública:

- `sea.dts` é `/plugin/` e inclui `sea/cust.dtsi`, que não está disponível na
  branch pública analisada;
- `arch/arm64/boot/dts/mediatek/Makefile` não registra um alvo `sea` para
  produzir o DTB; o build com GCC 13 também para em `kernel/sched/tune.c`.

Esses fatos deixam o build do kernel como **BLOCKED**, sem editar ou “corrigir”
a árvore oficial.

## Classificação por área

| Área | Estado | Limite da evidência |
|---|---|---|
| identidade, ARM64 e Helio G96/MT6781 | CONFIRMED | especificação Xiaomi e auditoria local |
| kernel vendor `sea-t-oss` | CONFIRMED | repositório oficial e commit fixado |
| CPU, USB, Wi-Fi, energia, display e touch | SOURCE_AVAILABLE | defconfig/DTS; falta teste no aparelho |
| RAM/SKU da unidade | UNKNOWN | variantes comerciais e sem inventário live |
| UFS | SOURCE_AVAILABLE | drivers/configuração; não prova do chip instalado |
| GPU, áudio, câmera, modem e sensores | SOURCE_AVAILABLE/UNKNOWN | código e especificações; sem bring-up |
| bootloader, AVB, partições e firmware da unidade | UNKNOWN/BLOCKED | ADB/fastboot indisponíveis |
| driver Windows para a interface live | BLOCKED | `VID_0E8D:201C`, Code 28 |

Veja a matriz detalhada em [`devices/xiaomi-sea/capabilities.json`](../devices/xiaomi-sea/capabilities.json).

## Console e operação física futura

O console de emergência deve ser tratado como uma camada separada do boot:

1. console serial/earlycon somente quando o mapa de UART, pinmux e baud forem
   comprovados para a placa exata;
2. console local framebuffer/touch somente após display, touch e energia terem
   testes de bring-up;
3. SSH e HTTP só depois de rootfs, rede, SELinux e serviços terem logs de boot.

O mínimo de UI física é um framebuffer/DRM com painel correto, um input-event
de touch, um terminal TTY com um processo de console e um teclado virtual
leve. Não é necessário um desktop: o painel pode mostrar status e endereço IP,
enquanto SSH continua sendo a interface administrativa principal.

Não se assume que o USB-C exponha UART. Não se usa test-point, desmontagem,
curto ou cabo especial nesta missão.

## Limites de segurança

Não foram executados `adb` ou `fastboot` contra o telefone nesta missão. Não
foram instalados drivers Windows, não houve unlock, flash, erase, format,
wiping, alteração de partição, bypass de FRP/conta/Secure Boot ou tentativa de
boot temporário.
