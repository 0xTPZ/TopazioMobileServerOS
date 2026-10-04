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
