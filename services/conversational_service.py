# conversational_service.py
import os
from typing import Optional, Dict, Any
import google.generativeai as genai
from services.agent.lead_agent import LeadAgentService

GEMINI_KEY = os.environ.get("GEMINI_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

if not GEMINI_KEY:
    raise RuntimeError("GEMINI_KEY no definida.")

genai.configure(api_key=GEMINI_KEY)


class ConversationalAgentService:
    def __init__(self):
        self.lead_agent = LeadAgentService()

        # ⛔ YA NO CREES UN "role: system" en generate_content
        # ✅ LO CORRECTO ES system_instruction AQUÍ
        self.model = genai.GenerativeModel(
            GEMINI_MODEL,
            system_instruction=(
                "Eres un asistente inmobiliario profesional, breve y amable. "
                "Usa los datos del lead si están disponibles. "
                "No hagas preguntas innecesarias."
            )
        )

    def _build_user_prompt(self, user_message: str, lead_data: Dict[str, Any]) -> str:
        summary_lines = []

        if lead_data.get("presupuesto"):
            summary_lines.append(f"Presupuesto: {lead_data['presupuesto']}")
        if lead_data.get("zona"):
            summary_lines.append(f"Zona: {lead_data['zona']}")
        if lead_data.get("tipo_propiedad"):
            summary_lines.append(f"Tipo: {lead_data['tipo_propiedad']}")
        if lead_data.get("urgencia"):
            summary_lines.append(f"Urgencia: {lead_data['urgencia']}")
        if lead_data.get("lead_score"):
            summary_lines.append(f"Score: {lead_data['lead_score']}")

        summary = "\n".join(summary_lines) if summary_lines else "No hay datos aún."

        return (
            f"Mensaje del usuario: \"{user_message}\"\n\n"
            f"Datos del lead:\n{summary}\n\n"
            "Responde de forma natural y útil."
        )

    def get_reply(
        self,
        user_message: str,
        contact_key: Optional[str] = None,
        lead_payload: Optional[Dict] = None
    ) -> Dict[str, Any]:

        # 1. Procesar lead e historial
        if lead_payload is None:
            lead_payload = {"mensaje": user_message, "contacto": contact_key}

        result = self.lead_agent.analyze_and_persist(
            lead_payload,
            history_key=contact_key
        )

        # 2. Preparar prompt
        user_prompt = self._build_user_prompt(user_message, result)

        # 3. Llamada correcta a Gemini (solo USER CONTENT)
        response = self.model.generate_content(user_prompt)

        reply = response.text

        return {
            "lead_analysis": result,
            "reply": reply
        }
