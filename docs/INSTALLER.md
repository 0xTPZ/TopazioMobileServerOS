# Topazio Mobile Installer

## Fluxo

```text
detect -> identify -> diagnose -> support-check -> recovery-readiness
       -> prepare-plan -> (future explicit install) -> verify -> report
```

O estágio executável atual termina no plano. O comando deve ser idempotente,
legível e seguro quando não há telefone conectado.

## Estados de parada

- `NO_DEVICE`: nenhum transporte detectado;
- `AMBIGUOUS_IDENTITY`: sinais conflitantes;
- `UNSUPPORTED`: nenhum DSP compatível;
- `BLOCKED_RECOVERY`: não há caminho de recuperação comprovado;
- `BLOCKED_SECURITY`: bootloader/proteção exige ação autorizada fora do
  Installer;
- `ABORTED`: pré-condição ou hash inválido.

O Installer nunca tenta desbloquear, remover conta, contornar FRP/Family Link,
desativar Secure Boot ou forçar INF/driver.

## Plataforma

A primeira implementação é CLI Python no Windows. A lógica de decisão é
separada do transporte para permitir adaptadores Linux/macOS futuramente. Uma
GUI pode apenas chamar o mesmo plano e mostrar o mesmo log; não deve possuir
um caminho privilegiado próprio.
