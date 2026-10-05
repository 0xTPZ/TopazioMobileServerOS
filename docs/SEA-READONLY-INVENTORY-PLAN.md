# SEA — plano de inventário futuro somente leitura

Este documento é um plano, não um registro de execução. Na Missão 011 nenhum
comando ADB ou fastboot foi executado e não houve interação com o telefone.

## Limites

- objetivo: confirmar identidade da unidade, slots, memória, partições,
  mounts, kernel em execução e disponibilidade de metadados;
- permitido: consultas que apenas enumeram ou leem propriedades publicadas pelo
  Android/bootloader;
- proibido: `adb push`, `dd`, `adb reboot`, `fastboot flash`, `erase`, `format`,
  `boot`, desbloqueio, leitura BROM/preloader bruto, dumps de partição e
  qualquer remoção de AVB/verity;
- a execução depende de autorização separada, transporte disponível e registro
  da saída completa com timestamp, sem alterar o estado da unidade.

## Comandos planejados

| Comando | Classe | Finalidade |
|---|---|---|
| `adb devices` | READ_ONLY_SAFE | presença do transporte |
| `adb get-state` | READ_ONLY_SAFE | estado do ADB |
| `adb shell getprop` | READ_ONLY_SAFE | identidade, build e propriedades de boot |
| `adb shell uname -a` | READ_ONLY_SAFE | release do kernel em execução |
| `adb shell cat /proc/meminfo` | READ_ONLY_SAFE | inventário de RAM publicado pelo kernel |
| `adb shell cat /proc/partitions` | READ_ONLY_SAFE | blocos lógicos publicados |
| `adb shell cat /proc/mounts` | READ_ONLY_SAFE | mounts e locais de módulos |
| `adb shell cat /proc/modules` | READ_ONLY_SAFE | nomes de módulos atualmente carregados |
| `adb shell ls -l /dev/block/by-name` | READ_ONLY_SAFE | nomes de partições expostos pelo Android |
| `adb shell cat /sys/class/thermal/thermal_zone0/type` | READ_ONLY_SAFE | identidade térmica pública |
| `adb shell cat /sys/class/thermal/thermal_zone0/temp` | READ_ONLY_SAFE | leitura térmica pública |
| `adb shell cat /sys/class/power_supply/battery/status` | READ_ONLY_SAFE | estado de charging |
| `adb shell cat /sys/class/power_supply/battery/technology` | READ_ONLY_SAFE | tecnologia da bateria |
| `adb shell cat /sys/class/power_supply/battery/capacity` | READ_ONLY_SAFE | capacidade percentual |
| `adb shell cat /sys/block/sda/size` | READ_ONLY_SAFE | capacidade pública em setores |
| `adb shell cat /sys/block/sda/queue/logical_block_size` | READ_ONLY_SAFE | tamanho de bloco lógico |
| `adb shell cat /sys/block/sda/device/vendor` | READ_ONLY_SAFE | fornecedor UFS público |
| `adb shell cat /sys/block/sda/device/model` | READ_ONLY_SAFE | modelo UFS público |
| `adb shell cat /sys/block/sda/device/rev` | READ_ONLY_SAFE | revisão UFS pública |
| `adb shell cat /sys/class/net/wlan0/device/uevent` | READ_ONLY_SAFE | metadata do driver Wi-Fi |
| `adb shell cat /sys/class/net/usb0/device/uevent` | READ_ONLY_SAFE | metadata do driver USB de rede |
| `adb shell cat /sys/class/drm/card0/device/uevent` | READ_ONLY_SAFE | metadata do driver de display |
| `fastboot devices` | READ_ONLY_SAFE | enumeração sem reiniciar o aparelho |
| `fastboot getvar product` | READ_ONLY_SAFE | identidade no bootloader |
| `fastboot getvar variant` | READ_ONLY_SAFE | variante exposta |
| `fastboot getvar current-slot` | READ_ONLY_SAFE | slot ativo |
| `fastboot getvar slot-count` | READ_ONLY_SAFE | quantidade de slots |
| `fastboot getvar unlocked` | READ_ONLY_SAFE | estado publicado do bootloader |
| `fastboot getvar secure` | READ_ONLY_SAFE | estado de segurança exposto |

O plano não inclui `fastboot getvar all` nem `fastboot boot`, ainda que a ação
fosse temporária, porque isso amplia a coleta/superfície e poderia mudar o
estado de execução.

## Critérios de parada

Parar e não tentar recuperação se houver qualquer pedido de confirmação de
desbloqueio, escrita, reboot, dump, leitura bruta de partição, BROM/preloader,
ou se a identidade `sea`/modelo não for coerente. O resultado esperado desta
etapa é somente um inventário; ele não autoriza gerar, assinar, inicializar ou
instalar imagem.

## Ferramenta de classificação

`host-tools/device_command_safety.py` classifica a lista sem executar nenhum
comando. A classificação é uma barreira estática auxiliar, não uma garantia de
segurança do shell; qualquer comando fora da lista deve ser revisado
manualmente.

## Resultado da Missão 012-B

As Platform Tools foram encontradas em
`C:\AndroidTools\platform-tools`, mas `adb devices` e `fastboot devices`
retornaram listas vazias. O Windows expôs o telefone somente como WPD/MTP;
nenhum comando shell, `getvar` ou escrita foi executado. O relatório
sanitizado está em
`devices/xiaomi-sea/firmware-forensics/mission-012b.json`.
