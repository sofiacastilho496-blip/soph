import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

# ==========================================
# 1. EPISTEMOLOGIA E INTERPRETAÇÃO TRI-STATE
# ==========================================
class EpistemicType(Enum):
    FACT = "EU_SEI"
    HYPOTHESIS = "EU_ACHO"
    UNKNOWN = "EU_NAO_SEI"
    NEED_TO_OBSERVE = "PRECISO_OBSERVAR"

class EvalResult(Enum):
    SUCCESS = "SUCESSO"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVO"

@dataclass
class ObservationFrame:
    timestamp: float
    entities: List[Dict[str, Any]]
    objects: List[Dict[str, Any]]
    events: List[Dict[str, Any]]

@dataclass
class ActionProposal:
    """
    Contrato público canônico M2 v0.2.
    Regras estritas:
    - O campo legado 'target' NÃO existe.
    - target_id é exclusivamente str ou None.
    - parameters é sempre um dict.
    - expected_effect possui exatamente: target_id, state, timeout_seconds (float).
    """
    intent: str
    target_id: Optional[str]
    parameters: Dict[str, Any]
    expected_effect: Dict[str, Any]

@dataclass
class PlanStep:
    intent: str
    target_id: Optional[str]
    expected_effect: Dict[str, Any]

class Interpreter:
    """Interpretador metacognitivo tri-state (Sucesso, Falha, ou Inconclusivo)"""
    def evaluate(self, expected: Dict[str, Any], obs: ObservationFrame) -> EvalResult:
        if not expected:
            return EvalResult.SUCCESS

        target_id = expected.get("target_id")
        expected_state = expected.get("state")

        # --------------------------------------
        # Ação sem alvo físico
        # --------------------------------------
        if target_id is None:
            if expected_state is None:
                return EvalResult.SUCCESS

            for event in obs.events:
                event_target = event.get("target_id") or event.get("target")
                if event_target is None and event.get("state") == expected_state:
                    return EvalResult.SUCCESS

            return EvalResult.INCONCLUSIVE

        # --------------------------------------
        # Verifica se o alvo continua perceptível
        # --------------------------------------
        target_in_view = (
            any(obj.get("id") == target_id for obj in obs.objects) or
            any(ent.get("id") == target_id for ent in obs.entities)
        )

        if not target_in_view:
            return EvalResult.INCONCLUSIVE  # Ausência de evidência não é falha.

        # --------------------------------------
        # Procura evidência explícita do evento
        # --------------------------------------
        for event in obs.events:
            event_target = event.get("target_id") or event.get("target")
            if event_target == target_id and event.get("state") == expected_state:
                return EvalResult.SUCCESS

        return EvalResult.FAIL

# ==========================================
# 2. WORLD MODEL RELACIONAL
# ==========================================
@dataclass
class Node:
    id: str
    properties: Dict[str, Any]
    epistemic_state: EpistemicType

@dataclass
class Relation:
    source: str
    predicate: str
    target: str
    epistemic_state: EpistemicType

class RelationalWorldModel:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Relation] = []

    def update_from_obs(self, obs: ObservationFrame):
        for obj in obs.objects:
            obj_id = obj["id"]
            if obj_id not in self.nodes:
                self.nodes[obj_id] = Node(
                    id=obj_id,
                    properties=dict(obj),
                    epistemic_state=EpistemicType.NEED_TO_OBSERVE
                )
            else:
                self.nodes[obj_id].properties.update(obj)

            if "near_to" in obj:
                self.edges.append(
                    Relation(
                        source=obj_id,
                        predicate="is_near",
                        target=obj["near_to"],
                        epistemic_state=EpistemicType.FACT
                    )
                )

# ==========================================
# 3. MEMÓRIA PROCEDURAL E SINTETIZADOR
# ==========================================
class ActionSynthesizer:
    def synthesize(self, target: str, epistemic_state: EpistemicType, creativity: float) -> str:
        if epistemic_state == EpistemicType.NEED_TO_OBSERVE:
            return "approach_then_inspect"
        elif epistemic_state == EpistemicType.HYPOTHESIS and creativity > 0.7:
            return "test_alternative_mechanism"
        return "force_interaction"

