# backend/services/analysis/meta_decision.py
"""
Meta Decision Service

Core decision-making logic for Meta-Agent.
Handles weighted voting, agreement calculation, and LLM-based decisions.
Pure functions - no database dependencies.
Used by both production MetaAgent and backtesting notebook.
"""

import logging
import json
from typing import Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


# Default prompt template for Meta-Agent
DEFAULT_META_PROMPT = """You are the Meta-Agent coordinator for OPARLI's gold scalping trading system.

## ROLE & CONTEXT
You coordinate multiple analyst agents (Visual, Technical, Sentiment) to make strategic trading decisions.
You operate in 4 modes: Pre-Trade, Mid-Trade, Post-Trade, and Monthly Evolution.

## MODE 1: PRE-TRADE COORDINATION

**Inputs:**
- Visual Analyst: signal, confidence, analysis
- Technical Analyst: signal, confidence, analysis
- Sentiment Analyst: signal, confidence, analysis
- Current weights: visual={visual_weight:.4f}, technical={technical_weight:.4f}, sentiment={sentiment_weight:.4f}
- Market context: price, volume, regime

**Decision Process:**

1. **Calculate Weighted Score:**
   ```
   weighted_score = (visual_conf × visual_weight) + (technical_conf × tech_weight) + (sentiment_conf × sent_weight)
   ```

2. **Calculate Agreement (IMPORTANT: PASS ≠ Disagreement):**
   - PASS/NEUTRAL = neutral, not opposing
   - Only LONG vs SHORT = conflict
   - Examples:
     - 2 LONG, 1 PASS → agreement = 1.0 (no opposition)
     - 2 LONG, 1 SHORT → agreement = 0.67 (1 opposes)
     - 1 LONG, 1 SHORT, 1 PASS → agreement = 0.5 (evenly split)

3. **Decision Thresholds:**
   - weighted_score ≥ 0.7 AND agreement ≥ 0.5 → TRADE
   - weighted_score ≥ 0.6 AND agreement ≥ 0.67 → TRADE (reduced confidence)
   - Otherwise → PASS

**Output JSON:**
```json
{{
  "decision": "LONG|SHORT|PASS",
  "confidence": 0.75,
  "weighted_score": 0.72,
  "agreement": 0.67,
  "position_size_modifier": 1.0,
  "tp_suggestion": 2680.0,
  "sl_suggestion": 2650.0,
  "reasoning": "Detailed reasoning...",
  "analyst_breakdown": {{
    "visual": {{"signal": "LONG", "confidence": 0.85, "weight_contribution": 0.30}},
    "technical": {{"signal": "LONG", "confidence": 0.70, "weight_contribution": 0.28}},
    "sentiment": {{"signal": "PASS", "confidence": 0.60, "weight_contribution": 0}}
  }}
}}
```

## CONSTRAINTS
- CANNOT override Risk Manager hard limits
- CANNOT exceed max 3 trades/hour
- CANNOT use position size >1.5× base
- IF win rate <45% for 15 trades → MUST return PAUSE decision
- IF daily loss >6% → MUST return CLOSE_ALL decision

## OUTPUT FORMAT
- Always return valid JSON only
- Include detailed reasoning
- Show all calculations
- No markdown code blocks, just raw JSON

---

**Current Mode:** {mode}
**Timestamp:** {timestamp}
**Context:** {context}
"""


