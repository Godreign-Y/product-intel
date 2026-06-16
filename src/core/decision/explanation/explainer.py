import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional

class ExplanationEngine:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("NVIDIA_API_KEY")
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self.model = "meta/llama-3.1-70b-instruct"
        
        if not self.api_key:
            self.client = None
        else:
            self.client = OpenAI(base_url=self.base_url, api_key=self.api_key, timeout=10.0)

    def generate_explanation(
        self, 
        ranked_items: List[Dict[str, Any]], 
        recommendations: List[Dict[str, Any]]
    ) -> str:
        """
        Synthesizes a business-friendly explanation in Markdown, calling LLM or falling back to a structured template.
        """
        if not ranked_items:
            return "# Decision Engine Explanation\n\nNo active business hypotheses generated for this query."

        # Compile summaries for the prompt/template
        summary_data = []
        for idx, item in enumerate(ranked_items):
            hypo = item["hypothesis"]
            val = item["validation"]
            conf = item["confidence"]
            rec = recommendations[idx] if idx < len(recommendations) else {}
            
            summary_data.append({
                "hypothesis": hypo["title"],
                "description": hypo["description"],
                "confidence_score": conf["overall_confidence"],
                "expected_impact": rec.get("expected_kpi_improvement", {}),
                "action_recommended": rec.get("recommendation_text", ""),
                "needs_ab_test": rec.get("needs_experimentation", False),
                "rollback_strategy": rec.get("rollback_strategy", "")
            })

        if not self.client:
            return self._generate_fallback_explanation(summary_data)
            
        system_prompt = (
            "You are an Executive Business Intelligence System.\n"
            "Compile a polished, business-ready executive decision brief based on the validated hypotheses and recommendations.\n"
            "The explanation MUST be formatted in clean GitHub markdown, utilizing headings, lists, bold text, and summary tables.\n"
            "Break the narrative down into:\n"
            "1. Executive Summary: High-level answers to the business question.\n"
            "2. Validated Hypotheses: Details of each hypothesis, supporting metrics, and confidence level.\n"
            "3. Action Recommendations: Practical next steps (rollouts or A/B tests) and rollback guidelines.\n"
            "Make the tone strictly professional, objective, and evidence-focused. Do not add conversational fluff at the beginning or end."
        )
        
        prompt = (
            f"Input Analytical Data:\n{json.dumps(summary_data, indent=2)}\n"
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            return response.choices[0].message.content.strip()
        except Exception:
            # Fall back to template on any error
            return self._generate_fallback_explanation(summary_data)

    def _generate_fallback_explanation(self, summary_data: List[Dict[str, Any]]) -> str:
        """
        Generates a robust local template if the LLM is unreachable.
        """
        md = "# AI Decision Intelligence Engine - Analytical Brief\n\n"
        md += "## 1. Executive Summary\n"
        md += f"We evaluated the business query and validated **{len(summary_data)}** hypotheses using predictive model simulations, elasticity analyses, and correlation checks. "
        
        high_conf = [s for s in summary_data if s["confidence_score"] >= 0.70]
        if high_conf:
            md += f"We identified **{len(high_conf)}** recommendations with high confidence supporting immediate implementation.\n\n"
        else:
            md += "Current validation confidence is low/moderate; we recommend running structured pilot experiments before full rollout.\n\n"
            
        md += "## 2. Hypothesis & Validation Matrix\n\n"
        md += "| Prioritized Hypothesis | Confidence Score | Expected KPI Impact | Verification Action Required |\n"
        md += "| :--- | :---: | :---: | :--- |\n"
        
        for s in summary_data:
            impact_str = ", ".join([f"{k}: {v}" for k, v in s["expected_impact"].items()])
            test_req = "A/B Test Pilot" if s["needs_ab_test"] else "Immediate Rollout"
            md += f"| **{s['hypothesis']}** | {s['confidence_score']:.2f} | {impact_str} | {test_req} |\n"
            
        md += "\n## 3. Detailed Recommendations & Tactical Actions\n"
        
        for idx, s in enumerate(summary_data):
            md += f"\n### Action {idx+1}: {s['hypothesis']}\n"
            md += f"* **Rationale**: {s['description']}\n"
            md += f"* **Tactical Action**: {s['action_recommended']}\n"
            md += f"* **Rollback Blueprint**: {s['rollback_strategy']}\n"
            
        return md
