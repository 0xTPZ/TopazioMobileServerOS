# Grafo DTS do Xiaomi `sea`

O grafo é produzido por `host-tools/dts_graph.py`. Ele resolve includes sem
alterar a fonte e marca qualquer include ausente como bloqueador.

```text
sea.dts (overlay /plugin/)
├── mediatek/touchscreen.dtsi
├── mediatek/cust_mt6781_fingerprint.dtsi
├── sea/cust.dtsi                         [AUSENTE na fonte oficial]
├── mediatek/cust_mt6781_camera.dtsi
├── mediatek/cust_foursemi_audio.dtsi
└── mediatek/cust_aw87xxx_audio.dtsi

k6781v1_64_k419.dts
├── k6781v1_64_k419/cust.dtsi             [AUSENTE na fonte oficial]
├── mediatek/cust_mt6781_camera.dtsi
└── mediatek/cust_mt6781_touch_1080x2300.dtsi
```

O arquivo comunitário
`arch/arm64/boot/dts/mediatek/sea/cust.dtsi` foi localizado no commit
`ae44e42c393b44b1534a7fcd7065366abe6bfe65`, SHA-256
`9ba54ed35a7ecb82c9b2d9ee5ed651162d8ca689174b0ca2ec29123189528216`.
Classificação: **STRONG_CANDIDATE**, não `CONFIRMED`. Ele tem relação direta
com `sea`/MT6781 e cabe no include ausente, mas não há prova de que seja o
mesmo snapshot vendor da fonte Xiaomi `6f6b84e…`; por isso não foi copiado.

Também há diferença material na árvore comunitária: ela inclui
`"sea/cust.dtsi"` e `cust_mt6781_sea_camera.dtsi`, enquanto a árvore oficial
usa `<sea/cust.dtsi>` e `cust_mt6781_camera.dtsi`. Isso impede chamar o
conjunto comunitário de reconstrução oficial.

Na busca da Missão 005 foi localizada uma única versão pública de
`sea/cust.dtsi` e nenhuma versão pública de
`k6781v1_64_k419/cust.dtsi`. Não há convergência independente de hashes. A
árvore Xiaomi também contém `drivers/misc/mediatek/dws/mt6785/sea.dws`, que é
um possível insumo do DrvGen, mas não substitui o artefato gerado nem prova a
licença/procedência do snapshot comunitário.

## DTB e DTBO

O `sea.dts` público é um overlay e a `arch/arm64/boot/dts/mediatek/Makefile`
oficial só lista targets `auto2712`. Assim, `make dtbs` não prova a geração do
device tree do telefone. Um DTB/DTBO só pode ser aceito depois que a origem
do `cust.dtsi`, o base DTS, as regras de overlay e o contexto vendor forem
reconciliados; um arquivo vazio ou gerado com outro modelo é inválido.

Como teste estático separado, o `sea.dts` oficial foi pré-processado com
Clang e o `cust.dtsi` comunitário foi fornecido somente como include externo.
O `dtc` gerou um overlay de 67.869 bytes, SHA-256
`34febe33284575825169a1b46f6f438491bd5f7ffd7931ed44dc746f0f1b01ab`.
Esse resultado é `DTBO_CANDIDATE / BUILT_UNTESTED`, não `CONFIRMED`: seus
warnings são esperados para um overlay sem base tree e a procedência mista
impede uso em boot image.
