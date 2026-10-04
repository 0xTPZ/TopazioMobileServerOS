# Handoff

## Estado no fim da Missão 003

O repositório contém um build automatizado de Debian 13/trixie arm64, serviços
Topazio, scripts QEMU, validação de manifesto, testes e DSP de pesquisa para
`xiaomi-sea`. O smoke test local iniciou o kernel/initramfs no QEMU `virt`,
detectou ARM64, exibiu `TOPAZIO_BOOT_OK`, respondeu HTTP e aceitou SSH por
chave no usuário `admin`.

Isso é **PARTIAL**: o artefato é validado somente em QEMU/TCG. Não há suporte
de boot para o telefone, procedimento de flash, unlock ou imagem para `sea`.

A Missão 003 fixou a fonte oficial `sea-t-oss` e confirmou o `sea_defconfig`,
mas o DTS público é overlay com include vendor ausente, o Makefile não possui
alvo `sea` e o build GCC 13 para em `kernel/sched/tune.c`. O manifest v2,
matriz de capabilities, host probe e recovery check estão no repositório; o
pipeline bloqueia sem kernel/DTB/boot image reais, hashes e DSP instalável.

## Como continuar com segurança

1. revisar o commit e o CI público;
2. reproduzir `scripts/build-arm64.sh` e `scripts/smoke-qemu.sh` em WSL;
3. preservar o manifesto e os logs do artefato como evidência do laboratório;
4. manter `devices/xiaomi-sea/STATUS.md` em `RESEARCH`;
5. não iniciar a Missão 004, unlock, flash ou qualquer escrita no telefone sem
   nova autorização e pré-condições de recuperação.

## Perguntas abertas

- qual transporte USB oficial estará disponível no Windows para consultas?
- qual árvore vendor completa e toolchain reproduzem kernel+DTB do aparelho?
- qual imagem/kernel legalmente redistribuível pode inicializar o aparelho?
- como preservar energia, Wi-Fi, UFS, display e touch fora do Android?
- qual modelo de atualização e rollback será seguro?
