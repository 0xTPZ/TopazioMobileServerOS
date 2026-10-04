# Pesquisa e evidências

## Convenções

- `CONFIRMED`: observado em fonte ou execução reproduzível;
- `INFERRED`: conclusão razoável derivada de evidência, ainda não prova;
- `UNKNOWN`: não medido ou sem fonte suficiente;
- `BLOCKED`: tentativa impedida por transporte, permissão ou pré-condição.

## Redmi Note 12S / `sea`

**CONFIRMED:** a auditoria local identificou Redmi Note 12S, SoC MediaTek
Helio G96/MT6781 e arquitetura ARM64; a FAQ da Xiaomi documenta o hardware
comercial. **CONFIRMED:** a tabela de código aberto da Xiaomi lista a árvore
`sea-t-oss` para Redmi Note 12S/Android T. **CONFIRMED:** durante a auditoria
não havia dispositivo acessível por `adb` ou `fastboot`; a interface live tinha
erro de driver 28. **BLOCKED:** consultas de bootloader e partições não foram
executadas. **UNKNOWN:** estado do bootloader desta unidade e nível de suporte
Linux mainline.

## Decisão

O caminho híbrido Android/Termux é a melhor primeira etapa reversível. Debian
arm64 é uma base conceitual válida para userspace, mas a documentação Debian
ressalta que suporte depende do kernel/device tree da plataforma; isso não
prova boot no `sea`.

## Fontes técnicas

- Xiaomi FAQ: https://www.mi.com/global/support/faq/details/KA-13546/
- Xiaomi Kernel Open Source: https://github.com/MiCode/Xiaomi_Kernel_OpenSource/blob/README/README.md
- Android OEM USB drivers: https://developer.android.com/studio/run/oem-usb
- Android Google USB driver scope: https://developer.android.com/studio/run/win-usb
- Debian arm64 hardware: https://www.debian.org/releases/stable/arm64/ch02s01.en.html
- Debian arm64 installation guide: https://www.debian.org/releases/trixie/arm64/
- Pesquisa comunitária pública (não tratada como suporte oficial): https://github.com/mt6781-sea/

Os documentos locais `C:\RedmiLabAudit\Relatorio.md` e
`C:\RedmiLabAudit\comandos-executados.txt` foram usados como evidência de
trabalho, mas não são copiados para o repositório por conterem identificadores
de dispositivo e histórico operacional.
