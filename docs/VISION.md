# Visão

## Problema

Smartphones antigos frequentemente conservam CPU ARM64, RAM, flash, Wi-Fi,
USB, bateria e tela depois de deixarem de servir como telefones. O projeto
quer transformar esse hardware em pequenos servidores recuperáveis e úteis.

## Experiência desejada

Após uma instalação suportada, a administração principal será remota por SSH.
A tela local exibirá identidade, IP, saúde, temperatura, armazenamento e um
console/teclado mínimo para emergência. Não haverá launcher, Play Store,
discador, SMS ou aplicações de consumidor como parte do produto.

## Não objetivos

- substituir Android em qualquer modelo sem suporte comprovado;
- contornar proteções do fabricante ou do usuário;
- prometer desempenho, segurança física ou disponibilidade de servidor;
- incluir firmware proprietário no repositório;
- exigir uma interface gráfica tradicional.

## Princípios

Estabilidade, recuperação, rede, SSH, armazenamento, baixo consumo e
compatibilidade precedem aceleração gráfica. Toda capacidade específica de
hardware deve estar atrás de um contrato do Device Support Package.
