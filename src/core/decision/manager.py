import datetime
import concurrent.futures
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from src.core.decision.storage.models import DecisionContext, Hypothesis, ValidationResult, ConfidenceScore, Recommendation, ExperimentPlan
from src.core.decision.context.engine import ContextEngine
from src.core.decision.hypothesis.generator import HypothesisGenerator
from src.core.decision.evidence.retriever import EvidenceRetriever
from src.core.decision.validation.validator import ValidationEngine
from src.core.decision.confidence.scorer import ConfidenceScorer
from src.core.decision.ranking.ranker import HypothesisRanker
from src.core.decision.recommendation.engine import RecommendationEngine
from src.core.decision.planner.ab_planner import ExperimentPlanner
from src.core.decision.explanation.explainer import ExplanationEngine

from src.core.forecaster import ProductForecaster
from src.core.sensitivity import SensitivityEngine
from src.core.simulator import ScenarioSimulator
from src.utils.logger import setup_logger

logger = setup_logger("decision_manager")

class DecisionManager:
    def __init__(
        self, 
        db: Session,
        df_historical: Any,
        forecaster: ProductForecaster,
        sensitivity_engine: SensitivityEngine,
        simulator: ScenarioSimulator,
        history_manager: Optional[Any] = None,
        explainer: Optional[Any] = None,
        llm_client: Optional[Any] = None,
    ):
        self.db = db
        
        if explainer is None:
            try:
                from src.api.dependencies import AppState
                explainer = AppState.explainer
                logger.info("Instantiated DecisionManager fallback to AppState explainer.")
            except ImportError:
                logger.warning("Failed importing AppState fallback for explainer in DecisionManager.")
                pass

        if llm_client is None:
            from src.core.llm import get_llm_client
            llm_client = get_llm_client()
                
        self.context_engine = ContextEngine(db)
        self.hypo_generator = HypothesisGenerator(
            db=db,
            forecaster=forecaster,
            explainer=explainer,
            history_manager=history_manager,
            llm_client=llm_client,
        )
        self.evidence_retriever = EvidenceRetriever(db, history_manager)
        self.validator = ValidationEngine(df_historical, forecaster, sensitivity_engine, simulator)
        self.scorer = ConfidenceScorer()
        self.ranker = HypothesisRanker()
        self.rec_engine = RecommendationEngine()
        self.planner = ExperimentPlanner()
        self.explainer = ExplanationEngine(llm_client=llm_client)
        self.df_historical = df_historical
        logger.info("Successfully initialized DecisionManager with all sub-engines.")

    def _get_product_df_len(self, product_id: str) -> int:
        """Returns the number of rows for a given product in the historical DataFrame."""
        try:
            if self.df_historical is not None:
                row_count = len(self.df_historical[self.df_historical["product_id"] == product_id])
                logger.debug(f"_get_product_df_len: Found {row_count} rows for product: {product_id}")
                return row_count
        except Exception as e:
            logger.warning(f"Failed to fetch product historical data length: {e}")
            pass
        return 0

    def process_decision_flow(self, query: str, product_id: str = "P001", session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes the complete AI Scientist decision intelligence loop.
        Now with: product-scoped context, parallel evidence+validation,
        bulk DB flush, data_quality_factor, and context-aware planner.
        """
        logger.info(f"process_decision_flow: Commencing intelligence loop for product_id={product_id}, session_id={session_id}")
        logger.info(f"process_decision_flow: Query: '{query}'")
        try:
            return self._process_decision_flow_body(query, product_id, session_id)
        except Exception as e:
            self.db.rollback()
            logger.error(f"process_decision_flow failed: {e}")
            raise

    def _process_decision_flow_body(self, query: str, product_id: str = "P001", session_id: Optional[str] = None) -> Dict[str, Any]:
        
        # Parse query shock percentage and direction
        import re
        from src.core.decision.direction_utils import parse_query_driver_direction
        from src.core.decision.config_loader import load_decision_config

        query_pcts = {}
        pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", query)
        if pct_match:
            try:
                magnitude = float(pct_match.group(1))
                cfg = load_decision_config()
                valid_drivers = list(cfg.get("elasticity", {}).get("min_driver_delta", {}).keys())
                if not valid_drivers:
                    valid_drivers = ["discount_pct", "shipping_fee", "avg_selling_price", "marketing_spend"]
                
                q_lower = query.lower()
                for driver in valid_drivers:
                    if driver == "discount_pct":
                        kws = ["discount", "promo"]
                        driver_keyword = "discount"
                    elif driver == "shipping_fee":
                        kws = ["shipping", "fee"]
                        driver_keyword = "shipping"
                    elif driver == "avg_selling_price":
                        kws = ["price", "pricing", "cost"]
                        driver_keyword = "price"
                    elif driver == "marketing_spend":
                        kws = ["marketing", "spend", "ads", "budget"]
                        driver_keyword = "marketing"
                    else:
                        kws = [driver.split("_")[0]]
                        driver_keyword = driver.split("_")[0]

                    if any(kw in q_lower for kw in kws):
                        direction = parse_query_driver_direction(query, driver_keyword)
                        if direction != "neutral":
                            signed_pct = magnitude if direction == "positive" else -magnitude
                            query_pcts[driver] = signed_pct
                            logger.info(f"Parsed query shock: driver={driver}, direction={direction}, magnitude={magnitude} -> pct={signed_pct}%")
            except Exception as ex:
                logger.error(f"Failed parsing literal query shock: {ex}")
        
        # Load df_historical once if not pre-loaded to guarantee consistency and avoid race conditions / redundant queries
        if self.df_historical is None:
            logger.info("process_decision_flow: df_historical is None. Loading once from database for consistency.")
            from src.api.dependencies import get_historical_df_from_db
            self.df_historical = get_historical_df_from_db(product_id=product_id)
            self.validator.df = self.df_historical

        # 1. Assemble Business Context — product-scoped
        logger.info("Step 1: Assembling Business Context.")
        context_data = self.context_engine.assemble_context(query, product_id)
        
        # Write Context to DB
        logger.debug("Writing assembled DecisionContext record to database.")
        db_context = DecisionContext(
            session_id=session_id,
            user_query=query,
            retrieved_kpi_snapshot=context_data["kpis"],
            active_anomalies=context_data["anomalies"],
            trend_metrics=context_data["trends"]
        )
        self.db.add(db_context)
        self.db.flush()  # Get db_context.id without committing yet
        logger.info(f"Saved DecisionContext to DB with context_id={db_context.id}")
        
        # 2. Generate Candidate Hypotheses
        logger.info("Step 2: Generating Candidate Hypotheses.")
        candidates = self.hypo_generator.generate_candidates(context_data)
        logger.info(f"Generated {len(candidates)} candidate hypotheses.")
        
        # Pre-compute product data length for data quality factor
        product_df_len = self._get_product_df_len(product_id)

        # Write Candidates & perform checks
        db_hypos = []
        validation_results = {}
        confidence_scores = {}
        historical_evidences = {}
        
        logger.info("Step 3: Running parallel validations and evidence lookup for hypotheses.")
        for idx, cand in enumerate(candidates):
            # Ensure hypothesis_id is globally unique to satisfy DB constraint
            unique_id = f"HYP_{db_context.id}_{cand['hypothesis_id']}"
            cand["hypothesis_id"] = unique_id
            logger.info(f"Processing candidate {idx+1}/{len(candidates)}: ID={unique_id}, Title='{cand['title']}'")
            
            # Run evidence retrieval and validation in parallel (they are independent)
            logger.debug("Dispatching parallel evidence retriever and scientific validator thread executor.")
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                f_evidence = executor.submit(
                    self.evidence_retriever.retrieve_historical_evidence,
                    cand["title"], cand["affected_kpis"]
                )
                f_validation = executor.submit(
                    self.validator.validate, cand, product_id, query_pcts
                )
                evidence = f_evidence.result()
                validation = f_validation.result()

            logger.debug(f"Retrieved {len(evidence)} evidence points for candidate {unique_id}")
            logger.debug(f"Validation completed for candidate {unique_id}")
            historical_evidences[cand["hypothesis_id"]] = evidence
            validation_results[cand["hypothesis_id"]] = validation
            
            # Map driver_variable to driver_keyword for confidence scorer
            driver_var = cand.get("driver_variable", "discount_pct")
            driver_map = {
                "discount_pct": "discount",
                "shipping_fee": "shipping",
                "avg_selling_price": "price",
                "marketing_spend": "marketing"
            }
            driver_keyword = driver_map.get(driver_var, "discount")

            # Compute confidence score (with data quality factor)
            logger.debug(f"Computing confidence score for candidate {unique_id}")
            score = self.scorer.compute_confidence(
                validation, evidence, cand["title"],
                product_df_len=product_df_len,
                driver_keyword=driver_keyword
            )
            confidence_scores[cand["hypothesis_id"]] = score
            
            # Save Hypothesis to DB
            logger.debug(f"Writing Hypothesis '{unique_id}' record to database.")
            db_hyp = Hypothesis(
                context_id=db_context.id,
                hypothesis_id=cand["hypothesis_id"],
                title=cand["title"],
                description=cand["description"],
                generated_from=cand["generated_from"],
                affected_kpis=cand["affected_kpis"],
                confidence_prior=cand["confidence_prior"]
            )
            self.db.add(db_hyp)
            self.db.flush()  # Get db_hyp.id without committing
            db_hypos.append(db_hyp)
            logger.debug(f"Hypothesis saved to DB with primary_id={db_hyp.id}")
            
            # Save Validation Result to DB
            logger.debug(f"Writing ValidationResult record for hypothesis primary_id={db_hyp.id} to database.")
            db_val = ValidationResult(
                hypothesis_id=db_hyp.id,
                correlation_metrics=validation["correlation"],
                forecast_sim_delta=validation["forecast_simulation"],
                sensitivity_elasticity=validation["sensitivity"],
                causal_estimates=validation["causal"],
                segment_consistency={"product_id": product_id}
            )
            self.db.add(db_val)
            
            # Save Confidence Score to DB (now includes data_quality_factor)
            logger.debug(f"Writing ConfidenceScore record for hypothesis primary_id={db_hyp.id} to database.")
            db_score = ConfidenceScore(
                hypothesis_id=db_hyp.id,
                overall_confidence=score["overall_confidence"],
                historical_agreement=score["breakdown"]["historical_agreement"],
                correlation_strength=score["breakdown"]["correlation_strength"],
                sensitivity_agreement=score["breakdown"]["sensitivity_alignment"],
                forecast_agreement=score["breakdown"]["forecast_simulation_agreement"],
                causal_confidence=score["breakdown"]["causal_confidence"],
                data_quality_factor=score.get("data_quality_factor", 0.0),
                reasoning_breakdown=score["reasoning"]
            )
            self.db.add(db_score)
            
        # Bulk commit all hypothesis/validation/confidence records at once
        logger.info("Committing all hypothesis, validation, and confidence records to Postgres.")
        self.db.commit()
        logger.info("Database transaction committed successfully for step 3.")
        
        # 3. Prioritize & Rank Hypotheses
        logger.info("Step 4: Prioritizing and ranking candidate hypotheses.")
        ranked_items = self.ranker.rank_hypotheses(candidates, validation_results, confidence_scores)
        
        # 4. Generate Recommendations & Action Steps (with context revenue for ROI normalization)
        logger.info("Step 5: Formulating tactical recommendations.")
        context_revenue = context_data.get("kpis", {}).get("total_revenue", 0.0)
        recommendations = self.rec_engine.generate_recommendations(ranked_items, context_revenue=context_revenue, db=self.db)
        logger.info(f"Formulated {len(recommendations)} recommendations from ranked list.")
        
        # Save Recommendations & Experiment Plans to DB
        logger.info("Step 6: Saving recommendations and experiment plans to database.")
        for idx, rec in enumerate(recommendations):
            # Find the db_hyp by hypothesis_id
            db_hyp = next((h for h in db_hypos if h.hypothesis_id == rec["hypothesis_id"]), None)
            if not db_hyp:
                logger.warning(f"Could not correlate recommendation {rec['hypothesis_id']} with saved DB hypothesis.")
                continue
            
            logger.debug(f"Writing Recommendation record for hypothesis primary_id={db_hyp.id} to database.")
            db_rec = Recommendation(
                hypothesis_id=db_hyp.id,
                recommendation_text=rec["recommendation_text"],
                action_type=rec["action_type"],
                expected_kpi_improvement=rec["expected_kpi_improvement"],
                estimated_roi=rec["estimated_roi"],
                priority=rec["priority"],
                rollback_strategy=rec["rollback_strategy"],
                risk_assessment=rec.get("risk_assessment")
            )
            self.db.add(db_rec)
            self.db.flush()  # Get db_rec.id
            logger.debug(f"Recommendation saved to DB with primary_id={db_rec.id}")
            
            # If needs experimentation, plan A/B test parameter requirements
            if rec["needs_experimentation"]:
                logger.info(f"Recommendation '{rec['hypothesis_id']}' requires structured testing. Invoking planner.")
                hypo_obj = next((item for item in ranked_items if item["hypothesis"]["hypothesis_id"] == rec["hypothesis_id"]), None)
                primary_metric = hypo_obj["hypothesis"]["affected_kpis"][0] if hypo_obj else "mean_conversion_rate"
                
                # Pass context to planner for live traffic data
                plan = self.planner.plan_experiment(rec, primary_metric, context=context_data)
                
                logger.debug(f"Writing ExperimentPlan record for recommendation primary_id={db_rec.id} to database.")
                db_plan = ExperimentPlan(
                    recommendation_id=db_rec.id,
                    experiment_type=plan["experiment_type"],
                    suggested_duration_days=plan["suggested_duration_days"],
                    required_sample_size=plan["required_sample_size"],
                    primary_metric=plan["primary_metric"],
                    success_criteria=plan["success_criteria"],
                    min_detectable_effect=float(plan["min_detectable_effect"].replace("%", "")) / 100.0
                )
                self.db.add(db_plan)
                logger.info(f"Experiment plan successfully saved to DB for recommendation primary_id={db_rec.id}")
                
        # Bulk commit all recommendations and experiment plans
        logger.info("Committing all recommendations and experiment plans to Postgres.")
        self.db.commit()
        logger.info("Database transaction committed successfully for step 6.")
        
        # 5. Compile Executive Markdown Summary
        logger.info("Step 7: Compiling executive brief markdown report.")
        explanation_markdown = self.explainer.generate_explanation(ranked_items, recommendations)
        
        logger.info("process_decision_flow: Complete intelligence loop executed successfully.")
        return {
            "context_id": db_context.id,
            "query": query,
            "business_context": context_data,
            "ranked_hypotheses": ranked_items,
            "recommendations": recommendations,
            "explanation": explanation_markdown
        }
