# 🎨 Prompt Gallery

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-green)](https://flask.palletsprojects.com)
[![SQLite](https://img.shields.io/badge/SQLite-3-orange)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

Uma galeria de prompts de IA elegante e funcional, com sistema de contagem de cópias, filtros de tendências e painel administrativo completo.

![Preview](https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1000&auto=format&fit=crop)

## ✨ Funcionalidades

### 🖼️ Galeria Pública
- **Layout em Masonry** - Visualização estilo Pinterest
- **Lightbox/Modal** - Clique nas imagens para ver em tamanho grande
- **Copiar Prompt** - Botão rápido para copiar o prompt completo
- **Favoritos** - Salve seus prompts favoritos no localStorage
- **Filtros de Tendência**:
  - 🔥 Mais copiados (sempre)
  - 📅 Mais copiados hoje
  - 📊 Mais copiados esta semana
  - 📈 Mais copiados este mês

### 🔐 Painel Administrativo
- **Login protegido** - Acesso seguro ao admin
- **CRUD Completo** - Criar, editar e excluir prompts
- **Upload de Imagens** - Arraste e solte ou selecione arquivos
- **Preview ao Vivo** - Veja a imagem antes de salvar
- **Estatísticas** - Acompanhe cópias totais e diárias

### 📊 Analytics
- **Contador de Cópias** - Cada clique em "copiar" é registrado
- **Logs com Timestamp** - Saiba quando cada cópia foi feita
- **Tendências em Tempo Real** - Filtros dinâmicos por período

## 🚀 Instalação

### Pré-requisitos
- Python 3.8+
- pip

### Passo a Passo

1. **Clone o repositório**
```bash
git clone https://github.com/EduardoSpek/prompt-gallery-py.git
cd prompt-gallery-py
```

2. **Crie um ambiente virtual (recomendado)**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale as dependências**
```bash
pip install flask flask-cors werkzeug
```

4. **Configure o admin (opcional)**

Edite o arquivo `app.py` e altere a senha padrão:
```python
ADMIN_PASSWORD_HASH = hashlib.sha256('sua_senha_aqui'.encode()).hexdigest()
```

5. **Inicie o servidor**
```bash
python app.py
```

6. **Acesse no navegador**
- Site público: http://localhost:8080
- Painel admin: http://localhost:8080/admin
  - Senha padrão: `admin123`

## 📁 Estrutura do Projeto

```
prompt-gallery-py/
├── app.py                 # Backend Flask
├── gallery.db             # Banco de dados SQLite
├── README.md              # Este arquivo
├── static/
│   ├── index.html         # Frontend
│   └── uploads/           # Imagens enviadas
└── server.log             # Logs do servidor
```

## 🔧 Configuração

### Porta do Servidor
Por padrão, o servidor roda na porta `8080`. Para alterar, edite o final do `app.py`:

```python
app.run(host='0.0.0.0', port=8080)  # Altere para a porta desejada
```

### Tipos de Imagem Permitidos
Por padrão: PNG, JPG, JPEG, GIF, WEBP

Para adicionar mais formatos, edite:
```python
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
```

### Pasta de Uploads
As imagens são salvas em `static/uploads/`. Certifique-se de que esta pasta exista e tenha permissões de escrita.

## 🛡️ Segurança

- ✅ Senhas hasheadas (SHA-256)
- ✅ Sessões protegidas
- ✅ Validação de tipos de arquivo
- ✅ Nomes de arquivo seguros (secure_filename)
- ✅ Proteção contra path traversal

**⚠️ Importante para Produção:**
- Altere a `secret_key` do Flask
- Use HTTPS
- Configure rate limiting
- Limite o tamanho máximo de upload

## 📝 Uso

### Adicionar Novo Prompt

1. Acesse `/admin` e faça login
2. Clique em "+ Novo Prompt"
3. Preencha:
   - **Título**: Nome do prompt
   - **Prompt**: Texto completo do prompt
   - **Modelo**: Midjourney, DALL-E, Stable Diffusion, etc.
   - **Tags**: Separadas por vírgula
   - **Imagem**: Upload da imagem de exemplo
4. Clique em "Criar Prompt"

### Editar Prompt

1. No painel admin, clique em "Editar" ao lado do prompt
2. Altere os campos desejados
3. Para trocar a imagem, selecione um novo arquivo
4. Clique em "Salvar Alterações"

### Excluir Prompt

1. No painel admin, clique em "Excluir"
2. Confirme a exclusão
3. A imagem também será removida do servidor

## 🎨 Personalização

### Cores e Tema
O frontend usa Tailwind CSS. Para personalizar, edite `static/index.html` e ajuste as classes de cor:

```html
<!-- Exemplo: mudar roxo para azul -->
class="bg-purple-600"  →  class="bg-blue-600"
```

### Layout Masonry
Para ajustar o número de colunas:

```css
@media (min-width: 1024px) { 
    .masonry { column-count: 4; }  /* Altere para 3, 5, etc. */
}
```

## 🤝 Contribuição

Contribuições são bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🙏 Agradecimentos

- [Flask](https://flask.palletsprojects.com) - Framework web
- [Tailwind CSS](https://tailwindcss.com) - Estilização
- [SQLite](https://sqlite.org) - Banco de dados
- [Unsplash](https://unsplash.com) - Imagens de exemplo

---

<p align="center">
  Feito com ❤️ e ☕ por <a href="https://github.com/EduardoSpek">Eduardo Spek</a>
</p>
