import os
from fastapi.testclient import TestClient
from soph.gateway.server import app, active_sessions

# 1. Configura a chave de API esperada no ambiente para o teste
os.environ["SOPH_GATEWAY_API_KEY"] = "integration-secret-key"

client = TestClient(app)

def test_gateway_brain_integration():
    print("--- INICIANDO TESTE DE INTEGRAÇÃO LOCAL: GATEWAY <-> COGNITIVE CORE ---")
    
    headers = {"X-API-Key": "integration-secret-key"}
    
    # Payload v0.2 simulando o ObservationFrame enviado pelo Roblox
    payload = {
        "protocol_version": "0.2",
        "agent_id": "soph_integration_agent",
        "server_id": "test_server_xyz",
        "frame_id": "frame_001",
        "timestamp": 1698765432.1,
        "entities": [],
        "objects": [{"id": "obj_test", "shape": "box", "material": "wood", "distance_studs": 10.0}],
        "events": []
    }

    # -------------------------------------------------------------
    # 1. Validação de Segurança (X-API-Key)
    # -------------------------------------------------------------
    response_no_auth = client.post("/tick", json=payload)
    assert response_no_auth.status_code == 401, "O Gateway deveria rejeitar requisições sem X-API-Key."
    print("[PASSOU] Autenticação: Requisição sem chave foi bloqueada corretamente (401).")

    # -------------------------------------------------------------
    # 2. Execução do Ticks e Conversão de Schemas (Entrada e Saída)
    # -------------------------------------------------------------
    response = client.post("/tick", json=payload, headers=headers)
    assert response.status_code == 200, f"O tick falhou com status {response.status_code}: {response.text}"
    
    data = response.json()
    assert data["protocol_version"] == "0.2"
    assert "request_id" in data
    assert "intent" in data
    print(f"[PASSOU] Execução & Schema: CognitiveCore.tick() executado com sucesso. Resposta gerada: intent='{data['intent']}'")

    # -------------------------------------------------------------
    # 3. Verificação de Persistência e Isolamento da Sessão (AgentSession)
    # -------------------------------------------------------------
    session_key = "soph_integration_agent:test_server_xyz"
    assert session_key in active_sessions, "A AgentSession deveria estar registrada no gerenciador global."
    
    session_obj = active_sessions[session_key]
    assert session_obj.brain is not None, "O CognitiveCore deve estar instanciado e preservado dentro da sessão."
    
    brain_instance_id_1 = id(session_obj.brain)
    print(f"[PASSOU] Instanciação de Sessão: AgentSession criada. ID do CognitiveCore na RAM: {brain_instance_id_1}")

    # -------------------------------------------------------------
    # 4. Verificação de Reutilização de Estado (Segundo Tick na mesma sessão)
    # -------------------------------------------------------------
    payload["frame_id"] = "frame_002"
    payload["timestamp"] = 1698765433.1
    
    response_tick_2 = client.post("/tick", json=payload, headers=headers)
    assert response_tick_2.status_code == 200
    
    brain_instance_id_2 = id(session_obj.brain)
    assert brain_instance_id_1 == brain_instance_id_2, "O CognitiveCore foi reinanciado incorretamente! A sessão deveria reutilizar a mesma instância."
    print(f"[PASSOU] Persistência de Estado: Segundo tick reutilizou exatamente a mesma instância do cérebro (ID: {brain_instance_id_2}).")

    print("\n--- SUCESSO TOTAL: O CÉREBRO EXISTENTE ESTÁ VIVO E INTEGRADO AO GATEWAY! ---")

if __name__ == "__main__":
    test_gateway_brain_integration()