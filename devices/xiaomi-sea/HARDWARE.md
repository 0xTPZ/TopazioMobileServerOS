# Hardware — `sea`

## CONFIRMED por fontes públicas/auditoria

- CPU ARM64, oito núcleos no Helio G96/MT6781;
- GPU Mali-G57;
- variantes comerciais de 6/8 GB RAM e 128/256 GB UFS 2.2;
- microSD, Wi-Fi 2.4/5 GHz, Bluetooth 5.2, USB-C/OTG e 4G;
- bateria nominal de 5000 mAh.

O SKU, partições, revisão de placa, sensores exatos e estado físico desta
unidade são `UNKNOWN`. A configuração de UFS, Wi-Fi, USB, energia, display e
touch no kernel oficial é `SOURCE_AVAILABLE`, não `WORKING`; nenhum periférico
foi testado no telefone.

A matriz formal está em [`capabilities.json`](capabilities.json) e o relatório
de enablement em [`docs/HARDWARE-ENABLEMENT.md`](../../docs/HARDWARE-ENABLEMENT.md).

## Implicações para o Core

CPU, RAM e armazenamento parecem adequados para workloads de laboratório, mas
rede, energia, suspensão, USB, display/touch e firmware dependem do kernel,
device tree e blobs compatíveis. GPU e modem não são requisitos do primeiro
protótipo de servidor.
