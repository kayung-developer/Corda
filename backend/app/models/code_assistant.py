# backend/app/models/code_assistant.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class CodeGenerationRequest(BaseModel):
    prompt: str
    language: Optional[str] = None
    context: Optional[str] = None # e.g., surrounding code
    max_tokens: Optional[int] = 1024
    temperature: Optional[float] = 0.7 # Creativity vs determinism

class CodeGenerationResponse(BaseModel):
    generated_code: str
    language_detected: Optional[str] = None
    confidence: Optional[float] = None # Model's confidence in the generation
    warnings: Optional[List[str]] = None

class CodeExplanationRequest(BaseModel):
    code_block: str
    language: Optional[str] = None

class CodeExplanationResponse(BaseModel):
    explanation: str
    language_detected: Optional[str] = None

class CodeRefactorRequest(BaseModel):
    code_block: str
    language: Optional[str] = None
    refactor_goals: List[str] # e.g., ["DRY", "performance", "readability"]

class CodeRefactorResponse(BaseModel):
    refactored_code: str
    changes_summary: List[str]

# ... other models for features like:
# - AutocompletionRequest / AutocompletionResponse
# - TestGenerationRequest / TestGenerationResponse
# - VulnerabilityDetectionRequest / VulnerabilityDetectionResponse