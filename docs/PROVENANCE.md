# Proveniência da reconstrução `sea`

O registro canônico está em
[`devices/xiaomi-sea/provenance.json`](../devices/xiaomi-sea/provenance.json).
O banco de pesquisa ampliado, com classificações, relações, hashes e política
de redistribuição, está em
[`devices/xiaomi-sea/sources.json`](../devices/xiaomi-sea/sources.json).

| Componente | Origem / ref | Uso | Redistribuição no projeto |
|---|---|---|---|
| kernel Xiaomi | oficial, `sea-t-oss`, `6f6b84e…` | baseline de kernel/DTS | somente fonte pública, sem blobs |
| Clang | Android Open Source, `android-s-v2-beta-2`, `0625305…` | perfil `build.config.mtk.aarch64.tiramisu` | não versionado; hash exigido |
| GCC | perfil vendor `6.3.1` | fallback legado | não versionado |
| kernel MT6781 comunitário | `mt6781-sea`, `ae44e42…` | comparação e candidato `cust.dtsi` | não copiado |
| device tree comunitária | `mt6781-sea`, `5bb6ea2…` | estudo de offsets e partições | não copiada; blobs não incluídos |

O `cust.dtsi` comunitário é `STRONG_CANDIDATE`, não `CONFIRMED`. O arquivo
não foi incorporado ao kernel oficial. O candidato DTBO gerado na pesquisa
usa esse include externo, tem SHA-256 registrado na documentação DTS e não
pode ser empacotado ou gravado no telefone.

Firmware, `proprietary-files.txt`, `proprietary-firmware.txt`, chaves AVB e
imagens stock não entram no repositório sem origem, hash da unidade e licença
adequada.