class ProceduralMemory:
    def __init__(self):
        # strategies[goal][context][strategy_name] = success_rate
        self.strategies: Dict[str, Dict[str, Dict[str, float]]] = {}
        self.synthesizer = ActionSynthesizer()

    def get_strategy(self, goal: str, context: str, epistemic_state: EpistemicType, creativity: float, frustration: float) -> str:
        context_strats = (
            self.strategies
            .setdefault(goal, {})
            .setdefault(context, {"interact": 0.2})
        )
        
        best_name, best_score = max(
            context_strats.items(),
            key=lambda x: x[1]
        )
        
        if best_score < 0.4 and (creativity * frustration) > 0.3:
            novel_strategy = self.synthesizer.synthesize(context, epistemic_state, creativity)
            context_strats.setdefault(novel_strategy, 0.5)
            return novel_strategy
            
        return best_name

    def update(self, goal: str, context: str, strategy: str, result: EvalResult):
        if result == EvalResult.INCONCLUSIVE:
            return  
            
        context_strats = (
            self.strategies
            .setdefault(goal, {})
            .setdefault(context, {strategy: 0.5})
        )
        current_score = context_strats.get(strategy, 0.5)
        
        if result == EvalResult.SUCCESS:
            context_strats[strategy] = min(1.0, current_score + 0.2)
        elif result == EvalResult.FAIL:
            context_strats[strategy] = max(0.0, current_score - 0.25)

# ==========================================
# 4. NÚCLEO COGNITIVO (COGNITIVE CORE)
# ==========================================
@dataclass
class Personality:
    curiosity: float = 0.78
    creativity: float = 0.82
    stubbornness: float = 0.64
    patience: float = 0.31

class CognitiveCore:
    PUBLIC_INTENTS = {"idle", "approach", "interact", "wander", "communicate"}

    def __init__(self):
        self.personality = Personality()
        self.world = RelationalWorldModel()
        self.procedural = ProceduralMemory()
        self.interpreter = Interpreter()
        
        self.active_goal: Optional[str] = None
        self.active_plan: List[PlanStep] = []
        self.plan_failures = 0
        self.last_action: Optional[ActionProposal] = None

    def _normalize_action(self, step: PlanStep) -> ActionProposal:
        """
        Camada de normalização estrita: transforma intenções/estratégias internas
        exclusivamente no contrato canônico de saída v0.2.
        """
        intent = step.intent
        target_id = step.target_id

        if target_id is not None and not isinstance(target_id, str):
            target_id = str(target_id) if target_id else None

        if intent == "idle":
            return ActionProposal(
                intent="idle",
                target_id=None,
                parameters={},
                expected_effect={"target_id": None, "state": None, "timeout_seconds": 1.0}
            )
        elif intent in ("basic_interact", "interact"):
            return ActionProposal(
                intent="interact",
                target_id=target_id,
                parameters={},
                expected_effect={"target_id": target_id, "state": "interacted", "timeout_seconds": 3.0}
            )
        elif intent == "approach":
            return ActionProposal(
                intent="approach",
                target_id=target_id,
                parameters={},
                expected_effect={"target_id": target_id, "state": "near", "timeout_seconds": 5.0}
            )
        elif intent == "wander":
            return ActionProposal(
                intent="wander",
                target_id=None,
                parameters={},
                expected_effect={"target_id": None, "state": "moving", "timeout_seconds": 3.0}
            )
        elif intent == "communicate":
            return ActionProposal(
                intent="communicate",
                target_id=target_id,
                parameters={},
                expected_effect={"target_id": target_id, "state": "sent", "timeout_seconds": 2.0}
            )
        elif intent == "inspect":
            return ActionProposal(
                intent="interact",
                target_id=target_id,
                parameters={"mode": "inspect"},
                expected_effect={"target_id": target_id, "state": "observed", "timeout_seconds": 3.0}
            )
        elif intent == "force_interaction":
            return ActionProposal(
                intent="interact",
                target_id=target_id,
                parameters={"execution_mode": "force"},
                expected_effect={"target_id": target_id, "state": "forced", "timeout_seconds": 4.0}
            )
        elif intent == "test_alternative_mechanism":
            return ActionProposal(
                intent="interact",
                target_id=target_id,
                parameters={"execution_mode": "alternative"},
                expected_effect={"target_id": target_id, "state": "tested", "timeout_seconds": 3.0}
            )
        else:
            return ActionProposal(
                intent="idle",
                target_id=None,
                parameters={},
                expected_effect={"target_id": None, "state": None, "timeout_seconds": 1.0}
            )

    def tick(self, observation: ObservationFrame) -> ActionProposal:
        self.world.update_from_obs(observation)

        # 1. INTERPRETAÇÃO E APRENDIZADO
        if self.last_action and self.active_goal:
            eval_result = self.interpreter.evaluate(self.last_action.expected_effect, observation)
            context = str(self.last_action.target_id) if self.last_action.target_id else "global"
            
            self.procedural.update(self.active_goal, context, self.last_action.intent, eval_result)
            
            if eval_result == EvalResult.FAIL:
                self.plan_failures += 1
                tolerance = (self.personality.stubbornness * 4) - ((1.0 - self.personality.patience) * 2)
                if self.plan_failures > max(1, int(tolerance)):
                    self.active_plan = []
                    self.active_goal = None
            elif eval_result == EvalResult.SUCCESS:
                self.plan_failures = 0
                if self.active_plan:
                    self.active_plan.pop(0)

        # 2. PLANEJAMENTO MULTI-STEP
        if not self.active_plan and observation.objects:
            self.active_goal = "investigate"
            target_id = observation.objects[0]["id"]
            
            node = self.world.nodes.get(target_id)
            epistemic_state = node.epistemic_state if node else EpistemicType.NEED_TO_OBSERVE
            
            frustration = min(1.0, self.plan_failures * 0.3)
            strategy = self.procedural.get_strategy(
                self.active_goal, target_id, epistemic_state, 
                self.personality.creativity, frustration=frustration
            )
            
            # Decomposição de macroestratégias
            if strategy == "approach_then_inspect":
                self.active_plan.extend([
                    PlanStep("approach", target_id, {"target_id": target_id, "state": "near"}),
                    PlanStep("inspect", target_id, {"target_id": target_id, "state": "observed"})
                ])
            else:
                self.active_plan.append(PlanStep(strategy, target_id, {"target_id": target_id, "state": "interacted"}))

        # 3. SELEÇÃO DO PASSO ATUAL
        step = self.active_plan[0] if self.active_plan else PlanStep("idle", None, {})
        proposal = self._normalize_action(step)
        
        if proposal.intent not in self.PUBLIC_INTENTS:
            proposal = self._normalize_action(PlanStep("idle", None, {}))

        self.last_action = proposal
        return proposal

