# Recovery e anti-brick

## Regra padrão

O Installer desta fase só detecta, coleta metadados, valida manifestos e gera
planos. Ele não executa `flash`, `erase`, `format`, `unlock`, escrita de
partição ou comandos de bypass.

## Pré-condições para uma futura gravação

1. identidade do aparelho confirmada por múltiplos sinais;
2. DSP explicitamente compatível e versão exata selecionada;
3. bootloader/transportes documentados por fonte oficial ou evidência
   reproduzível;
4. backup externo verificado e procedimento de retorno ensaiado;
5. cada artefato com origem, licença e SHA-256;
6. partições permitidas enumeradas; nenhuma partição desconhecida;
7. energia, cabo, conexão e espaço validados;
8. confirmação humana específica para a operação;
9. log append-only/exportável da operação;
10. verificação pós-operação e caminho de rollback.

Qualquer item ausente produz `BLOCKED`/`ABORTED`.

## O que registrar

Identidade pública do modelo/codename, versão de ferramentas, hashes,
timestamp, modo USB, resultado de cada pré-condição e resultado de cada etapa.
Remover serial, IMEI, contas e dados pessoais antes de publicar.

## Recuperação do `sea`

A auditoria de 04/10/2026 encontrou uma interface MediaTek com erro de driver
28 e nenhum dispositivo no `adb`/`fastboot`. Bootloader e partições ficaram
`UNKNOWN`. Portanto este repositório não inclui uma imagem, não define um
procedimento de flash e não declara o telefone recuperável pelo Installer.
