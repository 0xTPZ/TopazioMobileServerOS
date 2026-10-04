# Decisões técnicas

## 001 — Arquitetura híbrida e separação Core/DSP

**Status:** aceita para a Missão 001.

O Core define contratos de userspace Linux ARM64, status, serviços, políticas
de instalação e recuperação. Cada aparelho recebe um Device Support Package
(DSP) com identidade, boot chain, kernel/DT, firmware permitido e limitações.

Escolhemos um caminho híbrido por causa da auditoria do `sea`: a Xiaomi publica
uma árvore vendor Android (`sea-t-oss`), enquanto não há evidência de suporte
mainline completo para todos os periféricos. Android/Termux é reversível e
permite provar SSH, Git, Python, Node.js, SQLite e HTTP sem apagar o aparelho.
Linux nativo continua como objetivo de pesquisa, condicionado a boot, drivers,
firmware e recuperação comprovados.

**Alternativas rejeitadas nesta fase:** inventar kernel novo; declarar Debian
arm64 bootável só pela CPU; flash nativo no telefone; copiar firmware para o
repositório.

## 005 — Primeiro alvo executável: Debian arm64 em QEMU

**Status:** aceita para a Missão 002.

O primeiro artefato executável é um userspace Debian 13/trixie arm64 com
systemd, kernel Debian arm64, initramfs, SSH, Git, Python, Node.js, SQLite e
os quatro serviços Topazio. O transporte de validação é a máquina virtual
genérica `virt` do QEMU com TCG, disco virtio e rede user-mode. O processo
gera um manifesto com a lista de pacotes e hashes e termina com smoke test
de console, HTTP e SSH.

Essa decisão prova um produto executável do Core sem transformar a prova de
QEMU em alegação de compatibilidade com o `sea`. O artefato não é gravado no
telefone e imagens grandes permanecem fora do repositório.

## 006 — Build nativo no WSL e armazenamento de chaves de teste

**Status:** aceita para a Missão 002.

O rootfs é construído em `/tmp` dentro do WSL e somente os resultados são
exportados para `build/out/arm64`. Isso evita colisões de nomes entre arquivos
case-sensitive durante a montagem em `E:`. O smoke test mantém a chave
privada efêmera em `/tmp` Linux, pois o OpenSSH rejeita chaves armazenadas em
um caminho Windows montado com permissões efetivas `0777`.

## 002 — Licença

Código original sob Apache-2.0, uma licença permissiva compatível com a
preferência do projeto. Cada terceiro continua sob sua licença; kernel e
componentes GPL não são relicenciados. SPDX e avisos de terceiros serão
adicionados quando componentes forem incorporados.

## 003 — Instalador fail-closed

O instalador começa como planejador somente leitura. Detecção, suporte,
recovery-readiness, hash e confirmação são pré-condições separadas. Qualquer
ambiguidade produz `ABORTED`; não há caminho automático de bypass ou gravação.

## 004 — Evidência explícita

Documentação diferencia `CONFIRMED`, `INFERRED`, `UNKNOWN` e `BLOCKED`. Uma
hipótese de comunidade nunca vira afirmação de suporte sem logs reproduzíveis.

## 007 — Fonte oficial e pipeline fail-closed do `sea`

**Status:** aceita para a Missão 003.

O DSP fixa `sea-t-oss` e seu commit oficial, mas mantém `RESEARCH` porque a
fonte pública não forma um kernel+DTB autônomo, o boot chain/partições da
unidade não foram observados e o recovery-readiness está bloqueado. O pipeline
aceita apenas artefatos explícitos e hashados; nunca monta um `boot.img`
inventado nem grava no telefone. O build usa `O=` fora da árvore-fonte e
registra falhas como diagnóstico reproduzível.

## 008 — Perfil `SERVER_MINIMAL` do `sea`

**Status:** aceita para a Missão 006, `PARTIAL / BLOCKED`.

O contrato genérico `TOPAZIO_SERVER_PROFILE` exige CPU/SMP, RAM, timers,
interrupções, UFS, USB, Wi-Fi/rede, bateria, charging, thermal, display,
touch/input, filesystem e console/SSH. O perfil `SERVER_MINIMAL` parte de
`sea_defconfig` e vive numa camada externa auditável. Ele desabilita somente
CCCI/ECCCI/DPMAIF/MD1, pois conectividade celular não é requisito do primeiro
produto servidor; `VENDOR_REFERENCE` permanece imutável e `BLOCKED`.

O `fw_sample.i` ausente não é tratado como firmware falso. A evidência do
driver separa a leitura de touch/input da atualização automática: o trabalho
de auto-upgrade retorna quando `FTS_AUTO_UPGRADE_EN=0`. Por isso a camada
SERVER_MINIMAL desabilita apenas essa atualização embutida e preserva
`CONFIG_TOUCHSCREEN_FTS`, sem redistribuir bytes proprietários.

O perfil não autoriza inventar DTB, GPIO, regulador, phandle, blob Wi-Fi ou
`boot.img`. Kernel completo, módulos e DTB continuam bloqueados neste
checkpoint; nenhuma escrita física, recovery ou operação de boot foi feita.
