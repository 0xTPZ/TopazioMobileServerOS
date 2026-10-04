# Roadmap

## Missão 001 — fundação (esta versão)

- [x] workspace isolado, Git e guardrails;
- [x] Core/DSP, Installer, UI e Recovery documentados;
- [x] protótipo Python de status, HTTP e plano somente leitura;
- [x] pesquisa sanitizada do Redmi Note 12S;
- [x] testes, secret scan, validação de docs e CI;
- [x] checkpoint público no GitHub.

## Missão 002 — laboratório reversível

- validar Termux/SSH sem substituir Android;
- coletar métricas de rede, temperatura, bateria, I/O e suspensão;
- melhorar diagnóstico USB com fonte oficial e somente consultas;
- definir backup externo e procedimento de recuperação manual.

## Missão 003 — imagem de desenvolvimento

- produzir rootfs ARM64 reproduzível em PC/CI;
- testar em QEMU ou placa compatível, sem inferir suporte ao `sea`;
- assinar manifestos e testar atualização/rollback em ambiente descartável.

## Missão 004 — pesquisa de boot do `sea`

- confirmar estado do bootloader por caminho oficial;
- localizar documentação e código publicamente redistribuíveis;
- testar somente em hardware dedicado com recuperação verificada;
- classificar cada periférico como funcional, parcial ou bloqueado.

## Horizonte

Containerização real, UI touchscreen nativa, múltiplos DSPs, builds Linux/macOS
do Installer e suporte estável só entram após a base de recuperação e rede.