# ==========================================
# 5. TESTES UNITÁRIOS RIGOROSOS M2
# ==========================================
def assert_canonical_proposal(proposal: ActionProposal):
    assert hasattr(proposal, "intent")
    assert hasattr(proposal, "target_id")
    assert hasattr(proposal, "parameters")
    assert hasattr(proposal, "expected_effect")
    assert not hasattr(proposal, "target"), "ERRO: O campo legado 'target' foi detectado."

    allowed_intents = {"idle", "approach", "interact", "wander", "communicate"}
    assert proposal.intent in allowed_intents, f"ERRO: Intent público inválido: {proposal.intent}"

    assert isinstance(proposal.target_id, (str, type(None)))
    assert isinstance(proposal.expected_effect, dict)
    assert set(proposal.expected_effect.keys()) == {"target_id", "state", "timeout_seconds"}
    assert isinstance(proposal.expected_effect["timeout_seconds"], float)
    assert isinstance(proposal.parameters, dict)

def test_all_five_public_intents():
    print(">>> TESTE 1: Validação explícita dos 5 intents públicos canônicos")
    brain = CognitiveCore()

    p_idle = brain._normalize_action(PlanStep("idle", None, {}))
    assert_canonical_proposal(p_idle)
    assert p_idle.intent == "idle"

    p_approach = brain._normalize_action(PlanStep("approach", "obj_box_1", {}))
    assert_canonical_proposal(p_approach)
    assert p_approach.intent == "approach"
    assert p_approach.target_id == "obj_box_1"

    p_interact = brain._normalize_action(PlanStep("interact", "obj_box_1", {}))
    assert_canonical_proposal(p_interact)
    assert p_interact.intent == "interact"

    p_wander = brain._normalize_action(PlanStep("wander", "obj_ignore", {}))
    assert_canonical_proposal(p_wander)
    assert p_wander.intent == "wander"
    assert p_wander.target_id is None

    p_comm = brain._normalize_action(PlanStep("communicate", "ent_p2", {}))
    assert_canonical_proposal(p_comm)
    assert p_comm.intent == "communicate"
    assert p_comm.target_id == "ent_p2"

    print("[PASSOU] Teste 1 concluído.\n")

