# Arquitetura

## Camadas

```text
PC / Topazio Mobile Installer
  ├─ detecta e identifica (somente leitura)
  ├─ verifica suporte e recovery-readiness
  └─ gera plano; qualquer estado ambíguo aborta

Device Support Package
  ├─ identidade e estado de suporte
  ├─ boot/kernel/device tree referenciados
  ├─ firmware permitido por licença
  └─ limitações, hashes e método de recuperação

Core
  ├─ rootfs e contratos de serviço
  ├─ SSH, usuário administrativo e hostname
  ├─ status/métricas, HTTP de diagnóstico, console serial e logs
  └─ APIs locais estáveis

UI local mínima
  ├─ painel de saúde
  ├─ console administrativo
  └─ teclado touchscreen de emergência
```

## Estratégia de sistema

O alvo conceitual do Core é um userspace Linux ARM64 com init mínimo, SSH,
Git, Python, Node.js, SQLite e serviços HTTP. A primeira validação roda no PC
com Python padrão. No aparelho de referência, o caminho de laboratório é
Android/Termux sobre o sistema intacto, pois é reversível e respeita a
limitação observada na auditoria.

Um futuro boot nativo pode usar kernel/vendor Android e userspace Topazio, ou
um kernel mainline se os componentes forem comprovados. O Core não pressupõe
que um kernel de outro modelo funcione.

## Artefato executável da Missão 002

O caminho validado no laboratório é:

```text
debootstrap arm64/trixie
  -> systemd + kernel Debian + initramfs
  -> /opt/topazio e unidades systemd
  -> disco ext4 + manifesto de hashes
  -> QEMU virt / virtio / user-net
  -> console: TOPAZIO_BOOT_OK
  -> HTTP: /healthz, /status, /metrics
  -> SSH: usuário admin com chave injetada no smoke
```

O `topazio-http` escuta em `0.0.0.0:8787` dentro do laboratório QEMU e é um
diagnóstico sem autenticação própria; a administração continua sendo por SSH.
O arquivo [`docs/QEMU-LAB.md`](QEMU-LAB.md) define a fronteira entre essa
prova e o suporte ainda não confirmado ao telefone.

## Contratos DSP

Cada DSP deve fornecer uma identidade única, lista de estados suportados,
artefatos referenciados por hash, requisitos de boot, transporte, recuperação e
licença. O Core consome metadados; não duplica todo o sistema por aparelho.

## Fluxo de estado

`RESEARCH -> BOOTING -> PARTIAL -> SUPPORTED -> STABLE`.

Avanço exige evidência adicional e revisão. Regressão para `BLOCKED` é válida a
qualquer momento quando a recuperação ou a reprodução deixa de ser confiável.
