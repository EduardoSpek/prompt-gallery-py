"""
Main Application - Composition Root
Configura a injeção de dependências e rotas
"""
import os
import hashlib
from flask import Flask, jsonify, request, send_from_directory, session, redirect
from flask_cors import CORS

# Importações da arquitetura hexagonal
from infrastructure.sqlite_repositories import SQLitePromptRepository, SQLiteCopyLogRepository
from application.use_cases import PromptUseCases, AnalyticsUseCases
from interface.controllers import PromptController, AdminController, FileUploadService


# Configurações
DB_PATH = os.environ.get('DB_PATH', 'gallery.db')
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'static/uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ADMIN_PASSWORD_HASH = hashlib.sha256(
    os.environ.get('ADMIN_PASSWORD', 'admin123').encode()
).hexdigest()

# Criação do app Flask
app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'sua_chave_secreta_aqui_mude_em_producao')
CORS(app)

# ═══════════════════════════════════════════════════════════════
# INJEÇÃO DE DEPENDÊNCIAS (Composition Root)
# ═══════════════════════════════════════════════════════════════

# Repositories (Adapters)
prompt_repo = SQLitePromptRepository(DB_PATH)
log_repo = SQLiteCopyLogRepository(DB_PATH)

# Use Cases (Application)
prompt_use_cases = PromptUseCases(prompt_repo, log_repo)
analytics_use_cases = AnalyticsUseCases(log_repo)

# Controllers (Interface Adapters)
prompt_controller = PromptController(prompt_use_cases)
admin_controller = AdminController(ADMIN_PASSWORD_HASH)
file_service = FileUploadService(UPLOAD_FOLDER, ALLOWED_EXTENSIONS)

# ═══════════════════════════════════════════════════════════════
# ROTAS - API REST
# ═══════════════════════════════════════════════════════════════

@app.route('/api/prompts', methods=['GET'])
def get_prompts():
    """Lista todos os prompts"""
    sort_by = request.args.get('sort', 'id')
    return prompt_controller.get_all_prompts(sort_by)

@app.route('/api/prompts/trending/<period>', methods=['GET'])
def get_trending(period):
    """Busca prompts em tendência (day, week, month, all)"""
    return prompt_controller.get_trending(period)

@app.route('/api/prompts/<int:prompt_id>', methods=['GET'])
def get_prompt(prompt_id):
    """Busca um prompt específico"""
    return prompt_controller.get_prompt(prompt_id)

@app.route('/api/prompts', methods=['POST'])
def create_prompt():
    """Cria um novo prompt"""
    if not admin_controller.check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.form
    file = request.files.get('image')
    image_url = file_service.save_file(file) if file else data.get('image_url')
    
    if not image_url:
        return jsonify({'error': 'Image required'}), 400
    
    return prompt_controller.create_prompt(data, image_url)

@app.route('/api/prompts/<int:prompt_id>', methods=['PUT'])
def update_prompt(prompt_id):
    """Atualiza um prompt"""
    if not admin_controller.check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.form
    file = request.files.get('image')
    image_url = file_service.save_file(file) if file else None
    
    return prompt_controller.update_prompt(prompt_id, data, image_url)

@app.route('/api/prompts/<int:prompt_id>', methods=['DELETE'])
def delete_prompt(prompt_id):
    """Remove um prompt"""
    if not admin_controller.check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Remove arquivo de imagem
    prompt = prompt_use_cases.get_prompt(prompt_id)
    if prompt and prompt.image_url:
        filepath = os.path.join(UPLOAD_FOLDER, os.path.basename(prompt.image_url))
        if os.path.exists(filepath):
            os.remove(filepath)
    
    return prompt_controller.delete_prompt(prompt_id)

@app.route('/api/copy/<int:prompt_id>', methods=['POST'])
def copy_prompt(prompt_id):
    """Registra uma cópia de prompt"""
    return prompt_controller.copy_prompt(prompt_id)

# ═══════════════════════════════════════════════════════════════
# ROTAS - ADMIN
# ═══════════════════════════════════════════════════════════════

@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Login no painel admin"""
    data = request.get_json() or request.form
    return admin_controller.login(data.get('password', ''))

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    """Logout do painel admin"""
    return admin_controller.logout()

@app.route('/admin/check', methods=['GET'])
def check_admin():
    """Verifica status de autenticação"""
    return jsonify({'authenticated': admin_controller.check_auth()})

# ═══════════════════════════════════════════════════════════════
# ROTAS - SERVING DE ARQUIVOS
# ═══════════════════════════════════════════════════════════════

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve arquivos de upload"""
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/')
def index():
    """Serve a página principal"""
    return send_from_directory('static', 'index.html')

@app.route('/admin')
def admin():
    """Serve a página de admin"""
    return send_from_directory('static', 'admin.html')

# ═══════════════════════════════════════════════════════════════
# INICIALIZAÇÃO
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