def test_internal_normalizations_and_unknown():
    print(">>> TESTE 2: Normalizações internas e estratégia desconhecida")
    brain = CognitiveCore()

    p_insp = brain._normalize_action(PlanStep("inspect", "obj_x", {}))
    assert_canonical_proposal(p_insp)
    assert p_insp.intent == "interact"
    assert p_insp.parameters == {"mode": "inspect"}

    p_force = brain._normalize_action(PlanStep("force_interaction", "obj_y", {}))
    assert_canonical_proposal(p_force)
    assert p_force.intent == "interact"
    assert p_force.parameters == {"execution_mode": "force"}

    p_alt = brain._normalize_action(PlanStep("test_alternative_mechanism", "obj_z", {}))
    assert_canonical_proposal(p_alt)
    assert p_alt.intent == "interact"
    assert p_alt.parameters == {"execution_mode": "alternative"}

    p_unknown = brain._normalize_action(PlanStep("hack_exploit_intent", "obj_bad", {}))
    assert_canonical_proposal(p_unknown)
    assert p_unknown.intent == "idle"
    assert p_unknown.target_id is None

    print("[PASSOU] Teste 2 concluído.\n")

def test_approach_then_inspect_multistep_real():
    print(">>> TESTE 3: Plano multi-step atômico real (approach -> interact + mode=inspect)")
    brain = CognitiveCore()
    brain.personality.creativity = 0.9
    
    # Força estado epistêmico e falhas para acionar organicamente o sintetizador
    obs_initial = ObservationFrame(0.0, [], [{"id": "obj_door_99"}], [])
    brain.world.update_from_obs(obs_initial)
    brain.world.nodes["obj_door_99"].epistemic_state = EpistemicType.NEED_TO_OBSERVE
    
    brain.plan_failures = 2 
    brain.procedural.strategies = {"investigate": {"obj_door_99": {"interact": 0.2}}}

    # Tick 1: Deve gerar approach
    act1 = brain.tick(obs_initial)
    assert_canonical_proposal(act1)
    assert act1.intent == "approach"
    assert act1.target_id == "obj_door_99"

    # Tick 2: Simula sucesso do approach (evento de proximidade 'near')
    obs_near = ObservationFrame(1.0, [], [{"id": "obj_door_99"}], [{"target_id": "obj_door_99", "state": "near"}])
    act2 = brain.tick(obs_near)
    assert_canonical_proposal(act2)
    assert act2.intent == "interact"
    assert act2.parameters.get("mode") == "inspect"

    assert act1.intent != "approach_then_inspect"
    assert act2.intent != "approach_then_inspect"

    print("[PASSOU] Teste 3 concluído.\n")

def test_inconclusive_no_penalty():
    print(">>> TESTE 4: Ciclo INCONCLUSIVE garante ausência de penalização procedural")
    brain = CognitiveCore()
    brain.active_goal = "investigate"
    
    brain.active_plan = [PlanStep("interact", "obj_safe_box", {"target_id": "obj_safe_box", "state": "interacted"})]
    brain.last_action = ActionProposal(
        intent="interact",
        target_id="obj_safe_box",
        parameters={},
        expected_effect={"target_id": "obj_safe_box", "state": "interacted", "timeout_seconds": 3.0}
    )

    obs_away = ObservationFrame(1.0, [], [{"id": "obj_unrelated"}], [])

    before_strategies = dict(brain.procedural.strategies)
    result = brain.interpreter.evaluate(brain.last_action.expected_effect, obs_away)
    
    assert result == EvalResult.INCONCLUSIVE
    
    brain.procedural.update("investigate", "obj_safe_box", "interact", result)
    after_strategies = brain.procedural.strategies

    assert before_strategies == after_strategies, "ERRO: A estratégia foi penalizada incorretamente."
    print("[PASSOU] Teste 4 concluído.\n")

def run_tests_m2():
    print("=== INICIANDO BATERIA DE TESTES RIGOROSOS M2 — SOPH CORE ===\n")
    test_all_five_public_intents()
    test_internal_normalizations_and_unknown()
    test_approach_then_inspect_multistep_real()
    test_inconclusive_no_penalty()
    print("=== TODOS OS TESTES RIGOROSOS M2 FORAM EXECUTADOS E PASSARAM COM SUCESSO! ===")

if __name__ == "__main__":
    run_tests_m2()