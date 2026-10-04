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
  ├─ status/métricas, logs e políticas
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

## Contratos DSP

Cada DSP deve fornecer uma identidade única, lista de estados suportados,
artefatos referenciados por hash, requisitos de boot, transporte, recuperação e
licença. O Core consome metadados; não duplica todo o sistema por aparelho.

## Fluxo de estado

`RESEARCH -> BOOTING -> PARTIAL -> SUPPORTED -> STABLE`.

Avanço exige evidência adicional e revisão. Regressão para `BLOCKED` é válida a
qualquer momento quando a recuperação ou a reprodução deixa de ser confiável.
