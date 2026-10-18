# Busca Visual — projeto inicial Android

Este projeto foi preparado para edição pelo celular Android e compilação de APK na nuvem.

## O que esta versão inicial faz
- Interface Kivy para Android.
- Seleciona uma imagem do armazenamento.
- Indexa até 40 imagens encontradas em uma página pública acessível.
- Salva imagens e links em banco SQLite local.
- Compara imagens do índice usando um hash perceptual simples.

## Limitação importante
A comparação atual é de semelhança visual da imagem inteira. **Ainda não é reconhecimento facial** e o percentual exibido não é probabilidade de identidade. A integração de um modelo facial compatível com Android é uma etapa posterior; não instale este protótipo esperando identificação facial.

A pesquisa não consulta toda a web: indexa apenas imagens encontradas em páginas que você fornecer e que permitam o acesso. Respeite termos de uso, direitos autorais, privacidade e limites de acesso. Use imagens próprias ou com autorização.

## Como trabalhar somente pelo celular
1. Crie uma conta/repositório no GitHub pelo navegador do celular.
2. Envie os arquivos deste projeto ao repositório, preservando a pasta `.github/workflows`.
3. Abra a aba **Actions** no GitHub e execute **Build Android APK** (também compila ao enviar commits para `main`).
4. Baixe o artefato `BuscaVisual-debug-apk` na execução concluída.
5. Instale o APK no Android, autorizando a instalação a partir da fonte usada para baixar.

## Próxima etapa
Integrar um modelo de embeddings faciais compatível com Android/ONNX ou TensorFlow Lite, validar desempenho no dispositivo e implementar comparação facial somente com uma galeria autorizada.