class MetaDecisionService:
    """
    Meta-Agent decision-making service.

    Handles:
    - Weighted voting across analyst signals
    - Agreement calculation
    - LLM-based decision making
    - Fallback deterministic decisions

    No database dependencies - weights and prompts provided externally.
    """

    # Default weights
    DEFAULT_WEIGHTS = {
        'visual': 0.35,
        'technical': 0.50,
        'sentiment': 0.15
    }

    # Decision thresholds
    WEIGHTED_SCORE_THRESHOLD_HIGH = 0.7
    WEIGHTED_SCORE_THRESHOLD_LOW = 0.6
    AGREEMENT_THRESHOLD_HIGH = 0.5
    AGREEMENT_THRESHOLD_LOW = 0.67

    def __init__(
        self,
        llm_client=None,
        weights: Dict[str, float] = None,
        prompt_template: str = None
    ):
        """
        Initialize meta decision service.

        Args:
            llm_client: LLM client from llm_provider (optional)
            weights: Analyst weights dict (optional, uses defaults)
            prompt_template: Custom prompt template (optional)
        """
        self.llm_client = llm_client
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self.prompt_template = prompt_template or DEFAULT_META_PROMPT
        self.call_count = 0

    def set_llm_client(self, llm_client):
        """Set or update LLM client"""
        self.llm_client = llm_client

    def set_weights(self, weights: Dict[str, float]):
        """Set or update analyst weights"""
        self.weights = weights

    def set_prompt_template(self, prompt_template: str):
        """Set or update prompt template"""
        self.prompt_template = prompt_template

    def make_decision(
        self,
        visual_analysis: Dict,
        technical_analysis: Dict,
        sentiment_analysis: Optional[Dict] = None,
        market_context: Optional[Dict] = None,
        current_price: Optional[float] = None,
        use_llm: bool = True
    ) -> Dict:
        """
        Make trading decision based on analyst inputs.

        Args:
            visual_analysis: Visual analyst output
            technical_analysis: Technical analyst output
            sentiment_analysis: Sentiment analyst output (optional)
            market_context: Market context dict (optional)
            current_price: Current price (optional)
            use_llm: Whether to use LLM (True) or fallback (False)

        Returns:
            Dict with decision:
            {
                'decision': 'LONG|SHORT|PASS',
                'confidence': 0.0-1.0,
                'weighted_score': 0.0-1.0,
                'agreement': 0.0-1.0,
                'reasoning': '...',
                'analyst_breakdown': {...}
            }
        """
        # Default sentiment if not provided
        if sentiment_analysis is None:
            sentiment_analysis = {'signal': 'PASS', 'confidence': 0.5}

        # Calculate weighted score and agreement (deterministic)
        weighted_score, agreement, breakdown = self.calculate_weighted_score(
            visual_analysis, technical_analysis, sentiment_analysis
        )

        # Use LLM if available and requested
        if use_llm and self.llm_client:
            try:
                decision = self._make_llm_decision(
                    visual_analysis,
                    technical_analysis,
                    sentiment_analysis,
                    market_context,
                    current_price,
                    weighted_score,
                    agreement,
                    breakdown
                )
                return decision
            except Exception as e:
                logger.error(f"LLM decision error: {e}, using fallback")

        # Fallback to deterministic decision
        return self._make_deterministic_decision(
            visual_analysis,
            technical_analysis,
            sentiment_analysis,
            weighted_score,
            agreement,
            breakdown
        )

    def calculate_weighted_score(
        self,
        visual: Dict,
        technical: Dict,
        sentiment: Dict
    ) -> Tuple[float, float, Dict]:
        """
        Calculate weighted score and agreement.

        Args:
            visual: Visual analysis
            technical: Technical analysis
            sentiment: Sentiment analysis

        Returns:
            Tuple of (weighted_score, agreement, breakdown)
        """
        # Extract signals and confidences
        analyses = {
            'visual': visual,
            'technical': technical,
            'sentiment': sentiment
        }

        # Calculate weighted score for each direction
        scores = {'LONG': 0.0, 'SHORT': 0.0}

        for analyst_name, analysis in analyses.items():
            signal = analysis.get('signal', 'NEUTRAL').upper()
            confidence = analysis.get('confidence', 0.0)
            weight = self.weights.get(analyst_name, 0.0)

            if signal in scores:
                scores[signal] += confidence * weight

        weighted_score = max(scores.values())

        # Calculate agreement
        signals = [
            visual.get('signal', 'NEUTRAL').upper(),
            technical.get('signal', 'NEUTRAL').upper(),
            sentiment.get('signal', 'NEUTRAL').upper()
        ]

        long_count = signals.count('LONG')
        short_count = signals.count('SHORT')
        # PASS/NEUTRAL don't count as opposition

        if long_count > short_count:
            opposing = short_count
        elif short_count > long_count:
            opposing = long_count
        else:
            opposing = max(long_count, short_count)

        total = long_count + short_count
        agreement = 1.0 - (opposing / max(total, 1))

        # Build breakdown
        breakdown = {
            'scores': scores,
            'signals': signals,
            'counts': {
                'long': long_count,
                'short': short_count,
                'pass': 3 - long_count - short_count
            }
        }

        return weighted_score, agreement, breakdown

    def _make_llm_decision(
        self,
        visual: Dict,
        technical: Dict,
        sentiment: Dict,
        market_context: Optional[Dict],
        current_price: Optional[float],
        weighted_score: float,
        agreement: float,
        breakdown: Dict
    ) -> Dict:
        """Make decision using LLM"""
        # Build context
        context = {
            'visual': visual,
            'technical': technical,
            'sentiment': sentiment,
            'weights': self.weights,
            'weighted_score': weighted_score,
            'agreement': agreement,
            'breakdown': breakdown,
            'current_price': current_price
        }

        if market_context:
            context['market_context'] = market_context

        # Build prompt
        prompt = self.prompt_template.format(
            visual_weight=self.weights['visual'],
            technical_weight=self.weights['technical'],
            sentiment_weight=self.weights['sentiment'],
            mode="PRE_TRADE",
            timestamp=datetime.now().isoformat(),
            context=json.dumps(context, indent=2)
        )

        # Call LLM
        response = self.llm_client.generate(
            prompt=prompt,
            temperature=0.2,
            max_tokens=1000
        )

        self.call_count += 1

        # Parse response
        decision = self._parse_response(response)

        logger.info(f"✓ Meta decision (LLM): {decision['decision']} "
                   f"(conf: {decision['confidence']:.0%}, "
                   f"score: {decision['weighted_score']:.2f})")

        return decision

    def _parse_response(self, response: str) -> Dict:
        """Parse LLM response"""
        try:
            text = response.strip()

            # Extract JSON from markdown blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            data = json.loads(text.strip())

            return {
                'decision': data.get('decision', 'PASS').upper(),
                'confidence': float(data.get('confidence', 0)),
                'weighted_score': float(data.get('weighted_score', 0)),
                'agreement': float(data.get('agreement', 0)),
                'reasoning': data.get('reasoning', ''),
                'tp_suggestion': data.get('tp_suggestion'),
                'sl_suggestion': data.get('sl_suggestion'),
                'position_size_modifier': data.get('position_size_modifier', 1.0),
                'analyst_breakdown': data.get('analyst_breakdown', {})
            }

        except Exception as e:
            logger.error(f"Parse error: {e}")
            return {
                'decision': 'PASS',
                'confidence': 0,
                'weighted_score': 0,
                'agreement': 0,
                'reasoning': f'Parse error: {e}'
            }

    def _make_deterministic_decision(
        self,
        visual: Dict,
        technical: Dict,
        sentiment: Dict,
        weighted_score: float,
        agreement: float,
        breakdown: Dict
    ) -> Dict:
        """
        Make deterministic decision without LLM.

        Uses threshold-based logic matching the prompt rules.
        """
        # Determine direction
        v_sig = visual.get('signal', 'NEUTRAL').upper()
        t_sig = technical.get('signal', 'NEUTRAL').upper()

        # Priority: Technical > Visual > Sentiment
        if t_sig in ['LONG', 'SHORT']:
            direction = t_sig
        elif v_sig in ['LONG', 'SHORT']:
            direction = v_sig
        else:
            direction = 'PASS'

        # Apply thresholds
        if weighted_score >= self.WEIGHTED_SCORE_THRESHOLD_HIGH and agreement >= self.AGREEMENT_THRESHOLD_HIGH:
            decision = direction
        elif weighted_score >= self.WEIGHTED_SCORE_THRESHOLD_LOW and agreement >= self.AGREEMENT_THRESHOLD_LOW:
            decision = direction
        else:
            decision = 'PASS'

        return {
            'decision': decision,
            'confidence': weighted_score,
            'weighted_score': weighted_score,
            'agreement': agreement,
            'reasoning': 'Deterministic decision (LLM unavailable)',
            'analyst_breakdown': {
                'visual': {'signal': v_sig, 'confidence': visual.get('confidence', 0)},
                'technical': {'signal': t_sig, 'confidence': technical.get('confidence', 0)},
                'sentiment': {'signal': sentiment.get('signal', 'PASS'), 'confidence': sentiment.get('confidence', 0)}
            }
        }


# Singleton instance
_meta_decision_service: Optional[MetaDecisionService] = None


def get_meta_decision_service() -> MetaDecisionService:
    """
    Get singleton instance of MetaDecisionService.

    Returns:
        MetaDecisionService instance
    """
    global _meta_decision_service
    if _meta_decision_service is None:
        _meta_decision_service = MetaDecisionService()
    return _meta_decision_service


def create_meta_decision_service(
    llm_client=None,
    weights: Dict[str, float] = None,
    prompt_template: str = None
) -> MetaDecisionService:
    """
    Create a new MetaDecisionService instance.

    Use this for backtesting or when you need custom configuration.

    Args:
        llm_client: LLM client
        weights: Analyst weights
        prompt_template: Custom prompt template

    Returns:
        New MetaDecisionService instance
    """
    return MetaDecisionService(llm_client, weights, prompt_template)
