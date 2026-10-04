# Installer skeleton

`topazio_installer.py` demonstra a camada de política do Topazio Mobile
Installer. Ela aceita observações serializadas e devolve um plano, mas não
possui adaptador que abra USB, ADB, fastboot ou partições. O DSP `xiaomi-sea`
permanece `RESEARCH`, portanto a execução termina em `UNSUPPORTED`.
