"""
SQLite Adapters - Implementação concreta dos repositórios
Pode ser facilmente trocado por PostgreSQL, MongoDB, etc.
"""
import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional
from domain.entities import Prompt, CopyLog
from domain.repositories import PromptRepository, CopyLogRepository


class SQLitePromptRepository(PromptRepository):
    """Adapter SQLite para PromptRepository"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """Inicializa o banco de dados"""
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    prompt_text TEXT NOT NULL,
                    model TEXT NOT NULL,
                    tags TEXT,
                    image_url TEXT NOT NULL,
                    copy_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    
    def _row_to_prompt(self, row: sqlite3.Row) -> Prompt:
        """Converte row do SQLite para entidade Prompt"""
        return Prompt(
            id=row['id'],
            title=row['title'],
            prompt_text=row['prompt'],  # Mantém compatibilidade com DB antigo
            model=row['model'],
            tags=row['tags'] or '',
            image_url=row['image_url'],
            copy_count=row['copy_count'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )
    
    def create(self, prompt: Prompt) -> Prompt:
        with self._get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO prompts (title, prompt, model, tags, image_url, copy_count)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (prompt.title, prompt.prompt_text, prompt.model, 
                  prompt.tags, prompt.image_url, prompt.copy_count))
            conn.commit()
            prompt.id = cursor.lastrowid
            return prompt
    
    def get_by_id(self, prompt_id: int) -> Optional[Prompt]:
        with self._get_connection() as conn:
            row = conn.execute(
                'SELECT * FROM prompts WHERE id = ?', (prompt_id,)
            ).fetchone()
            return self._row_to_prompt(row) if row else None
    
    def get_all(self, sort_by: str = 'id') -> List[Prompt]:
        # Validação para prevenir SQL injection
        allowed_sorts = {'id': 'id', 'copy_count': 'copy_count DESC', 
                        'created_at': 'created_at DESC'}
        order_by = allowed_sorts.get(sort_by, 'id')
        
        with self._get_connection() as conn:
            rows = conn.execute(f'SELECT * FROM prompts ORDER BY {order_by}').fetchall()
            return [self._row_to_prompt(row) for row in rows]
    
    def update(self, prompt: Prompt) -> Prompt:
        with self._get_connection() as conn:
            conn.execute('''
                UPDATE prompts 
                SET title = ?, prompt = ?, model = ?, tags = ?, 
                    image_url = ?, copy_count = ?
                WHERE id = ?
            ''', (prompt.title, prompt.prompt_text, prompt.model, prompt.tags,
                  prompt.image_url, prompt.copy_count, prompt.id))
            conn.commit()
            return prompt
    
    def delete(self, prompt_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute('DELETE FROM prompts WHERE id = ?', (prompt_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_trending(self, period: str = 'all') -> List[Prompt]:
        """Busca prompts mais copiados por período"""
        if period == 'all':
            return self.get_all('copy_count')
        
        # Para períodos específicos, usa JOIN com copy_logs
        time_filters = {
            'day': "datetime(copied_at) > datetime('now', '-1 day')",
            'week': "datetime(copied_at) > datetime('now', '-7 days')",
            'month': "datetime(copied_at) > datetime('now', '-30 days')"
        }
        
        where_clause = time_filters.get(period, '1=1')
        
        with self._get_connection() as conn:
            rows = conn.execute(f'''
                SELECT p.*, COUNT(c.id) as period_copies
                FROM prompts p
                LEFT JOIN copy_logs c ON p.id = c.prompt_id AND {where_clause}
                GROUP BY p.id
                HAVING period_copies > 0
                ORDER BY period_copies DESC
            ''').fetchall()
            return [self._row_to_prompt(row) for row in rows]


class SQLiteCopyLogRepository(CopyLogRepository):
    """Adapter SQLite para CopyLogRepository"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS copy_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id INTEGER NOT NULL,
                    copied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (prompt_id) REFERENCES prompts(id)
                )
            ''')
            conn.commit()
    
    def _row_to_log(self, row: sqlite3.Row) -> CopyLog:
        return CopyLog(
            id=row['id'],
            prompt_id=row['prompt_id'],
            copied_at=datetime.fromisoformat(row['copied_at'])
        )
    
    def create(self, log: CopyLog) -> CopyLog:
        with self._get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO copy_logs (prompt_id, copied_at)
                VALUES (?, ?)
            ''', (log.prompt_id, log.copied_at.isoformat()))
            conn.commit()
            log.id = cursor.lastrowid
            return log
    
    def get_by_prompt_id(self, prompt_id: int) -> List[CopyLog]:
        with self._get_connection() as conn:
            rows = conn.execute(
                'SELECT * FROM copy_logs WHERE prompt_id = ? ORDER BY copied_at DESC',
                (prompt_id,)
            ).fetchall()
            return [self._row_to_log(row) for row in rows]
    
    def get_count_by_period(self, prompt_id: int, period: str) -> int:
        """Conta cópias por período"""
        if period == 'all':
            with self._get_connection() as conn:
                result = conn.execute(
                    'SELECT COUNT(*) FROM copy_logs WHERE prompt_id = ?',
                    (prompt_id,)
                ).fetchone()
                return result[0] if result else 0
        
        time_filters = {
            'day': "datetime(copied_at) > datetime('now', '-1 day')",
            'week': "datetime(copied_at) > datetime('now', '-7 days')",
            'month': "datetime(copied_at) > datetime('now', '-30 days')"
        }
        
        where_clause = time_filters.get(period, '1=1')
        
        with self._get_connection() as conn:
            result = conn.execute(f'''
                SELECT COUNT(*) FROM copy_logs 
                WHERE prompt_id = ? AND {where_clause}
            ''', (prompt_id,)).fetchone()
            return result[0] if result else 0
