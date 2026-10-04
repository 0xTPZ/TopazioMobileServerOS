# Build

## Verificações rápidas

O contrato Python e os validadores não têm dependências externas além de
Python 3.11+ e demonstram os contratos do Core em qualquer PC.

```text
python host-tools/verify_repo.py
python host-tools/secret_scan.py --working-tree
python -m unittest discover -s tests -v
python services/http/topazio_http.py --once
python host-tools/build_rootfs.py --output build/out/rootfs-manifest.json
```

`build/out/` é ignorado e não deve receber firmware, dumps ou chaves privadas.

## Imagem ARM64 executável

O build oficial da Missão 002 usa Debian 13/trixie arm64 e deve rodar dentro
de Linux/WSL2 como root. A forma recomendada no Windows é instalar Ubuntu 24.04
no WSL e executar:

```text
sudo apt-get update
sudo apt-get install -y --no-install-recommends debootstrap qemu-system-arm \
  qemu-user-static e2fsprogs openssh-client curl ca-certificates
sudo scripts/build-arm64.sh
python host-tools/validate_arm64_artifact.py build/out/arm64
sudo scripts/smoke-qemu.sh
```

O build exporta:

- `images/topazio-arm64.ext4`: disco ext4 de 1 GiB para `/dev/vda`;
- `kernel/vmlinuz` e `kernel/initrd.img`: kernel/initramfs Debian arm64;
- `rootfs/topazio-arm64-rootfs.tar.gz`: rootfs sem credenciais privadas;
- `manifests/packages.tsv` e `manifests/topazio-arm64.json`: proveniência,
  contrato, lista de serviços e SHA-256 do disco;
- `logs/`: logs de debootstrap, apt, systemd e QEMU.

O manifesto fixa `source_date_epoch` no commit de origem para o tar do rootfs,
registra o mirror Debian e delimita a máquina como `qemu virt`. O mirror de
pacotes é externo; portanto, esse processo é reproduzível e auditável, mas o
SHA-256 pode variar quando o mirror publica versões novas.

## Limites

O resultado é um artefato de laboratório para QEMU. Ainda faltam para
qualquer telefone: kernel/device tree exatos, firmware permitido, boot chain,
layout de partições, assinatura, prova em dispositivo e recuperação/rollback.
QEMU não prova compatibilidade com o `sea`.

## Dependências

O CI usa Python 3.12 padrão e `unittest`; o build ARM64 usa somente as
ferramentas Debian listadas acima dentro do WSL. Dependências futuras devem
ter licença, hash, origem e justificativa registrados.
