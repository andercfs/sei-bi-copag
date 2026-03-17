# Deploy com o mínimo de cliques

Este projeto foi ajustado para um fluxo simples:

- Backend no Render via `render.yaml`
- Frontend no Vercel a partir da raiz do repositório
- Proxy do frontend para a API já configurado em `vercel.json`

## Antes de subir para o GitHub

### Importante sobre os CSVs

Os arquivos `ListaProcessos_SEIPro_*.csv` e a pasta `SEI/` foram adicionados ao `.gitignore` para evitar publicar dados administrativos em um repositório.

Se esses arquivos já estiverem versionados no seu Git, remova-os antes de publicar o repositório.

## Passo 1. Publicar no GitHub

Suba este projeto para um repositório GitHub.

## Passo 2. Deploy do backend no Render

1. Entre em [Render Blueprints](https://dashboard.render.com/blueprints)
2. Clique em **New Blueprint**
3. Conecte o repositório
4. Confirme o arquivo `render.yaml`
5. Quando o Render pedir segredos, preencha apenas:
   - `DEFAULT_ADMIN_PASSWORD`
6. Clique em **Deploy Blueprint**

O `render.yaml` já cria:

- 1 Web Service Python
- 1 banco Render Postgres gratuito
- `DATABASE_URL` ligado automaticamente ao banco
- `JWT_SECRET_KEY` gerado automaticamente

## Passo 3. Deploy do frontend no Vercel

1. Entre em [Vercel New Project](https://vercel.com/new)
2. Importe o mesmo repositório
3. Clique em **Deploy**

Não é necessário:

- escolher pasta `frontend`
- configurar comando de build
- configurar output directory
- configurar URL da API

Tudo isso já foi preparado por `package.json` na raiz e `vercel.json`.

## Login inicial

- Email: `andersoncfs@ufc.br`
- Senha: a senha que você informar no campo `DEFAULT_ADMIN_PASSWORD` do Render

## Limitação importante do banco gratuito do Render

O Render informa que:

- web services gratuitos usam filesystem efêmero
- bancos Postgres gratuitos expiram 30 dias após a criação

Isso significa que este fluxo é excelente para subir rápido e gastar zero, mas não é o ideal para uso institucional contínuo sem manutenção.

Se você criar o banco gratuito em **16 de março de 2026**, a expiração esperada será por volta de **15 de abril de 2026**, salvo mudança nas regras do Render.

## Caminho recomendado depois do primeiro deploy

Se quiser manter a aplicação sem essa limitação de 30 dias, o próximo passo ideal é:

- manter o frontend no Vercel
- manter o backend no Render
- trocar apenas o banco para um Postgres gratuito mais durável, como Supabase

O backend já aceita `DATABASE_URL`, então essa troca exigirá pouca alteração.
