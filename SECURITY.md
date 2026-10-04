# Segurança

## Princípios

- O telefone é um alvo potencialmente destrutivo: o padrão é somente leitura.
- O instalador deve falhar fechado diante de modelo, transporte, hash, licença
  ou caminho de recuperação desconhecido.
- Nenhum componente deve contornar FRP, contas, Family Link, Secure Boot,
  bootloader ou proteção antifurto.
- Não guardar tokens, chaves privadas, dumps, identificadores pessoais,
  firmware proprietário ou blobs sem licença clara.

## Relato responsável

Não publique uma vulnerabilidade envolvendo credenciais ou uma cadeia de boot
antes de coordenar uma correção. Abra um issue privado ou contate o mantenedor
0xTPZ com reprodução mínima, impacto, versão/commit e mitigação sugerida.

Não envie segredos reais para issues. Use dados sintéticos.

## Scanner e hooks

`host-tools/secret_scan.py` procura padrões de chaves, tokens comuns, arquivos
proibidos e arquivos grandes. Ele é uma barreira auxiliar, não substitui revisão
humana. Um checkout pode instalar o hook opcional com:

```text
git config core.hooksPath .githooks
```

O CI executa o mesmo scanner e os testes. Um falso positivo deve ser removido
por alteração de código/documentação, não por desabilitar a proteção global.
