# Serviços

Serviços devem ser pequenos, observáveis e desativáveis. Cada serviço precisa
de um contrato de configuração, política de bind/auth, health check e teste.
O primeiro é um HTTP de diagnóstico local; não é uma API de produção. Na
imagem QEMU da Missão 002, `topazio-status`, `topazio-metrics`, `topazio-http`
e `topazio-console` são unidades systemd separadas.
