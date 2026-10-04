# Contribuindo

Topazio Mobile Server OS é mantido por 0xTPZ e recebe contribuições de
pesquisa, documentação, testes, Core e pacotes de suporte de dispositivos.

## Antes de abrir uma mudança

1. Leia `AGENTS.md`, `SECURITY.md` e a documentação do componente.
2. Não inclua dumps, dados pessoais, credenciais, firmware ou blobs de licença
   desconhecida.
3. Classifique afirmações técnicas como `CONFIRMED`, `INFERRED`, `UNKNOWN` ou
   `BLOCKED` e inclua a fonte ou o método de reprodução.
4. Mantenha mudanças focadas e evite misturar refatoração com pesquisa.

Execute localmente:

```text
python host-tools/verify_repo.py
python host-tools/secret_scan.py --working-tree
python -m unittest discover -s tests -v
git diff --check
```

## Dispositivos

Um novo telefone deve entrar como pacote independente em `devices/<vendor>-<codename>`.
Comece em `RESEARCH`; só use `BOOTING`, `PARTIAL`, `SUPPORTED` ou `STABLE`
quando os critérios objetivos em `docs/DEVICE-SUPPORT.md` forem atendidos.
Não declare suporte com base em semelhança de SoC ou em um kernel de outro
modelo.

## Pull requests

Descreva objetivo, evidências, riscos, testes e impacto de recuperação. Mudanças
que poderiam escrever em USB, partições ou boot chain exigem revisão explícita
e testes simulados; esta base não aceita bypass de segurança.
