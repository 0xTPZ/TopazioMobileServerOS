# Handoff

## Estado no fim da Missão 001

O repositório contém documentação, guardrails, protótipos de PC, testes e DSP
de pesquisa para `xiaomi-sea`. Não há imagem ARM64 nem procedimento de flash.

## Como continuar com segurança

1. revisar o commit e o CI público;
2. executar a Missão 002 somente com Android intacto;
3. coletar evidência adicional sem instalar driver incompatível ou forçar INF;
4. atualizar `devices/xiaomi-sea/STATUS.md` apenas com logs sanitizados;
5. não iniciar unlock/flash sem uma missão separada, autorização explícita e
   recuperação verificada.

## Perguntas abertas

- qual transporte USB oficial estará disponível no Windows para consultas?
- qual imagem/kernel legalmente redistribuível pode inicializar o aparelho?
- como preservar energia, Wi-Fi, UFS, display e touch fora do Android?
- qual modelo de atualização e rollback será seguro?
