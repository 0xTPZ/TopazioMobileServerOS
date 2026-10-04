# Manifesto de Device Support Package

O contrato v2 está em
[`devices/schema/device-manifest.schema.json`](../devices/schema/device-manifest.schema.json).
O manifesto de referência está em
[`devices/xiaomi-sea/device.json`](../devices/xiaomi-sea/device.json).

## Regras

Um DSP precisa declarar, no mínimo:

- identidade comercial, codename e arquitetura;
- SoC e base Android com estado de evidência;
- repositório, branch, commit, defconfig e DTS do kernel;
- firmware requerido como lista explícita, inclusive quando ainda desconhecido;
- cadeia de boot e contrato de partições, incluindo desconhecidos explícitos;
- matriz de capabilities com `UNKNOWN`, `SOURCE_AVAILABLE`, `BUILDABLE`,
  `BOOT_TEST_REQUIRED`, `WORKING`, `BROKEN` ou `NOT_REQUIRED`;
- pré-condições de recovery e inputs do pipeline de artefatos;
- `support_state` e `installable` independentes da existência do código-fonte.

`CONFIRMED` significa evidência observada ou fonte primária reproduzível;
`INFERRED` é hipótese técnica; `UNKNOWN` não foi medido; `BLOCKED` depende de
transporte, arquivo, permissão ou pré-condição ausente.

## Estado do `sea`

O manifest é deliberadamente conservador: o kernel vendor existe, mas o build
de dispositivo está bloqueado, o boot chain/partições estão desconhecidos, a
recovery-readiness está bloqueada e `installable` permanece `false`. A matriz
separa “há código/configuração” de “funciona na unidade”.

## Ferramentas de host

- `python host-tools/host_probe.py --fixture arquivo.json`: avalia uma
  observação sanitizada sem tocar USB;
- `python host-tools/recovery_check.py --device xiaomi-sea`: mostra o que falta
  para recovery readiness;
- `python host-tools/device_artifact_pipeline.py`: exige paths explícitos e
  bloqueia o DSP atual;
- `scripts/build-sea-kernel.sh`: build PC-only, out-of-tree e diagnosticado.

Nenhuma dessas ferramentas instala driver, abre transporte, desbloqueia,
flasha ou grava partições.
