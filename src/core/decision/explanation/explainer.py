import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional

from src.core.decision.config_loader import load_decision_config
from src.utils.logger import setup_logger

logger = setup_logger("explanation_engine")

class ExplanationEngine:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("NVIDIA_API_KEY")
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self.model = "meta/llama-3.1-8b-instruct"

        cfg = load_decision_config()
        exp_cfg = cfg.get("explanation", {})
        conf_thresh = cfg.get("confidence_thresholds", {})
        self.llm_timeout = None
        self.high_conf_threshold = conf_thresh.get("high", 0.70)
        
        logger.info(f"Initialized ExplanationEngine: model={self.model}, high_conf_threshold={self.high_conf_threshold}, timeout={self.llm_timeout}")
        if not self.api_key:
            logger.warning("NVIDIA_API_KEY is not defined in the environment. ExplanationEngine will fall back to local templates.")
            self.client = None
        else:
            self.client = OpenAI(base_url=self.base_url, api_key=self.api_key, timeout=self.llm_timeout)

    def generate_explanation(
        self, 
        ranked_items: List[Dict[str, Any]], 
        recommendations: List[Dict[str, Any]]
    ) -> str:
        """
        Synthesizes a business-friendly explanation in Markdown, calling LLM or falling back to a structured template.
        Uses hypothesis_id keyed lookup for safe correlation between ranked items and recommendations.
        """
        logger.info(f"generate_explanation: Compiling executive summary for {len(ranked_items)} ranked hypotheses.")
        if not ranked_items:
            logger.warning("generate_explanation: No active ranked hypotheses. Returning generic header.")
            return "# Decision Engine Explanation\n\nNo active business hypotheses generated for this query."

        # Build hypothesis_id-keyed recommendation lookup (replaces fragile index-based correlation)
        rec_map = {r["hypothesis_id"]: r for r in recommendations}

        # Compile summaries for the prompt/template
        summary_data = []
        for item in ranked_items:
            hypo = item["hypothesis"]
            val = item["validation"]
            conf = item["confidence"]
            rec = rec_map.get(hypo["hypothesis_id"], {})
            
            summary_data.append({
                "hypothesis": hypo["title"],
                "description": hypo["description"],
                "is_primary": hypo.get("is_primary", True),
                "confidence_score": conf["overall_confidence"],
                "expected_impact": rec.get("expected_kpi_improvement", {}),
                "action_recommended": rec.get("recommendation_text", ""),
                "needs_ab_test": rec.get("needs_experimentation", False),
                "rollback_strategy": rec.get("rollback_strategy", ""),
                "risk_assessment": rec.get("risk_assessment", {})
            })

        if not self.client:
            logger.info("generate_explanation: LLM client not instantiated. Using local fallback template.")
            return self._generate_fallback_explanation(summary_data)
            
        system_prompt = (
            "You are an Executive Business Intelligence System.\n"
            "Compile a polished, business-ready executive decision brief based on the validated hypotheses and recommendations.\n"
            "The explanation MUST be formatted in clean GitHub markdown, utilizing headings, lists, bold text, and summary tables.\n"
            "The analytical data contains an 'is_primary' flag for each item. Group the hypotheses and recommendations into two distinct sections:\n"
            "1. Primary Opportunities (where 'is_primary' is true): Focus on these as the direct answers to the user's query.\n"
            "2. Related Opportunities (where 'is_primary' is false): Present these as additional high-value growth levers or risks discovered during analysis.\n"
            "Do not drop the related opportunities; clearly present them in their own section as supplementary recommendations.\n"
            "Break the narrative down into:\n"
            "1. Executive Summary: High-level answers to the business question.\n"
            "2. Validated Hypotheses: Grouped by Primary and Related sections with their supporting metrics and confidence levels.\n"
            "3. Action Recommendations: Practical next steps (rollouts or A/B tests) and rollback guidelines, grouped by Primary and Related.\n"
            "4. Risk Matrix: Grouped by Primary and Related.\n"
            "Make the tone strictly professional, objective, and evidence-focused. Do not add conversational fluff at the beginning or end."
        )
        
        prompt = (
            f"Input Analytical Data:\n{json.dumps(summary_data, indent=2)}\n"
        )
        
        logger.info(f"generate_explanation: Querying LLM '{self.model}' for executive markdown generation.")
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
            raw_content = response.choices[0].message.content.strip()
            logger.info("generate_explanation: Successfully generated executive explanation via Llama API.")
            return raw_content
        except Exception as e:
            # Fall back to template on any error
            logger.error(f"generate_explanation: LLM request failed: {e}. Falling back to structured local markdown template.")
            return self._generate_fallback_explanation(summary_data)

    def _generate_fallback_explanation(self, summary_data: List[Dict[str, Any]]) -> str:
        """
        Generates a robust local template if the LLM is unreachable.
        Organizes hypotheses and recommendations into Primary and Related Opportunities.
        """
        logger.info(f"_generate_fallback_explanation: Formulating local brief for {len(summary_data)} hypotheses.")
        
        # Split into primary and related
        primary = [s for s in summary_data if s.get("is_primary", True)]
        related = [s for s in summary_data if not s.get("is_primary", True)]
        
        md = "# AI Decision Intelligence Engine - Analytical Brief\n\n"
        md += "## 1. Executive Summary\n"
        md += f"We evaluated the business query and validated **{len(summary_data)}** hypotheses using predictive model simulations, elasticity analyses, and correlation checks.\n"
        if primary:
            md += f"- **Primary Opportunities**: We validated {len(primary)} hypotheses directly addressing the target query.\n"
        if related:
            md += f"- **Related Opportunities**: We identified {len(related)} additional high-value growth levers or risks.\n"
            
        high_conf = [s for s in summary_data if s["confidence_score"] >= self.high_conf_threshold]
        if high_conf:
            md += f"\nWe identified **{len(high_conf)}** recommendations with high confidence supporting immediate implementation.\n\n"
        else:
            md += "\nCurrent validation confidence is low/moderate; we recommend running structured pilot experiments before full rollout.\n\n"
            
        def build_matrix_table(items: List[Dict[str, Any]]) -> str:
            table = "| Prioritized Hypothesis | Confidence Score | Expected KPI Impact | Verification Action Required |\n"
            table += "| :--- | :---: | :---: | :--- |\n"
            for s in items:
                impact_str = ", ".join([f"{k}: {v}" for k, v in s["expected_impact"].items()])
                test_req = "A/B Test Pilot" if s["needs_ab_test"] else "Immediate Rollout"
                table += f"| **{s['hypothesis']}** | {s['confidence_score']:.2f} | {impact_str} | {test_req} |\n"
            return table
            
        md += "## 2. Hypothesis & Validation Matrix\n\n"
        if primary:
            md += "### Primary Opportunities\n"
            md += build_matrix_table(primary) + "\n"
        if related:
            md += "### Related Opportunities (Discovered Growth Levers)\n"
            md += build_matrix_table(related) + "\n"
            
        md += "## 3. Detailed Recommendations & Tactical Actions\n"
        if primary:
            md += "\n### Primary Recommendations\n"
            for idx, s in enumerate(primary):
                md += f"\n#### Action P{idx+1}: {s['hypothesis']}\n"
                md += f"* **Rationale**: {s['description']}\n"
                md += f"* **Tactical Action**: {s['action_recommended']}\n"
                md += f"* **Rollback Blueprint**: {s['rollback_strategy']}\n"
        if related:
            md += "\n### Related Opportunity Recommendations\n"
            for idx, s in enumerate(related):
                md += f"\n#### Action R{idx+1}: {s['hypothesis']}\n"
                md += f"* **Rationale**: {s['description']}\n"
                md += f"* **Tactical Action**: {s['action_recommended']}\n"
                md += f"* **Rollback Blueprint**: {s['rollback_strategy']}\n"

        # 4. Risk Matrix
        has_risks = any(s.get("risk_assessment") for s in summary_data)
        if has_risks:
            md += "\n## 4. Risk Matrix\n\n"
            
            def build_risk_table(items: List[Dict[str, Any]]) -> str:
                table = "| Hypothesis | Volatility | Reversibility | Data Confidence | Impact Magnitude |\n"
                table += "| :--- | :---: | :---: | :---: | :---: |\n"
                for s in items:
                    risk = s.get("risk_assessment", {})
                    if risk:
                        data_conf = risk.get('data_confidence', 'N/A')
                        data_conf_str = f"{data_conf:.2f}" if isinstance(data_conf, (int, float)) else str(data_conf)
                        table += (
                            f"| **{s['hypothesis']}** "
                            f"| {risk.get('volatility', 'N/A')} "
                            f"| {risk.get('reversibility', 'N/A')} "
                            f"| {data_conf_str} "
                            f"| {risk.get('impact_magnitude', 'N/A')}% |\n"
                        )
                return table
                
            if primary:
                md += "### Primary Opportunities Risk\n"
                md += build_risk_table(primary) + "\n"
            if related:
                md += "### Related Opportunities Risk\n"
                md += build_risk_table(related) + "\n"
            
        logger.info("_generate_fallback_explanation: Finished compiling fallback brief.")
        return md
