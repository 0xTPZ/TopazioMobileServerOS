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
