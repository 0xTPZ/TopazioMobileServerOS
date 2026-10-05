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
| `adb shell ls -l /dev/block/by-name` | READ_ONLY_SAFE | nomes de partições expostos pelo Android |
| `fastboot getvar product` | READ_ONLY_SAFE | identidade no bootloader |
| `fastboot getvar current-slot` | READ_ONLY_SAFE | slot ativo |
| `fastboot getvar slot-count` | READ_ONLY_SAFE | quantidade de slots |
| `fastboot getvar unlocked` | READ_ONLY_SAFE | estado publicado do bootloader |
| `fastboot getvar all` | READ_ONLY_SAFE | metadados padrão do bootloader |

`fastboot getvar all` deve ser tratado como saída potencialmente sensível e
armazenado somente como evidência local autorizada. O plano não inclui
`fastboot boot`, ainda que a ação fosse temporária, porque isso mudaria o
estado de execução e não é necessário para o inventário inicial.

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
