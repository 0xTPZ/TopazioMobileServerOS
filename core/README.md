# Core

O Core contém contratos portáveis do sistema: identidade, hostname, status,
logs, políticas, SSH e serviços básicos. Ele não contém um kernel de telefone
nem presume um Device Support Package específico.

O `status.py` é um protótipo de PC. Métricas indisponíveis aparecem como
`unknown`; isso é intencional para separar observação de hipótese.
