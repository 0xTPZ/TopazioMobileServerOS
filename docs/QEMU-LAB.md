# Laboratório ARM64 no QEMU

## Escopo

Esta é a prova executável da Missão 002. Ela valida o Core em um PC usando
`qemu-system-aarch64`, a máquina virtual genérica `virt`, TCG, disco virtio e
rede user-mode. Não é um teste do Redmi Note 12S e não modifica nenhum
dispositivo Android.

## Dependências no WSL

No Ubuntu 24.04 do WSL2:

```text
sudo apt-get update
sudo apt-get install -y --no-install-recommends debootstrap qemu-system-arm \
  qemu-user-static e2fsprogs openssh-client curl ca-certificates
```

O build usa o filesystem Linux nativo `/tmp` para o rootfs e exporta somente
os resultados para `build/out/arm64`. Isso evita colisões de nomes ao montar
um rootfs Linux no volume Windows.

## Build e smoke test

```text
sudo scripts/build-arm64.sh
python host-tools/validate_arm64_artifact.py build/out/arm64
sudo scripts/smoke-qemu.sh
```

O smoke cria uma cópia descartável do disco, injeta uma chave Ed25519 somente
nessa cópia e encaminha `127.0.0.1:2222` para SSH e `127.0.0.1:8787` para o
HTTP convidado. A chave privada fica em `/tmp` no WSL e é apagada ao terminar.

Sucesso exige todos os sinais:

| Sinal | Evidência |
| --- | --- |
| boot | `TOPAZIO_BOOT_OK` na saída serial |
| serviço HTTP | `GET /healthz` retorna 200 |
| administração | `ssh admin@127.0.0.1 -p 2222` funciona por chave |
| arquitetura | kernel Debian arm64 no guest, manifesto `architecture=arm64` |

## Execução interativa

Depois do build, `scripts/run-qemu.sh` inicia o disco principal e salva a
serial em `build/out/arm64/logs/qemu-serial.log`. O encaminhamento de portas é
o mesmo do smoke. Encerre com `Ctrl+C`.

## Artefatos e limites

O manifesto `manifests/topazio-arm64.json` registra commit, mirror, epoch,
pacotes, caminhos, bytes, SHA-256, serviços e o marcador de boot. Imagens e
tarballs ficam ignorados pelo Git para não versionar binários grandes.

O resultado é **PARTIAL**: prova um servidor ARM64 executável no QEMU, não
prova kernel, device tree, drivers, firmware, partições, boot chain ou
recuperação no `sea`. A Missão 003 permanece planejada e não é iniciada por
este documento.
