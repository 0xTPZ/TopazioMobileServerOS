# Instruções de colaboração

## Escopo

Este repositório é o Topazio Mobile Server OS, projeto open source de 0xTPZ.
O Redmi Note 12S (`sea`) é o dispositivo de referência da pesquisa, não uma
declaração de suporte.

## Regras de segurança

- Trabalhar somente dentro do workspace do projeto.
- Nesta fase, não conectar comandos de escrita ao telefone.
- Nunca implementar bypass de FRP, contas, Secure Boot, bootloader ou proteção
  antifurto.
- Ferramentas de instalação devem abortar quando o modelo, transporte, imagem,
  hash ou estado de recuperação forem ambíguos.
- Não adicionar dumps, dados pessoais, chaves, credenciais, firmware ou blobs
  de licença incerta.
- Cada operação futura que possa gravar deve ter plano explícito, confirmação,
  log e caminho de recuperação.

## Qualidade

Antes de um commit, executar:

```text
python host-tools/verify_repo.py
python host-tools/secret_scan.py --working-tree
python -m unittest discover -s tests -v
git diff --check
```

Commits devem ser pequenos, descritivos e reversíveis. Não reescrever histórico
nem usar force push sem uma decisão documentada.
