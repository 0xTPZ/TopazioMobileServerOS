# Console touchscreen

## Princípio

A tela é um painel de status e um caminho de emergência, não um desktop. A
administração normal ocorre por SSH.

## Painel mínimo

```text
TOPAZIO MOBILE SERVER OS
Device / hostname / IP / SSH
CPU / RAM / storage / temperature / uptime
Network and recovery state
Open console   Reboot (future, guarded)   Help
```

O botão de reboot futuro deverá exigir confirmação e registrar o pedido. Não
existirá um botão de flash ou unlock na UI.

## Contrato

O Core fornece dados estruturados; a UI apenas renderiza. Eventos de toque
viram ações tipadas com política, autenticação e log. O teclado de emergência
deve aplicar allowlist de comandos, timeout e escape seguro. A especificação
visual atual está em `ui/console/README.md`.
