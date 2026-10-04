# Modelo de segurança

## Ameaças

- commit acidental de segredo, dump ou firmware;
- imagem de outro modelo ou hash alterado;
- usuário confundindo diagnóstico com autorização de flash;
- driver/transportes incorretos;
- perda de rede, bateria ou recuperação durante uma operação;
- exposição de um serviço HTTP/SSH em rede não confiável.

## Controles

`.gitignore`, scanner, CI e revisão reduzem vazamento no repositório. DSPs
separam identidade. Manifestos e hashes reduzem confusão de artefatos. O
Installer fail-closed separa detecção de autorização. A UI deve exibir estado
de segurança e não executar comandos privilegiados ocultos.

## Limites

Esses controles não tornam o telefone um servidor de alta disponibilidade. O
hardware não tem ECC, fonte redundante, out-of-band management ou garantia de
rede. SSH precisa de autenticação forte e serviços devem escutar apenas nas
interfaces pretendidas.
