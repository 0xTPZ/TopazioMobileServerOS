# Build

## Protótipo atual

O protótipo não é uma imagem bootável. Ele é um conjunto de scripts Python sem
dependências externas que demonstra contratos do Core em qualquer PC com Python
3.11+.

```text
python host-tools/verify_repo.py
python host-tools/secret_scan.py --working-tree
python -m unittest discover -s tests -v
python services/http/topazio_http.py --once
python host-tools/build_rootfs.py --output build/out/rootfs-manifest.json
```

O último comando gera apenas um manifesto JSON determinístico. `build/out/` é
ignorado e não deve receber imagens, firmware ou dumps.

## Futura imagem ARM64

Ainda faltam: toolchain/reprodutibilidade, base userspace licenciada, init,
kernel/DT, firmware permitido, boot chain, layout de partições, assinatura,
prova em dispositivo e recuperação/rollback. QEMU será usado quando houver um
kernel e uma máquina virtual adequados; sua execução não prova compatibilidade
com um telefone.

## Dependências

Não instalar dependências pesadas nesta missão. O CI usa Python 3.12 padrão e
`unittest`. Dependências futuras devem ter licença, hash, origem e justificativa
registrados.
