# Camada de reconstrução controlada do `sea`

Esta pasta descreve a reconstrução sem modificar a árvore Xiaomi original:

```text
upstream Xiaomi limpo
+ componentes externos declarados
+ patches nossos explicitamente ordenados
= perfil reproduzível, quando a evidência permitir
```

O manifesto canônico é [`manifest.json`](manifest.json). Ele mantém dois
perfis independentes:

- `VENDOR_REFERENCE`: prioridade da Missão 005; continua `BLOCKED` porque os
  dois `cust.dtsi` não foram reconstruídos com prova suficiente e o firmware
  Focaltech de cliente não é público/licenciado.
- `SERVER_MINIMAL`: camada experimental `SOURCE_ONLY`; remove CCCI/DPMAIF
  apenas no fragmento externo depois da auditoria de configuração, sem
  mascarar falhas do perfil vendor.

A camada específica está em
[`../server-minimal/`](../server-minimal/), com fragmento, patch Focaltech,
grafo estruturado e plano de build. Ela preserva `VENDOR_REFERENCE` e nunca
aplica alterações diretamente ao checkout Xiaomi.

Nenhum arquivo de firmware, blob vendor, imagem de boot ou dump do telefone é
armazenado aqui. A lista estruturada de fontes, componentes, hashes e relações
está em [`../sources.json`](../sources.json).

## Missão 008 — device tree

[`dt-analysis.json`](dt-analysis.json) registra a auditoria formal dos dois
overlays oficiais, do `cust.dtsi` comunitário, do DTBO externo e da aplicação
offline sobre o candidato público `mt6781.dtb`. Os grafos transitiveis estão
em [`official-sea-dts-graph.json`](official-sea-dts-graph.json) e
[`official-k6781-dts-graph.json`](official-k6781-dts-graph.json), além da base
[`official-mt6781-base-dts-graph.json`](official-mt6781-base-dts-graph.json).

O resultado é `PARTIAL / DT_STRUCTURALLY_VALID`: o `sea` DTB stock, o contexto
`k6781v1_64_k419/cust.dtsi`, o layout de boot e a validação em hardware ainda
não foram provados.
