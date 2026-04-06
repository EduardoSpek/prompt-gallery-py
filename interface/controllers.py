"""
Interface Adapters - Controllers e presenters
Conecta o framework Flask com a aplicação
"""
import os
import hashlib
from flask import Flask, jsonify, request, send_from_directory, session, redirect
from flask_cors import CORS
from werkzeug.utils import secure_filename
from application.use_cases import PromptUseCases, AnalyticsUseCases
from infrastructure.sqlite_repositories import SQLitePromptRepository, SQLiteCopyLogRepository


class PromptController:
    """Controller para endpoints de prompts"""
    
    def __init__(self, prompt_use_cases: PromptUseCases):
        self.use_cases = prompt_use_cases
    
    def get_all_prompts(self, sort_by: str = 'id'):
        """GET /api/prompts"""
        prompts = self.use_cases.list_prompts(sort_by)
        return jsonify([p.to_dict() for p in prompts])
    
    def get_prompt(self, prompt_id: int):
        """GET /api/prompts/<id>"""
        prompt = self.use_cases.get_prompt(prompt_id)
        if not prompt:
            return jsonify({'error': 'Prompt not found'}), 404
        return jsonify(prompt.to_dict())
    
    def create_prompt(self, data: dict, image_url: str):
        """POST /api/prompts"""
        try:
            prompt = self.use_cases.create_prompt(
                title=data['title'],
                prompt_text=data['prompt'],
                model=data['model'],
                tags=data.get('tags', ''),
                image_url=image_url
            )
            return jsonify(prompt.to_dict()), 201
        except KeyError as e:
            return jsonify({'error': f'Missing field: {str(e)}'}), 400
    
    def update_prompt(self, prompt_id: int, data: dict, image_url: str = None):
        """PUT /api/prompts/<id>"""
        kwargs = {
            'title': data.get('title'),
            'prompt_text': data.get('prompt'),
            'model': data.get('model'),
            'tags': data.get('tags')
        }
        if image_url:
            kwargs['image_url'] = image_url
        
        # Remove None values
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        
        prompt = self.use_cases.update_prompt(prompt_id, **kwargs)
        if not prompt:
            return jsonify({'error': 'Prompt not found'}), 404
        return jsonify(prompt.to_dict())
    
    def delete_prompt(self, prompt_id: int):
        """DELETE /api/prompts/<id>"""
        success = self.use_cases.delete_prompt(prompt_id)
        if not success:
            return jsonify({'error': 'Prompt not found'}), 404
        return jsonify({'message': 'Prompt deleted'})
    
    def copy_prompt(self, prompt_id: int):
        """POST /api/copy/<id>"""
        prompt = self.use_cases.copy_prompt(prompt_id)
        if not prompt:
            return jsonify({'error': 'Prompt not found'}), 404
        return jsonify({'message': 'Copied', 'prompt': prompt.to_dict()})
    
    def get_trending(self, period: str):
        """GET /api/prompts/trending/<period>"""
        prompts = self.use_cases.get_trending(period)
        return jsonify([p.to_dict() for p in prompts])


class AdminController:
    """Controller para autenticação e admin"""
    
    def __init__(self, admin_password_hash: str):
        self.admin_password_hash = admin_password_hash
    
    def login(self, password: str):
        """POST /admin/login"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if password_hash == self.admin_password_hash:
            session['admin'] = True
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Invalid password'}), 401
    
    def logout(self):
        """POST /admin/logout"""
        session.pop('admin', None)
        return jsonify({'success': True})
    
    def check_auth(self):
        """Verifica se usuário está autenticado"""
        return session.get('admin', False)


class FileUploadService:
    """Serviço para upload de arquivos"""
    
    def __init__(self, upload_folder: str, allowed_extensions: set):
        self.upload_folder = upload_folder
        self.allowed_extensions = allowed_extensions
        os.makedirs(upload_folder, exist_ok=True)
    
    def allowed_file(self, filename: str) -> bool:
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def save_file(self, file) -> str:
        """Salva arquivo e retorna URL"""
        if file and self.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(self.upload_folder, filename)
            file.save(filepath)
            return f'/uploads/{filename}'
        return None
