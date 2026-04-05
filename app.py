from flask import Flask, jsonify, send_from_directory, request, render_template_string, redirect, session
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename
import hashlib

app = Flask(__name__, static_folder='static')
app.secret_key = 'sua_chave_secreta_aqui_mude_em_producao'  # Mude em produção!
CORS(app)

DB_PATH = 'gallery.db'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Cria pasta de uploads se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                prompt TEXT NOT NULL,
                image_url TEXT NOT NULL,
                model TEXT,
                tags TEXT,
                copy_count INTEGER DEFAULT 0
            )
        ''')
        
        # Tabela para registrar cada cópia com timestamp
        conn.execute('''
            CREATE TABLE IF NOT EXISTS copy_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id INTEGER NOT NULL,
                copied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prompt_id) REFERENCES prompts(id)
            )
        ''')
        
        # Seed data if empty
        cursor = conn.cursor()
        cursor.execute('SELECT count(*) FROM prompts')
        if cursor.fetchone()[0] == 0:
            seed_data = [
                ("Cyberpunk Salvador", "Futuristic Salvador Bahia, Brazil, cyberpunk style, neon lights, Pelourinho with flying cars, 8k, highly detailed, cinematic lighting", "https://images.unsplash.com/photo-1614850523296-dbe1c3452747?q=80&w=1000", "Midjourney v6", "Cyberpunk, Brazil, City"),
                ("Abstract Musical Theory", "Abstract representation of musical theory, floating notes, golden ratio, deep blue and gold colors, ethereal, octane render, 4k", "https://images.unsplash.com/photo-1507838596351-333033333333?q=80&w=1000", "DALL-E 3", "Abstract, Music, Art"),
                ("Hyper-realistic Cavaquinho", "Close up of a professional cavaquinho, polished wood, studio lighting, bokeh background, macro photography, 8k", "https://images.unsplash.com/photo-1510915228383-66776630737d?q=80&w=1000", "Stable Diffusion XL", "Instrument, Realistic, Music"),
                ("Neon Samurai", "Cybernetic samurai in a rainy Tokyo street, neon reflections, sharp focus, volumetric fog, 8k resolution", "https://images.unsplash.com/photo-1578301978693-82581d96177a?q=80&w=1000", "Midjourney v6", "Samurai, Tokyo, Neon"),
                ("Cosmic Library", "Infinite library in space, floating books, nebulae in the background, ethereal lighting, surrealism, 8k", "https://images.unsplash.com/photo-1462085366279-75b69717665d?q=80&w=1000", "DALL-E 3", "Space, Library, Surreal"),
                ("Ancient Forest Spirit", "Giant glowing spirit in a deep ancient forest, bioluminescent plants, cinematic atmosphere, fantasy art", "https://images.unsplash.com/photo-1441974231531-c6227db76b6b?q=80&w=1000", "Stable Diffusion XL", "Nature, Fantasy, Spirit")
            ]
            conn.executemany('INSERT INTO prompts (title, prompt, image_url, model, tags) VALUES (?, ?, ?, ?, ?)', seed_data)
            conn.commit()

@app.route('/api/prompts', methods=['GET'])
def get_prompts():
    sort_by = request.args.get('sort', 'id') # 'id' or 'copies'
    with get_db() as conn:
        if sort_by == 'copies':
            cursor = conn.execute('SELECT * FROM prompts ORDER BY copy_count DESC')
        else:
            cursor = conn.execute('SELECT * FROM prompts')
        
        prompts = []
        for row in cursor:
            prompts.append({
                "id": row['id'],
                "title": row['title'],
                "prompt": row['prompt'],
                "image_url": row['image_url'],
                "model": row['model'],
                "tags": row['tags'].split(','),
                "copy_count": row['copy_count']
            })
    return jsonify(prompts)

@app.route('/api/copy/<int:prompt_id>', methods=['POST'])
def increment_copy(prompt_id):
    with get_db() as conn:
        # Incrementa o contador total
        conn.execute('UPDATE prompts SET copy_count = copy_count + 1 WHERE id = ?', (prompt_id,))
        # Registra o log com timestamp
        conn.execute('INSERT INTO copy_logs (prompt_id) VALUES (?)', (prompt_id,))
        conn.commit()
    return jsonify({"status": "success"})

@app.route('/api/prompts/trending', methods=['GET'])
def get_trending_prompts():
    period = request.args.get('period', 'all')  # 'day', 'week', 'month', 'all'
    
    with get_db() as conn:
        if period == 'day':
            # Últimas 24 horas
            cursor = conn.execute('''
                SELECT p.*, COUNT(c.id) as period_copies 
                FROM prompts p
                LEFT JOIN copy_logs c ON p.id = c.prompt_id 
                    AND c.copied_at >= datetime('now', '-1 day')
                GROUP BY p.id
                ORDER BY period_copies DESC, p.copy_count DESC
            ''')
        elif period == 'week':
            # Últimos 7 dias
            cursor = conn.execute('''
                SELECT p.*, COUNT(c.id) as period_copies 
                FROM prompts p
                LEFT JOIN copy_logs c ON p.id = c.prompt_id 
                    AND c.copied_at >= datetime('now', '-7 days')
                GROUP BY p.id
                ORDER BY period_copies DESC, p.copy_count DESC
            ''')
        elif period == 'month':
            # Últimos 30 dias
            cursor = conn.execute('''
                SELECT p.*, COUNT(c.id) as period_copies 
                FROM prompts p
                LEFT JOIN copy_logs c ON p.id = c.prompt_id 
                    AND c.copied_at >= datetime('now', '-30 days')
                GROUP BY p.id
                ORDER BY period_copies DESC, p.copy_count DESC
            ''')
        else:
            # 'all' - todos os tempos (usa o copy_count total)
            cursor = conn.execute('SELECT *, copy_count as period_copies FROM prompts ORDER BY copy_count DESC')
        
        prompts = []
        for row in cursor:
            prompts.append({
                "id": row['id'],
                "title": row['title'],
                "prompt": row['prompt'],
                "image_url": row['image_url'],
                "model": row['model'],
                "tags": row['tags'].split(','),
                "copy_count": row['copy_count'],
                "period_copies": row['period_copies']
            })
    return jsonify(prompts)

# ==================== ÁREA ADMINISTRATIVA ====================

ADMIN_PASSWORD_HASH = hashlib.sha256('admin123'.encode()).hexdigest()  # Senha padrão: admin123

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if hashlib.sha256(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH:
            session['admin'] = True
            return redirect('/admin')
        return render_template_string(LOGIN_TEMPLATE, error='Senha incorreta')
    return render_template_string(LOGIN_TEMPLATE, error=None)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect('/admin/login')

def require_admin(f):
    def wrapper(*args, **kwargs):
        if not session.get('admin'):
            return redirect('/admin/login')
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/admin')
@require_admin
def admin_dashboard():
    with get_db() as conn:
        # Estatísticas
        total_prompts = conn.execute('SELECT COUNT(*) FROM prompts').fetchone()[0]
        total_copies = conn.execute('SELECT COALESCE(SUM(copy_count), 0) FROM prompts').fetchone()[0]
        today_copies = conn.execute('''
            SELECT COUNT(*) FROM copy_logs 
            WHERE copied_at >= datetime('now', '-1 day')
        ''').fetchone()[0]
        
        # Lista de prompts
        prompts = conn.execute('SELECT * FROM prompts ORDER BY id DESC').fetchall()
    
    return render_template_string(ADMIN_TEMPLATE, 
        prompts=prompts, 
        total_prompts=total_prompts,
        total_copies=total_copies,
        today_copies=today_copies
    )

@app.route('/admin/prompt/new', methods=['GET', 'POST'])
@require_admin
def admin_new_prompt():
    if request.method == 'POST':
        title = request.form.get('title')
        prompt_text = request.form.get('prompt')
        model = request.form.get('model')
        tags = request.form.get('tags')
        
        # Processa upload da imagem
        if 'image' not in request.files:
            return 'Nenhuma imagem enviada', 400
        
        file = request.files['image']
        if file.filename == '':
            return 'Nenhuma imagem selecionada', 400
        
        if file and allowed_file(file.filename):
            # Gera nome único para o arquivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = secure_filename(f"{timestamp}_{file.filename}")
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            # URL relativa para acesso
            image_url = f'/static/uploads/{filename}'
            
            with get_db() as conn:
                conn.execute('''
                    INSERT INTO prompts (title, prompt, image_url, model, tags, copy_count)
                    VALUES (?, ?, ?, ?, ?, 0)
                ''', (title, prompt_text, image_url, model, tags))
                conn.commit()
            
            return redirect('/admin')
        
        return 'Tipo de arquivo não permitido', 400
    
    return render_template_string(ADMIN_FORM_TEMPLATE, prompt=None, action='new')

@app.route('/admin/prompt/edit/<int:id>', methods=['GET', 'POST'])
@require_admin
def admin_edit_prompt(id):
    with get_db() as conn:
        prompt = conn.execute('SELECT * FROM prompts WHERE id = ?', (id,)).fetchone()
        if not prompt:
            return 'Prompt não encontrado', 404
        
        if request.method == 'POST':
            title = request.form.get('title')
            prompt_text = request.form.get('prompt')
            model = request.form.get('model')
            tags = request.form.get('tags')
            
            # Se enviou nova imagem
            if 'image' in request.files:
                file = request.files['image']
                if file.filename != '' and allowed_file(file.filename):
                    # Remove imagem antiga se existir
                    old_path = prompt['image_url'].replace('/static/', 'static/')
                    if os.path.exists(old_path) and 'uploads' in old_path:
                        os.remove(old_path)
                    
                    # Salva nova imagem
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = secure_filename(f"{timestamp}_{file.filename}")
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(filepath)
                    image_url = f'/static/uploads/{filename}'
                    
                    conn.execute('''
                        UPDATE prompts SET title=?, prompt=?, image_url=?, model=?, tags=?
                        WHERE id=?
                    ''', (title, prompt_text, image_url, model, tags, id))
                else:
                    conn.execute('''
                        UPDATE prompts SET title=?, prompt=?, model=?, tags=?
                        WHERE id=?
                    ''', (title, prompt_text, model, tags, id))
            else:
                conn.execute('''
                    UPDATE prompts SET title=?, prompt=?, model=?, tags=?
                    WHERE id=?
                ''', (title, prompt_text, model, tags, id))
            
            conn.commit()
            return redirect('/admin')
        
        return render_template_string(ADMIN_FORM_TEMPLATE, prompt=prompt, action='edit')

@app.route('/admin/prompt/delete/<int:id>', methods=['POST'])
@require_admin
def admin_delete_prompt(id):
    with get_db() as conn:
        prompt = conn.execute('SELECT image_url FROM prompts WHERE id = ?', (id,)).fetchone()
        if prompt:
            # Remove imagem do sistema de arquivos
            image_path = prompt['image_url'].replace('/static/', 'static/')
            if os.path.exists(image_path) and 'uploads' in image_path:
                os.remove(image_path)
            
            # Remove do banco
            conn.execute('DELETE FROM prompts WHERE id = ?', (id,))
            conn.execute('DELETE FROM copy_logs WHERE prompt_id = ?', (id,))
            conn.commit()
    
    return redirect('/admin')

# Templates HTML para admin
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Login - Admin</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 min-h-screen flex items-center justify-center">
    <div class="bg-slate-800 p-8 rounded-2xl shadow-xl w-full max-w-md">
        <h1 class="text-2xl font-bold text-white mb-6 text-center">🔐 Área Administrativa</h1>
        {% if error %}
            <div class="bg-red-500/20 border border-red-500 text-red-300 p-3 rounded-lg mb-4">{{ error }}</div>
        {% endif %}
        <form method="POST" class="space-y-4">
            <div>
                <label class="block text-slate-400 text-sm mb-2">Senha</label>
                <input type="password" name="password" required 
                    class="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-purple-500 focus:outline-none">
            </div>
            <button type="submit" 
                class="w-full py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-medium transition">
                Entrar
            </button>
        </form>
    </div>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - Admin</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 min-h-screen">
    <nav class="bg-slate-800 border-b border-slate-700 p-4">
        <div class="max-w-7xl mx-auto flex justify-between items-center">
            <h1 class="text-xl font-bold text-white">🎨 Prompt Gallery Admin</h1>
            <div class="flex gap-4">
                <a href="/" target="_blank" class="text-slate-400 hover:text-white transition">Ver Site →</a>
                <a href="/admin/logout" class="text-red-400 hover:text-red-300 transition">Sair</a>
            </div>
        </div>
    </nav>
    
    <main class="max-w-7xl mx-auto p-6">
        <!-- Estatísticas -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700">
                <div class="text-slate-400 text-sm mb-1">Total de Prompts</div>
                <div class="text-3xl font-bold text-white">{{ total_prompts }}</div>
            </div>
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700">
                <div class="text-slate-400 text-sm mb-1">Total de Cópias</div>
                <div class="text-3xl font-bold text-purple-400">{{ total_copies }}</div>
            </div>
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700">
                <div class="text-slate-400 text-sm mb-1">Cópias Hoje</div>
                <div class="text-3xl font-bold text-green-400">{{ today_copies }}</div>
            </div>
        </div>
        
        <!-- Ações -->
        <div class="flex justify-between items-center mb-6">
            <h2 class="text-xl font-bold text-white">Prompts</h2>
            <a href="/admin/prompt/new" 
                class="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-medium transition">
                + Novo Prompt
            </a>
        </div>
        
        <!-- Lista de Prompts -->
        <div class="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
            <table class="w-full">
                <thead class="bg-slate-700/50">
                    <tr>
                        <th class="px-4 py-3 text-left text-slate-400 font-medium">Imagem</th>
                        <th class="px-4 py-3 text-left text-slate-400 font-medium">Título</th>
                        <th class="px-4 py-3 text-left text-slate-400 font-medium">Modelo</th>
                        <th class="px-4 py-3 text-left text-slate-400 font-medium">Cópias</th>
                        <th class="px-4 py-3 text-right text-slate-400 font-medium">Ações</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-700">
                    {% for p in prompts %}
                    <tr class="hover:bg-slate-700/30">
                        <td class="px-4 py-3">
                            <img src="{{ p.image_url }}" alt="" class="w-16 h-16 object-cover rounded-lg">
                        </td>
                        <td class="px-4 py-3 text-white">{{ p.title }}</td>
                        <td class="px-4 py-3 text-slate-400">{{ p.model }}</td>
                        <td class="px-4 py-3 text-slate-400">{{ p.copy_count }}</td>
                        <td class="px-4 py-3 text-right">
                            <a href="/admin/prompt/edit/{{ p.id }}" 
                                class="text-blue-400 hover:text-blue-300 mr-3">Editar</a>
                            <form method="POST" action="/admin/prompt/delete/{{ p.id }}" class="inline" 
                                onsubmit="return confirm('Tem certeza que deseja excluir?')">
                                <button type="submit" class="text-red-400 hover:text-red-300">Excluir</button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </main>
</body>
</html>
'''

