# Roadmap

## Missão 001 — fundação (esta versão)

- [x] workspace isolado, Git e guardrails;
- [x] Core/DSP, Installer, UI e Recovery documentados;
- [x] protótipo Python de status, HTTP e plano somente leitura;
- [x] pesquisa sanitizada do Redmi Note 12S;
- [x] testes, secret scan, validação de docs e CI;
- [x] checkpoint público no GitHub.

## Missão 002 — primeiro executável ARM64/QEMU

- [x] gerar Debian arm64 com rootfs, kernel e initramfs;
- [x] instalar SSH sem senha padrão, usuário `admin` e serviços Topazio;
- [x] exportar imagem ext4, rootfs tar, manifesto e hashes;
- [x] iniciar no QEMU `virt` com rede e console serial;
- [x] comprovar `TOPAZIO_BOOT_OK`, `/healthz` e login SSH no smoke test;
- [x] manter o `sea` intocado e em `RESEARCH`.

## Missão 003 — enablement do Xiaomi `sea`

- [x] fixar a fonte oficial `sea-t-oss`, commit, defconfig e DTS;
- [x] registrar boot chain, AVB, A/B/dynamic e partições como evidência explícita;
- [x] criar manifest v2 e matriz de capabilities sem declarar `WORKING`;
- [x] criar host probe, recovery check e pipeline de artefatos fail-closed;
- [x] tentar `sea_defconfig` e build out-of-tree no PC;
- [x] preservar o telefone intocado e documentar driver Windows Code 28;
- [ ] obter source/vendor completo ou toolchain compatível e gerar kernel+DTB;
- [ ] validar recovery e boot em hardware dedicado com procedimento aprovado.

## Missão 004 — próxima etapa, não iniciada

- confirmar estado do bootloader por caminho oficial;
- localizar documentação e código publicamente redistribuíveis;
- testar somente em hardware dedicado com recuperação verificada;
- classificar cada periférico como funcional, parcial ou bloqueado.

## Horizonte

Containerização real, UI touchscreen nativa, múltiplos DSPs, builds Linux/macOS
do Installer e suporte estável só entram após a base de recuperação e rede.
