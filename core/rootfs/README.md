# Rootfs prototype

Este diretório descreve a configuração mínima esperada pelo Core. A imagem
ARM64 da Missão 002 é bootável no QEMU `virt` com Debian 13/trixie, mas isso
não é suporte de boot para um telefone: kernel, device tree, firmware,
partições e recuperação de cada aparelho continuam específicos.

`etc/topazio/feature-contract.json` registra, sem credenciais, o contrato
validado no QEMU: ARM64, hostname, usuário administrativo, SSH, Git, Python,
Node.js, SQLite, HTTP, métricas e o limite `qemu-virt-only`.
