"""
Repository Interface (Port) - Define o contrato para persistência
Seguindo Arquitetura Hexagonal / Ports and Adapters
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities import Prompt, CopyLog


class PromptRepository(ABC):
    """Port/Interface para repositório de prompts"""
    
    @abstractmethod
    def create(self, prompt: Prompt) -> Prompt:
        """Cria um novo prompt"""
        pass
    
    @abstractmethod
    def get_by_id(self, prompt_id: int) -> Optional[Prompt]:
        """Busca prompt por ID"""
        pass
    
    @abstractmethod
    def get_all(self, sort_by: str = 'id') -> List[Prompt]:
        """Lista todos os prompts"""
        pass
    
    @abstractmethod
    def update(self, prompt: Prompt) -> Prompt:
        """Atualiza um prompt"""
        pass
    
    @abstractmethod
    def delete(self, prompt_id: int) -> bool:
        """Deleta um prompt"""
        pass
    
    @abstractmethod
    def get_trending(self, period: str = 'all') -> List[Prompt]:
        """Busca prompts mais copiados por período"""
        pass


class CopyLogRepository(ABC):
    """Port/Interface para repositório de logs de cópia"""
    
    @abstractmethod
    def create(self, log: CopyLog) -> CopyLog:
        """Registra uma nova cópia"""
        pass
    
    @abstractmethod
    def get_by_prompt_id(self, prompt_id: int) -> List[CopyLog]:
        """Busca logs por prompt"""
        pass
    
    @abstractmethod
    def get_count_by_period(self, prompt_id: int, period: str) -> int:
        """Conta cópias por período (day, week, month, all)"""
        pass
