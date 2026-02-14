"""
Sentiment Analysis Service
Analyzes message sentiment using LLM with keyword-based fallback.
Inspired by OnePunch architecture.

Migration Path: Sentiment models will be locally trained for privacy-sovereign analysis.
"""
import json
import logging
from typing import Dict, Any, List
from flask import current_app

logger = logging.getLogger(__name__)


class SentimentService:
    """
    Sentiment analysis engine for conversation monitoring.
    Detects frustration, escalation risk, and emotional trends.
    """
    
    POSITIVE = 'positive'
    NEUTRAL = 'neutral'
    NEGATIVE = 'negative'

    # Keywords that indicate the user wants a human or is very upset
    ESCALATION_KEYWORDS_ES = [
        'hablar con humano', 'persona real', 'gerente', 'supervisor',
        'queja', 'denuncia', 'demanda', 'abogado', 'legal',
        'furioso', 'enojado', 'molesto', 'frustrado',
        'cancelar', 'reembolso', 'devolver dinero', 'estafa',
    ]
    ESCALATION_KEYWORDS_EN = [
        'speak to human', 'real person', 'manager', 'supervisor',
        'complaint', 'lawsuit', 'lawyer', 'legal action',
        'angry', 'upset', 'frustrated', 'furious',
        'cancel', 'refund', 'money back', 'scam',
    ]
    ESCALATION_KEYWORDS = ESCALATION_KEYWORDS_ES + ESCALATION_KEYWORDS_EN

    # Simple word lists for fallback
    POSITIVE_WORDS = [
        'gracias', 'excelente', 'genial', 'perfecto', 'bueno', 'encanta', 'increíble', 'maravilloso',
        'thank', 'great', 'excellent', 'perfect', 'good', 'love', 'amazing', 'wonderful',
    ]
    NEGATIVE_WORDS = [
        'malo', 'terrible', 'horrible', 'odio', 'peor', 'nunca', 'pésimo', 'basura',
        'bad', 'terrible', 'horrible', 'hate', 'worst', 'never', 'awful', 'trash',
    ]

    def __init__(self, distributor=None):
        self.distributor = distributor
        self._llm_service = None

    def _get_llm_service(self):
        """Lazy-load LLM service."""
        if not self._llm_service:
            from services.llm_service import llm_service
            self._llm_service = llm_service
        return self._llm_service

    # ------------------------------------------------------------------ #
    #  PUBLIC API                                                         #
    # ------------------------------------------------------------------ #

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of a single message.
        Returns dict with score (-1..1), category, confidence, escalation_risk, emotions.
        """
        if not text or not text.strip():
            return self._neutral_result("Empty text")

        text_lower = text.lower()
        has_escalation = any(kw in text_lower for kw in self.ESCALATION_KEYWORDS)

        try:
            llm = self._get_llm_service()
            prompt = (
                f'Analyze the sentiment of this message and respond ONLY with valid JSON:\n'
                f'Message: "{text}"\n\n'
                f'{{"score": <float -1.0 to 1.0>, "category": "<positive|neutral|negative>", '
                f'"confidence": <float 0-1>, "reasoning": "<brief>", '
                f'"escalation_risk": <true|false>, "emotions": ["<list>"]}}'
            )
            raw = llm.generate(
                prompt=prompt,
                system_prompt="You are a sentiment analysis expert. Respond with valid JSON only.",
                model='gpt-5-nano',
                temperature=0.1,
                max_tokens=200,
            )
            # Strip markdown fences if present
            content = raw.strip()
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
            result = json.loads(content.strip())
            result.setdefault('score', 0.0)
            result.setdefault('category', self.NEUTRAL)
            result.setdefault('confidence', 0.8)
            result.setdefault('reasoning', '')
            result.setdefault('escalation_risk', has_escalation)
            result.setdefault('emotions', [])
            if has_escalation:
                result['escalation_risk'] = True
            return result

        except Exception as e:
            logger.warning(f"LLM sentiment failed, using fallback: {e}")
            return self._fallback_analysis(text, has_escalation)

    def analyze_conversation(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Aggregate sentiment over a conversation (analyzes last 5 user messages).
        Returns overall_score, trend (improving/declining/stable), and escalation_risk.
        """
        user_msgs = [m for m in messages if m.get('role') == 'user']
        if not user_msgs:
            return {'overall_score': 0.0, 'overall_category': self.NEUTRAL, 'trend': 'stable', 'escalation_risk': False}

        sentiments = [self.analyze_text(m.get('content', '')) for m in user_msgs[-5:]]
        scores = [s['score'] for s in sentiments]
        avg = sum(scores) / len(scores)

        # Trend
        if len(scores) >= 2:
            mid = len(scores) // 2
            first_avg = sum(scores[:mid]) / mid
            second_avg = sum(scores[mid:]) / (len(scores) - mid)
            trend = 'improving' if second_avg > first_avg + 0.2 else ('declining' if second_avg < first_avg - 0.2 else 'stable')
        else:
            trend = 'stable'

        category = self.POSITIVE if avg > 0.3 else (self.NEGATIVE if avg < -0.3 else self.NEUTRAL)
        escalation = any(s.get('escalation_risk') for s in sentiments)

        return {
            'overall_score': round(avg, 2),
            'overall_category': category,
            'trend': trend,
            'escalation_risk': escalation,
        }

    def should_escalate(self, result: Dict[str, Any]) -> bool:
        """Determine if a human should take over based on sentiment."""
        if result.get('escalation_risk'):
            return True
        score = result.get('score') or result.get('overall_score', 0)
        if score < -0.7:
            return True
        if result.get('trend') == 'declining' and score < -0.3:
            return True
        return False

    # ------------------------------------------------------------------ #
    #  INTERNAL                                                           #
    # ------------------------------------------------------------------ #

    def _neutral_result(self, reason: str) -> Dict[str, Any]:
        return {'score': 0.0, 'category': self.NEUTRAL, 'confidence': 1.0, 'reasoning': reason,
                'escalation_risk': False, 'emotions': []}

    def _fallback_analysis(self, text: str, has_escalation: bool) -> Dict[str, Any]:
        """Keyword-based fallback when LLM is unavailable."""
        text_lower = text.lower()
        pos = sum(1 for w in self.POSITIVE_WORDS if w in text_lower)
        neg = sum(1 for w in self.NEGATIVE_WORDS if w in text_lower)

        if neg > pos:
            score = max(-1.0, -0.5 - 0.1 * min(neg, 5))
            category = self.NEGATIVE
        elif pos > neg:
            score = min(1.0, 0.5 + 0.1 * min(pos, 5))
            category = self.POSITIVE
        else:
            score, category = 0.0, self.NEUTRAL

        return {
            'score': score, 'category': category, 'confidence': 0.5,
            'reasoning': 'Keyword-based fallback', 'escalation_risk': has_escalation or score < -0.5,
            'emotions': [],
        }
