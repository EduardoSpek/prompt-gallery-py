"""
Domain Entities - Regras de negócio puras, sem dependências externas
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Prompt:
    """Entidade Prompt - coração do domínio"""
    id: Optional[int]
    title: str
    prompt_text: str
    model: str
    tags: str
    image_url: str
    copy_count: int = 0
    created_at: Optional[datetime] = None
    
    def increment_copy(self) -> None:
        """Incrementa contador de cópias"""
        self.copy_count += 1
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'prompt': self.prompt_text,
            'model': self.model,
            'tags': self.tags,
            'image_url': self.image_url,
            'copy_count': self.copy_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class CopyLog:
    """Entidade de log de cópias"""
    id: Optional[int]
    prompt_id: int
    copied_at: datetime
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'prompt_id': self.prompt_id,
            'copied_at': self.copied_at.isoformat()
        }
