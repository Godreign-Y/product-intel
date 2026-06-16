import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, Any, List
from src.core.history.storage.models import Experiment, Report
from src.utils.logger import setup_logger

logger = setup_logger("report_generator")

class ReportGenerator:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("NVIDIA_API_KEY")
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self.model = "meta/llama-3.1-70b-instruct"
        
        if not self.api_key:
            logger.warning("NVIDIA_API_KEY not found. ReportGenerator will use deterministic template fallbacks.")
            self.client = None
        else:
            self.client = OpenAI(base_url=self.base_url, api_key=self.api_key, timeout=None)

    def generate_report(self, exp: Experiment) -> Report:
        """
        Creates a structured Report object for an experiment, calling NVIDIA NIM or falling back to templated content.
        """
        before_str = ", ".join([f"{k}: {v}" for k, v in exp.before_metrics.items()])
        after_str = ", ".join([f"{k}: {v}" for k, v in exp.after_metrics.items()])
        
        # Calculate percentage changes for baseline prompt context
        deltas = {}
        for k in exp.before_metrics.keys():
            before_val = exp.before_metrics[k]
            after_val = exp.after_metrics[k]
            if before_val > 0:
                pct = ((after_val - before_val) / before_val) * 100.0
                deltas[k] = f"{'+' if pct > 0 else ''}{pct:.2f}%"
            else:
                deltas[k] = "0.0%"

        if not self.client:
            return self._generate_fallback_report(exp, deltas)
            
        system_prompt = (
            "You are a professional Business Intelligence Analyst.\n"
            "Analyze the given experiment metadata and metrics to produce a detailed experiment audit report.\n"
            "The output MUST be a valid JSON object containing exactly two fields:\n"
            "1. \"structured_json\": an object with the fields:\n"
            "   - \"business_context\": A summary of the market situation or reason for the experiment.\n"
            "   - \"changes_made\": What changes were made to the price, discount, marketing, or shipping fee.\n"
            "   - \"observed_kpi_changes\": Dictionary mapping KPIs to percentage changes (e.g. {\"revenue\": \"+12.4%\"}).\n"
            "   - \"positive_effects\": List of positive impacts observed.\n"
            "   - \"negative_effects\": List of negative impacts observed.\n"
            "   - \"learnings\": Core business lessons learned.\n"
            "   - \"recommendations\": Recommended next steps for future strategy.\n"
            "2. \"human_readable_text\": A polished markdown report containing headers, bullets, and summary tables.\n\n"
            "Ensure the output is clean JSON. Do not prepend markdown formatting code blocks unless they encapsulate the JSON itself. Do not write text before or after the JSON."
        )
        
        prompt = (
            f"Experiment Name: {exp.type}\n"
            f"Product: {exp.product_ids}\n"
            f"Category: {exp.category}\n"
            f"Change Summary: {exp.change_summary}\n"
            f"Start Date: {exp.start_date.strftime('%Y-%m-%d')}\n"
            f"End Date: {exp.end_date.strftime('%Y-%m-%d')}\n"
            f"Pre-Experiment Averages: {before_str}\n"
            f"Post-Experiment Averages: {after_str}\n"
            f"Calculated Metric Deltas: {json.dumps(deltas)}\n"
            f"Statistical Outcome: {exp.outcome} (Confidence: {exp.confidence_score*100:.1f}%)\n"
            f"KPI Improvement %: {exp.improvement_pct}%\n"
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
            raw_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
            else:
                data = json.loads(raw_text)
                
            return Report(
                structured_json=data.get("structured_json"),
                human_readable_text=data.get("human_readable_text")
            )
            
        except Exception as e:
            logger.error(f"LLM Report generation failed for {exp.experiment_id}: {e}. Using fallback templates.")
            return self._generate_fallback_report(exp, deltas)

    def _generate_fallback_report(self, exp: Experiment, deltas: Dict[str, str]) -> Report:
        """
        Creates a structured report using local string templates.
        """
        target_kpi = "conversion_rate"
        if "Spend" in exp.type or "Pricing" in exp.type:
            target_kpi = "revenue"
        elif "Discount" in exp.type:
            target_kpi = "profit"
            
        target_change = deltas.get(target_kpi, "0.0%")
        outcome_sign = "positive" if exp.improvement_pct > 0 else "negative" if exp.improvement_pct < 0 else "stable"
        
        structured_json = {
            "business_context": f"Audit analysis of {exp.type} testing pricing, spend or discount elasticity for product {exp.product_ids}.",
            "changes_made": exp.change_summary,
            "observed_kpi_changes": deltas,
            "positive_effects": [
                f"{kpi.replace('_', ' ').title()} changed by {val}"
                for kpi, val in deltas.items() if not val.startswith("-") and val != "0.0%"
            ],
            "negative_effects": [
                f"{kpi.replace('_', ' ').title()} decreased by {val}"
                for kpi, val in deltas.items() if val.startswith("-")
            ],
            "learnings": f"The policy change yielded a {outcome_sign} effect on {target_kpi.replace('_', ' ')} of {target_change}.",
            "recommendations": f"Adopt or revert the change depending on whether margins were successfully maintained during the test period."
        }
        
        md_text = (
            f"# Historical Experiment Report: {exp.type} ({exp.experiment_id})\n\n"
            f"**Testing Window:** {exp.start_date.strftime('%Y-%m-%d')} to {exp.end_date.strftime('%Y-%m-%d')}\n"
            f"**Target Product:** {exp.product_ids} | **Category:** {exp.category}\n\n"
            f"## 1. Executive Summary\n"
            f"{exp.change_summary} The primary objective of the test was to measure impacts on "
            f"**{target_kpi.replace('_', ' ').title()}**, which shifted by **{target_change}** during the test period. "
            f"The trial resulted in a **{exp.outcome.upper()}** business outcome (Statistical Confidence: {exp.confidence_score*100:.1f}%).\n\n"
            f"## 2. KPI Performance Audit Table\n\n"
            f"| Metric | Pre-Experiment Average | Post-Experiment Average | Change (%) |\n"
            f"| :--- | :--- | :--- | :--- |\n"
        )
        
        for k in deltas.keys():
            before_val = exp.before_metrics[k]
            after_val = exp.after_metrics[k]
            # format values nicely
            fmt = ".4f" if k in ["conversion_rate", "retention_rate"] else ",.2f"
            md_text += f"| {k.replace('_', ' ').title()} | {before_val:{fmt}} | {after_val:{fmt}} | {deltas[k]} |\n"
            
        md_text += (
            f"\n## 3. Positive & Negative Impacts\n"
            f"### Positive Impacts\n"
            f" - " + ("\n - ".join(structured_json["positive_effects"]) if structured_json["positive_effects"] else "No positive factors logged.") + "\n"
            f"### Negative Impacts\n"
            f" - " + ("\n - ".join(structured_json["negative_effects"]) if structured_json["negative_effects"] else "No negative factor degradation logged.") + "\n\n"
            f"## 4. Key Learnings & Strategy Recommendation\n"
            f"**Learnings:** {structured_json['learnings']}\n\n"
            f"**Recommendation:** {structured_json['recommendations']}"
        )
        
        return Report(
            structured_json=structured_json,
            human_readable_text=md_text
        )
