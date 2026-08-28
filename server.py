import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, status

from soph.gateway.schemas import (
    ObservationFrameSchema,
    ActionProposalSchema,
    ExpectedEffectSchema
)
from soph.gateway.security import verify_api_key

# Tenta importar o CognitiveCore e o ObservationFrame interno de forma segura (sem modificá-los)
try:
    from soph.core.soph_core import CognitiveCore, ObservationFrame as BrainObservationFrame
except ImportError:
    CognitiveCore = None
    BrainObservationFrame = None

app = FastAPI(title="SOPH Gateway", version="0.2")

class PendingAction:
    def __init__(self, request_id: str, intent: str, target: Optional[str], expected_effect: dict, timeout_seconds: float):
        self.request_id = request_id
        self.intent = intent
        self.target = target
        self.expected_effect = expected_effect
        self.created_at = time.time()
        self.timeout_seconds = timeout_seconds

    def is_timed_out(self) -> bool:
        return (time.time() - self.created_at) > self.timeout_seconds

class AgentSession:
    def __init__(self, agent_id: str, server_id: str):
        self.agent_id = agent_id
        self.server_id = server_id
        self.last_contact = time.time()
        self.pending_actions: Dict[str, PendingAction] = {}
        
        # Instancia e preserva o CognitiveCore exclusivamente para esta sessão
        if CognitiveCore:
            self.brain = CognitiveCore()
        else:
            self.brain = None

    def process_timeouts(self) -> list:
        """Rastreia ações pendentes e dispara limpezas ou eventos de timeout."""
        timed_out_requests = []
        for req_id, action in list(self.pending_actions.items()):
            if action.is_timed_out():
                timed_out_requests.append(action)
                del self.pending_actions[req_id]
        return timed_out_requests

# Dicionário global de sessões ativas: "agent_id:server_id" -> AgentSession
active_sessions: Dict[str, AgentSession] = {}

def get_or_create_session(agent_id: str, server_id: str) -> AgentSession:
    session_key = f"{agent_id}:{server_id}"
    if session_key not in active_sessions:
        print(f"[Gateway] Criando nova AgentSession para Agent: '{agent_id}' no Server: '{server_id}'")
        active_sessions[session_key] = AgentSession(agent_id, server_id)
    
    session = active_sessions[session_key]
    session.last_contact = time.time()
    return session

@app.post("/tick", response_model=ActionProposalSchema)
async def process_tick(
    frame: ObservationFrameSchema,
    api_key: str = Depends(verify_api_key)
):
    """
    Endpoint protegido por X-API-Key.
    Gerencia sessões, converte contratos de entrada/saída e executa o loop do CognitiveCore.
    """
    # 1. Recupera ou cria a sessão isolada (AgentSession)
    session = get_or_create_session(frame.agent_id, frame.server_id)
    
    # 2. Processa rastreamento de timeouts pendentes
    timed_outs = session.process_timeouts()
    if timed_outs:
        pass

    # 3. Adaptador de Entrada: ObservationFrameSchema -> CognitiveCore.ObservationFrame
    if BrainObservationFrame:
        brain_obs = BrainObservationFrame(
            timestamp=frame.timestamp,
            entities=[e.model_dump() for e in frame.entities],
            objects=[o.model_dump() for o in frame.objects],
            events=[ev.model_dump() for ev in frame.events]
        )
    else:
        brain_obs = None

    # 4. Execução através do CognitiveCore preservado na sessão
    intent = "idle"
    target_id = None
    parameters = {}
    expected_effect_data = {}
    timeout_seconds = 3.0

    if session.brain and hasattr(session.brain, "tick") and brain_obs:
        try:
            # Chama o método tick() original do cérebro com o objeto adaptado
            brain_proposal = session.brain.tick(brain_obs)
            
            if brain_proposal:
                intent = getattr(brain_proposal, "intent", "idle")
                target_id = getattr(brain_proposal, "target", None) or getattr(brain_proposal, "target_id", None)
                parameters = getattr(brain_proposal, "parameters", {})
                
                raw_effect = getattr(brain_proposal, "expected_effect", {})
                if isinstance(raw_effect, dict):
                    expected_effect_data = raw_effect
                elif hasattr(raw_effect, "__dict__"):
                    expected_effect_data = raw_effect.__dict__
                
                if "timeout_seconds" in expected_effect_data:
                    timeout_seconds = float(expected_effect_data["timeout_seconds"])
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro interno no processamento cognitivo: {str(e)}"
            )

    request_id = f"tick_{frame.frame_id}"

    # 5. Constrói o ExpectedEffectSchema de resposta com base na proposta do cérebro
    expected_effect = ExpectedEffectSchema(
        target_id=expected_effect_data.get("target_id") or expected_effect_data.get("target") or target_id,
        state=expected_effect_data.get("state"),
        timeout_seconds=timeout_seconds
    )

    # 6. Registra a ação pendente no gerenciador de timeouts da sessão
    session.pending_actions[request_id] = PendingAction(
        request_id=request_id,
        intent=intent,
        target=target_id,
        expected_effect=expected_effect.model_dump(),
        timeout_seconds=timeout_seconds
    )

    # 7. Adaptador de Saída: ActionProposal do Cérebro -> ActionProposalSchema do Gateway
    return ActionProposalSchema(
        protocol_version="0.2",
        request_id=request_id,
        intent=intent,
        target_id=target_id,
        parameters=parameters,
        expected_effect=expected_effect
    )