ADMIN_FORM_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>{% if action == 'new' %}Novo{% else %}Editar{% endif %} Prompt - Admin</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 min-h-screen">
    <nav class="bg-slate-800 border-b border-slate-700 p-4">
        <div class="max-w-3xl mx-auto">
            <a href="/admin" class="text-slate-400 hover:text-white transition">← Voltar</a>
        </div>
    </nav>
    
    <main class="max-w-3xl mx-auto p-6">
        <h1 class="text-2xl font-bold text-white mb-6">
            {% if action == 'new' %}🆕 Novo Prompt{% else %}✏️ Editar Prompt{% endif %}
        </h1>
        
        <form method="POST" enctype="multipart/form-data" class="bg-slate-800 p-6 rounded-xl border border-slate-700 space-y-6">
            <div>
                <label class="block text-slate-400 text-sm mb-2">Título *</label>
                <input type="text" name="title" required value="{{ prompt.title if prompt else '' }}"
                    class="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-purple-500 focus:outline-none"
                    placeholder="Ex: Cyberpunk Salvador">
            </div>
            
            <div>
                <label class="block text-slate-400 text-sm mb-2">Prompt *</label>
                <textarea name="prompt" required rows="4"
                    class="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-purple-500 focus:outline-none resize-none"
                    placeholder="Descreva o prompt completo...">{{ prompt.prompt if prompt else '' }}</textarea>
            </div>
            
            <div>
                <label class="block text-slate-400 text-sm mb-2">Modelo *</label>
                <input type="text" name="model" required value="{{ prompt.model if prompt else 'Midjourney v6' }}"
                    class="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-purple-500 focus:outline-none"
                    placeholder="Ex: Midjourney v6, DALL-E 3, Stable Diffusion...">
            </div>
            
            <div>
                <label class="block text-slate-400 text-sm mb-2">Tags (separadas por vírgula)</label>
                <input type="text" name="tags" value="{{ prompt.tags if prompt else '' }}"
                    class="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-purple-500 focus:outline-none"
                    placeholder="Ex: Cyberpunk, Brazil, City">
            </div>
            
            <div>
                <label class="block text-slate-400 text-sm mb-2">
                    Imagem {% if action == 'new' %}*{% else %}(deixe em branco para manter a atual){% endif %}
                </label>
                <input type="file" name="image" accept="image/*" {% if action == 'new' %}required{% endif %}
                    class="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-purple-600 file:text-white file:font-medium hover:file:bg-purple-500"
                    onchange="previewImage(this)">
                
                {% if prompt %}
                <div class="mt-2">
                    <p class="text-slate-400 text-sm mb-2">Imagem atual:</p>
                    <img src="{{ prompt.image_url }}" alt="" class="w-48 h-48 object-cover rounded-lg">
                </div>
                {% endif %}
                
                <div id="preview" class="mt-2 hidden">
                    <p class="text-slate-400 text-sm mb-2">Preview:</p>
                    <img id="preview-img" src="" alt="" class="w-48 h-48 object-cover rounded-lg">
                </div>
            </div>
            
            <div class="flex gap-4">
                <a href="/admin" 
                    class="flex-1 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition text-center">
                    Cancelar
                </a>
                <button type="submit" 
                    class="flex-1 py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-medium transition">
                    {% if action == 'new' %}Criar Prompt{% else %}Salvar Alterações{% endif %}
                </button>
            </div>
        </form>
    </main>
    
    <script>
        function previewImage(input) {
            const preview = document.getElementById('preview');
            const previewImg = document.getElementById('preview-img');
            
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImg.src = e.target.result;
                    preview.classList.remove('hidden');
                }
                reader.readAsDataURL(input.files[0]);
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    init_db()
    # Usa porta da variável de ambiente (para Render, Railway, etc.) ou 8080 local
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
