# Topazio Mobile Server OS

Topazio Mobile Server OS é um projeto open source de 0xTPZ para reaproveitar
smartphones ARM64 antigos como pequenos servidores administráveis por SSH.

O objetivo não é criar outro Android de consumo. A experiência final deve ser
um aparelho com interface local mínima, console de emergência e serviços Linux
remotos: SSH, Git, Python, Node.js, SQLite, HTTP/API e aplicações do usuário.

## Estado atual

**RESEARCH / protótipo de PC — não há suporte de boot publicado.**

O Redmi Note 12S (`sea`) é o `REFERENCE DEVICE #001`. A auditoria local
confirmou o modelo e o ecossistema MediaTek/vendor, mas não confirmou o
bootloader nem uma interface fastboot funcional. Nenhuma partição foi alterada,
nenhum unlock foi tentado e nenhum flash foi executado.

O que é executável hoje:

- protótipo de status e métricas em Python, sem dependências externas;
- serviço HTTP local com `/healthz`, `/status` e `/metrics`;
- planejador de instalação somente leitura, com abortos por ambiguidade;
- relatório de recovery-readiness e scanner básico contra segredos/artefatos;
- testes de contrato e validação de documentação.

## Arquitetura em camadas

```text
Topazio Mobile Server OS
├── Core: contratos de serviços, rootfs, status, SSH e políticas
├── Device Support Package: boot, kernel/DT, firmware permitido e quirks
├── Installer: detecção, diagnóstico, plano, verificação e abortos seguros
├── Recovery: inventário, hashes, logs e readiness sem gravação implícita
└── UI local: painel/console mínimo e teclado de emergência
```

A decisão atual é híbrida: desenvolver contratos de um userspace Linux ARM64
portátil, validar o Core primeiro em PC e usar Android/Termux como caminho
inicial reversível para laboratório. Um boot nativo exigirá um Device Support
Package comprovado; não é inferido apenas por a CPU ser ARM64.

## Estrutura

- [`core/`](core/): contratos e protótipo do rootfs.
- [`services/`](services/): serviços mínimos, começando pelo HTTP.
- [`installer/`](installer/): arquitetura do Topazio Mobile Installer.
- [`recovery/`](recovery/): modelo anti-brick e readiness.
- [`host-tools/`](host-tools/): verificações executadas no PC.
- [`ui/`](ui/): protocolo da interface local mínima.
- [`devices/xiaomi-sea/`](devices/xiaomi-sea/): pesquisa do Redmi Note 12S.
- [`docs/`](docs/): visão, arquitetura, roadmap, pesquisa e handoff.

## Segurança e escopo

O instalador nunca deve contornar FRP, Family Link, contas, Secure Boot,
bootloader bloqueado ou proteções antifurto. Um aparelho não suportado, uma
imagem de outro modelo, um hash ausente ou um estado ambíguo devem parar o
fluxo. Firmware proprietário e blobs sem licença de redistribuição não fazem
parte deste repositório.

Leia [`SECURITY.md`](SECURITY.md), [`AGENTS.md`](AGENTS.md) e
[`docs/RECOVERY.md`](docs/RECOVERY.md) antes de trabalhar em código de host.

## Desenvolvimento

Requisitos para o protótipo: Git e Python 3.11+; não é necessário QEMU, Android
SDK ou dependência pesada para executar as verificações iniciais.

```text
python host-tools/verify_repo.py
python host-tools/secret_scan.py --working-tree
python -m unittest discover -s tests -v
python services/http/topazio_http.py --once
```

Contribuições são bem-vindas. Consulte [`CONTRIBUTING.md`](CONTRIBUTING.md) e
o guia de criação de Device Support Package em
[`docs/DEVICE-SUPPORT.md`](docs/DEVICE-SUPPORT.md).

## Licença

Código original: Apache License 2.0. Componentes de terceiros mantêm suas
licenças originais; esta licença não relicencia kernel, drivers, firmware,
blobs ou código externo. A decisão está registrada em
[`DECISOES.md`](DECISOES.md).
