# Rootfs prototype

Este diretório é um esqueleto de rootfs e não uma imagem bootável. Os arquivos
descrevem configuração mínima esperada pelo Core. A montagem de uma imagem
ARM64 exige uma base licenciada, init, kernel, device tree, firmware permitido
e validação em hardware/VM apropriado.

`etc/topazio/feature-contract.json` registra, sem credenciais, a demonstração
conceitual de ARM64, hostname, usuário administrativo, SSH, Git, Python,
Node.js, SQLite, HTTP e métricas.
