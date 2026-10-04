# Mapa do ecossistema público do Redmi Note 12S / `sea`

Estado da pesquisa em 2026-10-04: **PARTIAL / BLOCKED**. A fonte Xiaomi e a
toolchain Android T estão confirmadas, mas o contexto vendor necessário para
um kernel + DT reproduzível não está publicado de forma suficiente. O telefone
não foi conectado nem modificado.

O banco estruturado e reutilizável está em
[`devices/xiaomi-sea/sources.json`](../devices/xiaomi-sea/sources.json). Ele
separa fonte, componente, hash, licença, confiança e relação entre árvores.

## Fonte oficial

| Item | Evidência | Classificação |
|---|---|---|
| [MiCode/Xiaomi_Kernel_OpenSource](https://github.com/MiCode/Xiaomi_Kernel_OpenSource), `sea-t-oss`, `6f6b84e0e2fa8d474db66798a051ec1835257729` | README Xiaomi associa a branch ao Redmi Note 12S, Android T e ao release MediaTek `bsp-t-alps-release-s0.mp1.tc8sp2-cs1-xm-V1.0.13`; o commit nomeia `sea_defconfig` | **OFFICIAL** |
| [AOSP clang-r433403b](https://android.googlesource.com/platform/prebuilts/clang/host/linux-x86/+/refs/tags/android-s-v2-beta-2/clang-r433403b) | `build.config.mtk.aarch64.tiramisu` seleciona LLVM/Clang, e o prebuilt AOSP contém a versão esperada | **OFFICIAL** |
| [Especificação Xiaomi](https://www.mi.com/co/product/redmi-note-12s/specs/) | identidade comercial, MT6781/Helio G96 e ARM64 | **OFFICIAL** |

O checkout oficial permanece externo à árvore do Topazio, limpo e usado com
`O=`. Não há cópia de firmware ou blob no repositório.

## Genealogia e fontes comunitárias

| Repositório | Ref observado | Relação | Classificação |
|---|---|---|---|
| [android_kernel_xiaomi_mt6781](https://github.com/mt6781-sea/android_kernel_xiaomi_mt6781) | `lineage-23.2`, `ae44e42c393b44b1534a7fcd7065366abe6bfe65` (2026-02-21) | árvore comunitária posterior para MT6781/sea; contém o único `sea/cust.dtsi` localizado | **COMMUNITY_VERIFIED**; o `cust.dtsi` é **STRONG_CANDIDATE** |
| [android_device_xiaomi_sea](https://github.com/mt6781-sea/android_device_xiaomi_sea) | `lineage-23.2`, `5bb6ea26756658687da2189dceb4d76b923ba7d3` (2026-07-29) | device tree Lineage; fornece BoardConfig, dependências e inventário de blobs | **COMMUNITY_VERIFIED**; offsets são **WEAK_CANDIDATE** |
| [twrp_device_xiaomi_sea](https://github.com/mt6781-sea/twrp_device_xiaomi_sea) | `main`, `1ae754e55373fc81089ce758858eac62a58347da` | árvore TWRP criada para o codename, sem prova de recovery stock da unidade | **WEAK_CANDIDATE** |
| [android_vendor_xiaomi_sea](https://github.com/mt6781-sea/android_vendor_xiaomi_sea) | `16.0`, `021a2883e9c0755ca076c3365242cd80868c5483` | contém bibliotecas proprietárias e `radio/md1img.img` via LFS | **PROPRIETARY**; não importado |

As duas árvores kernel têm tamanhos de snapshot diferentes (74.460 contra
82.414 caminhos `git ls-tree -r`). O número não é um diff semântico, mas é uma
medição reproduzível de que a árvore comunitária não é uma cópia textual
idêntica do snapshot Xiaomi. A história observada do kernel comunitário não
mostra ancestralidade Git comum com `sea-t-oss`; portanto a relação é tratada
como derivação provável por conteúdo/uso, não como fork oficial provado.

O device tree comunitário declara, entre outros, Android boot header 2,
`Image.gz`, DTB incluído no boot e DTBO separado. Esses campos ajudam a
mapear o ecossistema Android, mas não substituem uma imagem stock, um mapa de
partições ou a confirmação da unidade.

## Busca negativa

A busca incluiu Xiaomi/MiCode, AOSP, LineageOS, GitHub, GitLab, Codeberg,
TWRP, OrangeFox, postmarketOS, Droidian e Halium. Foram encontrados guias e
infraestrutura genérica de [Droidian](https://docs.droidian.org/porting-guide/kernel-compilation/)
e [Halium](https://docs.halium.org/), além do índice de
[dispositivos postmarketOS](https://wiki.postmarketos.org/wiki/Devices), mas
não foi encontrada uma porta pública `sea` suficientemente específica para
fornecer os arquivos vendor ausentes. Esses resultados são **UNRELATED** para
a reconstrução do kernel Xiaomi; não foram usados como substitutos.

## `cust.dtsi`: prioridade máxima

| Arquivo | Oficial Xiaomi | Comunidade | Resultado |
|---|---|---|---|
| `sea/cust.dtsi` | referenciado por `<sea/cust.dtsi>`, ausente no commit oficial | presente no kernel comunitário, SHA-256 `9ba54ed35a7ecb82c9b2d9ee5ed651162d8ca689174b0ca2ec29123189528216` | **1 candidato público**, sem convergência independente; não importado |
| `k6781v1_64_k419/cust.dtsi` | referenciado, ausente | não localizado na árvore comunitária | **0 versões públicas localizadas** |

O candidato `sea/cust.dtsi` tem cabeçalho de `MTK SP DrvGen Version: 3.5.160809
for MT6781`, 494 linhas no snapshot observado, e declarações para ADC,
clock-buffer, I2C/câmera, carregamento/USB-C, NFC, GPIO, touch e DSI. Isso
explica por que ele é tecnicamente plausível. Ainda assim:

- o conteúdo não tem hash igual a um snapshot oficial disponível;
- o kernel comunitário usa `cust_mt6781_sea_camera.dtsi`, enquanto o Xiaomi
  público usa `cust_mt6781_camera.dtsi`;
- a existência de `drivers/misc/mediatek/dws/mt6785/sea.dws` no source Xiaomi
  indica um possível insumo do DrvGen, mas não reproduz sozinha todos os
  arquivos vendor;
- nenhum segundo repositório independente foi encontrado com o mesmo conteúdo.

Conclusão: **STRONG_CANDIDATE**, nunca **OFFICIAL**. O `k6781...cust.dtsi`
continua **UNKNOWN**.

## Focaltech e `fw_sample.i`

O caminho não é um arquivo gerado pelo Makefile. No source Xiaomi:

1. `arch/arm64/configs/sea_defconfig` define `CONFIG_TOUCHSCREEN_FTS=y`;
2. `drivers/input/touchscreen/mediatek/ft3418_i2c/Makefile` inclui o módulo
   quando essa configuração está ativa;
3. `focaltech_flash.c` inclui `FTS_UPGRADE_FW_FILE`;
4. `focaltech_config.h` aponta esse macro, e duas variantes adicionais, para
   `include/firmware/fw_sample.i`;
5. os comentários do próprio driver dizem que o sample é inválido e deve ser
   substituído pelo firmware do cliente/módulo.

O `sea.dts` também inclui `mediatek/touchscreen.dtsi`, que declara um painel
Focaltech e GPIOs de reset/IRQ. Isso torna a dependência relevante para o
`sea`, embora ainda não prove qual firmware corresponde a cada painel físico.

A árvore comunitária repete o caminho, mas o arquivo observado tem **zero
bytes**. Ele é um placeholder vazio, não um firmware compilável. Não há hash
de bytes de firmware, aviso de copyright específico ou licença de
redistribuição do firmware real. Portanto:

- não é legítimo criar um array falso ou aceitar arquivo vazio;
- não é legítimo desativar Focaltech no `VENDOR_REFERENCE` só para obter PASS;
- a redistribuição do firmware real permanece **não estabelecida / provável
  componente proprietário**;
- o bloqueador objetivo é obter uma fonte pública licenciada ou uma instrução
  legal de aquisição do firmware exato, sem extrair o aparelho nesta missão.

## DPMAIF / modem

`sea_defconfig` ativa `MTK_CCCI_DEVICES=y`, `MTK_MD1_SUPPORT=11` e
`MTK_ECCCI_DRIVER=y`. Os Makefiles do ECCCI incluem
`hif/ccci_hif_dpmaif.o` quando o driver modem está ativo. A falha observada
com `clang-r433403b` ocorre nos casts de debug nas linhas 453 e 466 de
`ccci_hif_dpmaif.c`:

```c
(u32)data_64ptr
(u32)data_8ptr
```

Clang diagnostica truncamento de ponteiro para inteiro e o código legado trata
o warning como erro. O Makefile pai de `drivers/misc/mediatek` aplica
`-Werror`; não foi encontrada uma flag vendor específica que torne esses
casts corretos. A árvore comunitária troca os casts por `long`, evidenciando
um patch posterior plausível, mas isso não é prova de que seja o patch Xiaomi
nem foi aplicado ao perfil de referência.

Logo, a causa é **incompatibilidade entre código vendor legado e diagnóstico
mais estrito do compilador, agravada por `-Werror`**, dentro de um caminho
modem/CCCI. Não é evidência de falha de hardware nem motivo para apagar o
driver da referência.

`SERVER_MINIMAL` pode futuramente estudar a desativação coerente de CCCI/MD1,
mas deve manter um delta de configuração separado, revalidar dependências de
USB/energia/thermal e nunca substituir o resultado de `VENDOR_REFERENCE`.

## Perfis e artefatos

O manifesto de reconstrução está em
[`devices/xiaomi-sea/reconstruction/manifest.json`](../devices/xiaomi-sea/reconstruction/manifest.json).

### `VENDOR_REFERENCE`

- baseline: Xiaomi `sea-t-oss` + `sea_defconfig` + `clang-r433403b`;
- patches nossos: nenhum aplicado;
- `cust.dtsi` comunitário: declarado externamente, não importado;
- `fw_sample.i`: ausente e não substituído;
- kernel completo: **BLOCKED**;
- módulos completos: **BLOCKED**;
- DTB: **BLOCKED**;
- DTBO candidato misto: **BUILT_UNTESTED**, 67.869 bytes,
  SHA-256 `34febe33284575825169a1b46f6f438491bd5f7ffd7931ed44dc746f0f1b01ab`;
- boot image: **BLOCKED**.

### `SERVER_MINIMAL`

Estado **DESIGN_ONLY**. Não há build nem artefato desse perfil; ele existe
somente para impedir que a finalidade de servidor seja usada como justificativa
para esconder as falhas do kernel vendor original.

## Licenças e cadeia estimada

Código do kernel oficial e comunitário é tratado como GPL conforme os arquivos
`COPYING`; o device tree comunitário declara Apache-2.0. A toolchain AOSP tem
Apache-2.0 e avisos de componentes. Firmware Focaltech, vendor shared objects,
`md1img.img`, chaves de teste e imagens stock não têm autorização de
redistribuição neste projeto e não foram incluídos.

Como estimativa de engenharia para uma cadeia Android vendor completa, não como
percentual de bytes: **70% código/fonte público oficial ou upstream, 15%
comunitário, 15% proprietário ou ainda não resolvido**. A incerteza está
concentrada justamente em firmware, vendor blobs, boot chain e `cust.dtsi`,
portanto essa estimativa não é uma declaração de suporte.

## Próximo bloqueador objetivo

O próximo bloqueador não é “mais um patch”: é fechar a procedência do contexto
vendor. A sequência mínima é obter uma versão licenciada e correspondente do
Focaltech `fw_sample.i`, reconstruir/validar os dois `cust.dtsi` com evidência
independente, e então repetir o build completo para separar falhas de código
de falhas de contexto. Até lá, `Recovery Readiness` permanece **BLOCKED** e
nenhuma operação de escrita no telefone é autorizada.
