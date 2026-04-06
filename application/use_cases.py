"""
Use Cases (Application Layer) - Orquestração de regras de negócio
Independente de frameworks e infraestrutura
"""
from typing import List, Optional
from domain.entities import Prompt, CopyLog
from domain.repositories import PromptRepository, CopyLogRepository


class PromptUseCases:
    """Casos de uso para gerenciamento de prompts"""
    
    def __init__(self, prompt_repo: PromptRepository, log_repo: CopyLogRepository):
        self.prompt_repo = prompt_repo
        self.log_repo = log_repo
    
    def create_prompt(self, title: str, prompt_text: str, model: str, 
                      tags: str, image_url: str) -> Prompt:
        """Cria um novo prompt"""
        prompt = Prompt(
            id=None,
            title=title,
            prompt_text=prompt_text,
            model=model,
            tags=tags,
            image_url=image_url,
            copy_count=0
        )
        return self.prompt_repo.create(prompt)
    
    def get_prompt(self, prompt_id: int) -> Optional[Prompt]:
        """Busca um prompt por ID"""
        return self.prompt_repo.get_by_id(prompt_id)
    
    def list_prompts(self, sort_by: str = 'id') -> List[Prompt]:
        """Lista todos os prompts"""
        return self.prompt_repo.get_all(sort_by)
    
    def update_prompt(self, prompt_id: int, **kwargs) -> Optional[Prompt]:
        """Atualiza um prompt existente"""
        prompt = self.prompt_repo.get_by_id(prompt_id)
        if not prompt:
            return None
        
        for key, value in kwargs.items():
            if hasattr(prompt, key):
                setattr(prompt, key, value)
        
        return self.prompt_repo.update(prompt)
    
    def delete_prompt(self, prompt_id: int) -> bool:
        """Remove um prompt"""
        return self.prompt_repo.delete(prompt_id)
    
    def copy_prompt(self, prompt_id: int) -> Optional[Prompt]:
        """Registra uma cópia e retorna o prompt atualizado"""
        prompt = self.prompt_repo.get_by_id(prompt_id)
        if not prompt:
            return None
        
        # Incrementa contador
        prompt.increment_copy()
        self.prompt_repo.update(prompt)
        
        # Registra log
        from datetime import datetime
        log = CopyLog(id=None, prompt_id=prompt_id, copied_at=datetime.now())
        self.log_repo.create(log)
        
        return prompt
    
    def get_trending(self, period: str = 'all') -> List[Prompt]:
        """Busca prompts em tendência"""
        return self.prompt_repo.get_trending(period)


class AnalyticsUseCases:
    """Casos de uso para análise e estatísticas"""
    
    def __init__(self, log_repo: CopyLogRepository):
        self.log_repo = log_repo
    
    def get_copy_stats(self, prompt_id: int) -> dict:
        """Retorna estatísticas de cópias por período"""
        return {
            'day': self.log_repo.get_count_by_period(prompt_id, 'day'),
            'week': self.log_repo.get_count_by_period(prompt_id, 'week'),
            'month': self.log_repo.get_count_by_period(prompt_id, 'month'),
            'all': self.log_repo.get_count_by_period(prompt_id, 'all')
        }
