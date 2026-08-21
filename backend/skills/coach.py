import json
import logging
from typing import List
from langchain_core.tools import StructuredTool
from flask import g
from .base_skill import BaseSkill
from extensions import db, ctx
from models.distributor import Distributor
from services.ai_coach_service import ai_coach_service, TASK_METADATA

logger = logging.getLogger(__name__)

class CoachSkill(BaseSkill):
    def __init__(self):
        self._name = "coach"
        self._description = "Manage distributor coaching roadmap, achievements, and challenges checklist."

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def get_tools(self) -> List[StructuredTool]:
        return [
            StructuredTool.from_function(
                func=self.update_coach_tasks_status,
                name="update_coach_tasks_status",
                description="[DISTRIBUTOR ONLY] Marks a daily coach challenge/task as completed or incomplete. Use this when the distributor reports their task completion."
            ),
            StructuredTool.from_function(
                func=self.get_coach_roadmap,
                name="get_coach_roadmap",
                description="[DISTRIBUTOR ONLY] Get the distributor's coaching level progress and the status of today's challenges."
            )
        ]

    def update_coach_tasks_status(self, task_id: str, is_completed: bool = True) -> str:
        """
        Update the status of a specific daily challenge task for the distributor.
        
        Args:
            task_id: The ID of the task to update (e.g. 'take_product', 'exercise_30', 'talk_5_people').
            is_completed: Boolean indicating if the task is completed.
        """
        db.session.rollback() # Database Stability Rule
        distributor = getattr(ctx, 'current_company', None)
        if not distributor:
            return "Error: No distributor context found."

        if not distributor.coach_mode_enabled:
            return f"Coach Mode is currently disabled for {distributor.name}."

        tasks_status = dict(distributor.coach_daily_tasks_status or {})
        
        # Helper: if they pass a descriptive name, try to match it with task_id
        matched_id = None
        if task_id in tasks_status:
            matched_id = task_id
        else:
            # Try to match by checking task labels
            for tid in tasks_status.keys():
                labels = TASK_METADATA.get(tid, {})
                if task_id.lower() in [val.lower() for val in labels.values()]:
                    matched_id = tid
                    break
            
            # Simple keyword matching if still not found
            if not matched_id:
                for tid in tasks_status.keys():
                    if tid in task_id or task_id in tid:
                        matched_id = tid
                        break

        if not matched_id:
            return f"Task '{task_id}' not found in today's challenge checklist: {list(tasks_status.keys())}"

        tasks_status[matched_id] = is_completed
        distributor.coach_daily_tasks_status = tasks_status
        
        try:
            db.session.commit()
            status_str = "completado" if is_completed else "pendiente"
            logger.info(f"Distributor {distributor.id} task '{matched_id}' set to {status_str}")
            return f"El reto '{matched_id}' ha sido marcado como {status_str} exitosamente."
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update task status: {e}")
            return f"Error al guardar el estado: {str(e)}"

    def get_coach_roadmap(self) -> str:
        """
        Retrieve the current coach roadmap stats and daily challenges for the distributor.
        """
        db.session.rollback() # Database Stability Rule
        distributor = getattr(ctx, 'current_company', None)
        if not distributor:
            return "Error: No distributor context found."

        if not distributor.coach_mode_enabled:
            return f"Coach Mode is disabled for {distributor.name}."

        level = distributor.herbalife_level or "Distribuidor Independiente"
        progress = distributor.coach_level_progress or 0
        tasks_status = distributor.coach_daily_tasks_status or {}

        lang = distributor.language or 'es'
        lang_key = 'es' if lang == 'es' else 'en'

        tasks_bullets = []
        for tid, is_done in tasks_status.items():
            label = TASK_METADATA.get(tid, {}).get(lang_key, tid)
            status = "✅ Completado" if is_done else "❌ Pendiente"
            tasks_bullets.append(f"- {label} ({tid}): {status}")

        response = (
            f"Roadmap Coach para {distributor.name}:\n"
            f"Nivel en la Escalera del Éxito: {level}\n"
            f"Progreso actual: {progress}%\n"
            f"Retos de hoy:\n" + "\n".join(tasks_bullets)
        )
        return response

    def get_system_prompt_addition(self) -> str:
        """
        Provides guidance instructions for Coach Mode if it is enabled.
        """
        distributor = getattr(ctx, 'current_company', None)
        if not distributor or not distributor.coach_mode_enabled:
            return ""

        level = distributor.herbalife_level or "Distribuidor Independiente"
        
        addition = (
            f"Tienes activado el MODO COACH para acompañar a {distributor.name} en su camino al Equipo del Presidente. "
            f"Su nivel actual es: '{level}'. "
            f"Si el distribuidor te indica que completó algún reto diario (como tomar el producto, hacer ejercicio, hablar con prospectos), "
            f"DEBES usar la herramienta 'update_coach_tasks_status' para registrarlo. "
            f"Sé motivador, entusiasta y apóyalo diariamente en su disciplina de negocio."
        )
        return addition
