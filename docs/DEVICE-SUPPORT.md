# Device Support Packages

Um DSP é o contrato mínimo para adicionar um aparelho sem copiar o Core.

## Arquivos mínimos

```text
devices/<vendor>-<codename>/
├── README.md
├── HARDWARE.md
├── BOOT.md
├── STATUS.md
└── device.json
```

Referencie artefatos por URL/origem, licença e SHA-256. Não faça commit de
firmware ou blobs só para tornar o pacote conveniente.

## Estados objetivos

- `RESEARCH`: identidade e fontes públicas em investigação; sem boot Topazio.
- `BOOTING`: há uma tentativa reproduzível de iniciar algum componente, mas
  não há contrato de serviços completo.
- `PARTIAL`: boot e uma parte relevante dos serviços funcionam, com limitações
  conhecidas e recuperação documentada.
- `SUPPORTED`: Core, rede/SSH, armazenamento, energia básica e recuperação
  foram validados para a versão declarada em hardware de teste.
- `STABLE`: duas ou mais execuções independentes, atualização/rollback
  ensaiados, logs publicados sem dados pessoais e nenhuma falha crítica aberta.

Um estado mais baixo deve ser usado quando uma regressão for descoberta.

## Processo

1. abrir issue com identidade e fontes;
2. reproduzir somente operações autorizadas e reversíveis;
3. escrever limitações e riscos;
4. adicionar testes de identidade e manifestos;
5. obter revisão antes de mudar o estado.
