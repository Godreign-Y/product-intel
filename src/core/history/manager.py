import os
import json
import pandas as pd
import datetime
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from src.core.history.storage.database import engine, Base, get_neon_connection
from src.core.history.storage.models import (
    Snapshot, Event, Experiment, Report, ReportEmbedding,
    KnowledgeBase, ProductDailyFeature, Pattern, ProductPerformance
)
from src.core.history.embeddings.encoder import SentenceTransformerEncoder
from src.utils.logger import setup_logger

logger = setup_logger("history_manager")

class HistoryManager:
    def __init__(self, db: Session, encoder: Optional[SentenceTransformerEncoder] = None):
        self.db = db
        self.encoder = encoder or SentenceTransformerEncoder()
        
        # Bypassed FAISS index setup; we query directly from database.

    def rebuild_tables(self):
        """
        Cleans and recreates the historical intelligence repository tables.
        """
        logger.info("Dropping historical repository tables selectively...")
        tables = [
            ReportEmbedding.__table__,
            Report.__table__,
            Experiment.__table__,
            Event.__table__,
            Snapshot.__table__,
            KnowledgeBase.__table__,
            ProductDailyFeature.__table__,
            Pattern.__table__
        ]
        for table in tables:
            table.drop(bind=engine, checkfirst=True)
            
        logger.info("Creating historical repository tables selectively...")
        for table in reversed(tables):
            table.create(bind=engine, checkfirst=True)
            
        logger.info("Database tables initialized successfully.")

    def _clear_table_via_neon(self, table_name: str):
        """
        Use the direct Neon connection for clearing tables when the SQLAlchemy
        session pool has stale SSL connections.
        """
        logger.info(f"Clearing table {table_name} using direct Neon connection...")
        conn = get_neon_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(f"DELETE FROM {table_name}")
            conn.commit()
        except Exception as e:
            logger.error(f"Direct clear table failed for {table_name}: {e}")
            raise e
        finally:
            conn.close()

    def run_build_pipeline(self, df_hist: Optional[pd.DataFrame] = None, force_rebuild: bool = True, csv_path: str = "experiment_dataset.csv") -> Dict[str, Any]:
        """
        Cleans existing repository tables and populates the database using the ground-truth
        experiment dataset (from CSV). Generates report text and vectorizes the results.
        """
        logger.info("Initializing Historical Intelligence load pipeline...")
        self.db.rollback()
        engine.dispose()
        
        if force_rebuild:
            logger.info("Force rebuild requested. Dropping and recreating tables...")
            self.rebuild_tables()
        else:
            logger.info("Ensuring all tables exist...")
            Base.metadata.create_all(bind=engine)
            
        # Locate the experiment CSV
        if not os.path.exists(csv_path):
            # Try workspace absolute path fallback if needed
            workspace_root = os.getcwd()
            csv_path = os.path.join(workspace_root, "experiment_dataset.csv")
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"Experiment dataset CSV not found at {csv_path}")

        logger.info(f"Loading experiment dataset from {csv_path}...")
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} experiment rows.")
        
        # Clear the relevant tables
        if not force_rebuild:
            self._clear_table_via_neon(ReportEmbedding.__tablename__)
            self._clear_table_via_neon(Report.__tablename__)
            self._clear_table_via_neon(Experiment.__tablename__)
            self._clear_table_via_neon(KnowledgeBase.__tablename__)

        experiments_to_create = []
        embedding_descriptions = []

        logger.info("Parsing experiments and preparing database records...")
        for idx, row in df.iterrows():
            # Setup dates
            start_date_val = datetime.datetime.strptime(str(row["start_date"]), "%Y-%m-%d").date()
            end_date_val = datetime.datetime.strptime(str(row["end_date"]), "%Y-%m-%d").date()
            
            # Outcome mapping
            res_val = str(row["result"]).strip()
            if res_val == "Win":
                outcome_val = "positive"
            elif res_val == "Loss":
                outcome_val = "negative"
            else:
                outcome_val = "neutral"
                
            conf_val = float(row["confidence"])
            p_val_calc = float(1.0 - conf_val)
            effect_pct = float(row["observed_effect_pct"])
            
            # Changed features parsing
            changed_str = row["changed_features"]
            before_m = {}
            after_m = {}
            driver_val = "discount_pct"
            driver_delta_val = 0.0
            
            if isinstance(changed_str, str):
                try:
                    feat_data = json.loads(changed_str)
                    for k, v in feat_data.items():
                        if isinstance(v, dict):
                            if "old" in v and "new" in v:
                                before_m[k] = v["old"]
                                after_m[k] = v["new"]
                                driver_val = k
                                driver_delta_val = float(v.get("change_pct", 0.0))
                            else:
                                for sk, sv in v.items():
                                    if isinstance(sv, dict) and "old" in sv and "new" in sv:
                                        before_m[f"{k}_{sk}"] = sv["old"]
                                        after_m[f"{k}_{sk}"] = sv["new"]
                                        driver_val = k
                                        driver_delta_val = float(sv.get("change_pct", 0.0))
                except Exception:
                    pass

            db_exp = Experiment(
                experiment_id=row["experiment_id"],
                type=row["experiment_type"],
                product_ids=row["product_id"],
                product_id=row["product_id"],
                category=row["category"],
                subcategory=row["subcategory"],
                brand=row["brand"],
                start_date=start_date_val,
                end_date=end_date_val,
                before_metrics=before_m,
                after_metrics=after_m,
                change_summary=row["notes"],
                improvement_pct=effect_pct,
                outcome=outcome_val,
                confidence_score=conf_val,
                
                # New explicit columns
                changed_features=feat_data if 'feat_data' in locals() else {},
                primary_metric=row["primary_metric"],
                expected_direction=row["expected_direction"],
                observed_effect_pct=effect_pct,
                result=res_val,
                notes=row["notes"],
                
                # Rebuilt history engine explicit legacy fields
                driver=driver_val,
                driver_delta=driver_delta_val,
                kpi_target=row["primary_metric"],
                kpi_before=float(list(before_m.values())[0]) if before_m else 0.0,
                kpi_after=float(list(after_m.values())[0]) if after_m else 0.0,
                ATE=effect_pct,
                p_value=p_val_calc,
                hypothesis_text=row["notes"],
                
                # Legacy compatibility columns
                segment=row["category"],
                season="Summer",
                outcome_score=effect_pct,
                confidence=conf_val
            )
            experiments_to_create.append(db_exp)
            
            # Prepare rich search descriptions
            desc_text = (
                f"Brand: {row['brand']} | Category: {row['category']} | Subcategory: {row['subcategory']} | "
                f"Type: {row['experiment_type']} | Metric: {row['primary_metric']} | Notes: {row['notes']}"
            )
            embedding_descriptions.append(desc_text)

        # Bulk save Experiments
        logger.info("Writing experiment rows to database...")
        self.db.add_all(experiments_to_create)
        self.db.commit()

        # Batch encode description texts
        logger.info("Vectorizing experiments descriptions in batch...")
        embeddings = self.encoder.encode_batch(embedding_descriptions)
        
        # Write Reports and Embeddings
        logger.info("Creating Reports and Embeddings database records...")
        reports_created = 0
        
        for idx, db_exp in enumerate(experiments_to_create):
            row_data = df.iloc[idx]
            structured_json = {
                "learnings": row_data["notes"],
                "recommendations": "Roll out change platform-wide." if row_data["result"] == "Win" else "Refine or reject hypothesis."
            }
            
            human_text = (
                f"# Experiment Report: {db_exp.experiment_id}\n"
                f"**Product ID:** {db_exp.product_id}\n"
                f"**Category:** {db_exp.category} | **Subcategory:** {db_exp.subcategory}\n"
                f"**Brand:** {db_exp.brand} | **Type:** {db_exp.type}\n\n"
                f"## Executive Summary\n"
                f"Tested a **{db_exp.type}** on product **{db_exp.product_id}** "
                f"from **{db_exp.start_date}** to **{db_exp.end_date}**. "
                f"Targeted **{db_exp.primary_metric}** with an expected direction of **{db_exp.expected_direction}**.\n\n"
                f"## Results & Performance\n"
                f"- **Outcome:** {db_exp.result} (Classified as: {db_exp.outcome})\n"
                f"- **Observed Effect:** {db_exp.observed_effect_pct}%\n"
                f"- **Statistical Confidence:** {db_exp.confidence_score * 100:.1f}%\n\n"
                f"## Changed Features Log\n"
                f"```json\n{json.dumps(db_exp.before_metrics, indent=2)}\n-->\n{json.dumps(db_exp.after_metrics, indent=2)}\n```\n\n"
                f"## Strategic Notes\n"
                f"{db_exp.notes}\n"
            )
            
            db_report = Report(
                experiment_id=db_exp.id,
                structured_json=structured_json,
                human_readable_text=human_text
            )
            self.db.add(db_report)
            self.db.commit() # commit report to get ID
            
            vector = embeddings[idx]
            db_emb = ReportEmbedding(
                report_id=db_report.id,
                embedding=vector,
                meta_data={
                    "experiment_id": db_exp.experiment_id,
                    "type": db_exp.type,
                    "category": db_exp.category,
                    "outcome": db_exp.outcome
                }
            )
            self.db.add(db_emb)
            self.db.commit()
            
            reports_created += 1

        logger.info(f"Database build pipeline completed successfully. Recorded {len(experiments_to_create)} experiments.")
        return {
            "status": "success",
            "features_created": 0,
            "patterns_mined": 0,
            "snapshots_built": 0,
            "experiments_recorded": len(experiments_to_create)
        }

    # --- L6 API Implementation ---
    
    def get_kpi_snapshot(self, product_id: str, window_days: int = 7) -> Dict[str, Any]:
        """
        Retrieves a rolling average of core KPIs from ProductPerformance (temporal logs) directly.
        """
        query = self.db.query(ProductPerformance).filter(ProductPerformance.product_id == product_id)
        features = query.order_by(ProductPerformance.date.desc()).limit(window_days).all()
        
        if not features:
            return {
                "total_revenue": 0.0,
                "total_profit": 0.0,
                "total_orders": 0,
                "mean_conversion_rate": 0.0,
                "mean_retention_rate": 0.0,
                "avg_discount_pct": 0.0,
                "avg_price": 0.0
            }
            
        n = len(features)
        avg_revenue = sum(f.revenue or 0.0 for f in features) / n
        avg_profit = sum(f.profit or 0.0 for f in features) / n
        avg_orders = sum(f.orders or 0.0 for f in features) / n
        avg_conv = sum(f.conversion_rate or 0.0 for f in features) / n
        avg_ret = sum(f.retention_rate or 0.0 for f in features) / n
        avg_disc = sum(f.discount_pct or 0.0 for f in features) / n
        avg_price = sum(f.avg_selling_price or 0.0 for f in features) / n
        
        # Mixes from the latest day
        latest = features[0]
        
        return {
            "total_revenue": round(avg_revenue, 2),
            "total_profit": round(avg_profit, 2),
            "total_orders": int(round(avg_orders)),
            "mean_conversion_rate": round(avg_conv, 4),
            "mean_retention_rate": round(avg_ret, 4),
            "avg_discount_pct": round(avg_disc, 2),
            "avg_price": round(avg_price, 2),
            "channel_mix": {
                "Amazon": round(latest.amazon_sales_pct or 0.0, 2),
                "Website": round(latest.website_sales_pct or 0.0, 2),
                "Nykaa": round(latest.nykaa_sales_pct or 0.0, 2),
                "MobileApp": round(latest.mobile_app_sales_pct or 0.0, 2)
            },
            "campaign_mix": {
                "Search": round(latest.search_campaign_pct or 0.0, 2),
                "Social": round(latest.social_campaign_pct or 0.0, 2),
                "Email": round(latest.email_campaign_pct or 0.0, 2),
                "Affiliate": round(latest.affiliate_campaign_pct or 0.0, 2)
            },
            "rolling_window_days": n
        }

    def get_anomalies(self, severity_min: str = "High") -> List[Dict[str, Any]]:
        """
        Wiped as time-series pattern mining is disabled. Returns empty array safely.
        """
        return []

    def get_trend_direction(self, product_id: str, kpi: str) -> str:
        """
        Wiped as time-series pattern mining is disabled. Returns default 'stable'.
        """
        return "stable"

    def get_elasticity_profile(self, driver: str, kpi: str, product_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Wiped as time-series pattern mining is disabled. Returns default low-confidence profile to trigger perturbation fallbacks.
        """
        return {
            "driver": driver,
            "kpi_target": kpi,
            "elasticity_coef": 0.0,
            "n_valid_obs": 0,
            "confidence": "Low"
        }

    def semantic_search(self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Executes vector semantic search directly querying the Postgres (or SQLite via fallback) database.
        """
        query_vector = self.encoder.encode(query)
        results = []
        
        # Check if we can perform a pgvector query directly in postgres
        from src.core.history.storage.models import HAS_PGVECTOR
        is_postgres = (self.db.bind.dialect.name == "postgresql") and HAS_PGVECTOR
        
        if is_postgres:
            nested = self.db.begin_nested()
            try:
                # pgvector cosine distance operator is <=>
                cosine_dist = ReportEmbedding.embedding.op('<=>')(query_vector)
                
                # Query both the embedding record and the distance
                query_db = self.db.query(ReportEmbedding, cosine_dist).join(
                    Report, Report.id == ReportEmbedding.report_id
                ).join(
                    Experiment, Experiment.id == Report.experiment_id
                )
                
                # Apply database-level filters
                if filters:
                    category = filters.get("category")
                    exp_type = filters.get("type")
                    outcome = filters.get("outcome")
                    
                    if category:
                        query_db = query_db.filter(Experiment.category == category)
                    if exp_type:
                        query_db = query_db.filter(Experiment.type == exp_type)
                    if outcome:
                        query_db = query_db.filter(Experiment.outcome == outcome)
                        
                # Order by distance ascending (closest first)
                query_db = query_db.order_by(cosine_dist).limit(limit)
                
                db_results = query_db.all()
                for emb, dist in db_results:
                    score = 1.0 - float(dist) if dist is not None else 0.0
                    results.append({
                        "score": round(score, 4),
                        "report": emb.report,
                        "experiment": emb.report.experiment
                    })
                nested.commit()
                return results
            except Exception as e:
                nested.rollback()
                logger.error(f"PostgreSQL pgvector query failed: {e}. Falling back to Python similarity search.")
                results = []
                
        # Fallback python cosine similarity search (useful for SQLite tests or if pgvector is missing)
        try:
            import numpy as np
            
            # Query all embeddings from DB
            query_db = self.db.query(ReportEmbedding).join(
                Report, Report.id == ReportEmbedding.report_id
            ).join(
                Experiment, Experiment.id == Report.experiment_id
            )
            
            # Apply filters
            if filters:
                category = filters.get("category")
                exp_type = filters.get("type")
                outcome = filters.get("outcome")
                
                if category:
                    query_db = query_db.filter(Experiment.category == category)
                if exp_type:
                    query_db = query_db.filter(Experiment.type == exp_type)
                if outcome:
                    query_db = query_db.filter(Experiment.outcome == outcome)
                    
            embeddings = query_db.all()
            if not embeddings:
                return []
                
            np_query = np.array(query_vector, dtype=np.float32)
            query_norm = np.linalg.norm(np_query)
            if query_norm > 0:
                np_query /= query_norm
                
            candidate_results = []
            for emb in embeddings:
                if not emb.embedding:
                    continue
                # Deserialized representation from text (SQLite) or VectorType
                emb_vec = np.array(emb.embedding, dtype=np.float32)
                emb_norm = np.linalg.norm(emb_vec)
                if emb_norm > 0:
                    emb_vec /= emb_norm
                sim = np.dot(np_query, emb_vec)
                candidate_results.append((sim, emb))
                
            # Sort by similarity descending
            candidate_results.sort(key=lambda x: x[0], reverse=True)
            
            for score, emb in candidate_results[:limit]:
                results.append({
                    "score": round(float(score), 4),
                    "report": emb.report,
                    "experiment": emb.report.experiment
                })
        except Exception as e:
            logger.error(f"Fallback python semantic search failed: {e}")
            
        return results

    def find_similar_experiments(self, category: str, features: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
        """
        Backward compatible lookup for similar experiments.
        """
        query = f"past experiments category {category} " + " ".join(f"{k} {v}" for k, v in features.items())
        results = self.semantic_search(query, limit=limit, filters={"category": category})
        # Map score to similarity_score for router compatibility
        for res in results:
            res["similarity_score"] = res["score"]
        return results

    def extract_topic_insights(self, topic: str) -> Dict[str, Any]:
        """
        Checks KnowledgeBase cache. If missing, fetches relevant experiments via semantic search
        to synthesize insights.
        """
        cached = self.db.query(KnowledgeBase).filter(KnowledgeBase.pattern_type == topic).first()
        if cached:
            return {
                "topic": topic,
                "synthesized_rules": cached.synthesized_rules,
                "confidence_score": cached.confidence_score,
                "cached": True
            }
            
        search_query = f"learnings related to {topic}"
        similar_reports = self.semantic_search(search_query, limit=10)
        
        if not similar_reports:
            return {
                "topic": topic,
                "synthesized_rules": {
                    "success_rate_pct": 0.0,
                    "learnings": f"No experiments found for topic '{topic}'.",
                    "frequent_failures": [],
                    "successful_strategies": []
                },
                "confidence_score": 0.5,
                "cached": False
            }
            
        total = len(similar_reports)
        positives = sum(1 for r in similar_reports if r["experiment"].outcome == "positive")
        success_rate = (positives / total * 100.0) if total > 0 else 0.0
        
        failures = []
        successes = []
        for r in similar_reports:
            exp = r["experiment"]
            rep = r["report"]
            desc = exp.notes or exp.change_summary
            if rep.structured_json and rep.structured_json.get("learnings"):
                desc += f" ({rep.structured_json.get('learnings')})"
                
            if exp.outcome == "negative":
                failures.append(desc)
            elif exp.outcome == "positive":
                successes.append(desc)
                
        synthesized = {
            "learnings": f"Analysis of {len(similar_reports)} experiments matching topic '{topic}'.",
            "frequent_failures": failures[:3] if failures else ["No major failures recorded."],
            "successful_strategies": successes[:3] if successes else ["No consistent successes recorded."],
            "success_rate_pct": round(success_rate, 2)
        }
        
        confidence_score = round(float(0.5 + (success_rate / 200.0)), 2)
        kb_entry = KnowledgeBase(
            pattern_type=topic,
            query_context=search_query,
            synthesized_rules=synthesized,
            confidence_score=confidence_score,
            driver=topic,
            segment="Generic",
            season="Summer",
            outcome_score=round(float(success_rate), 2),
            confidence=confidence_score
        )
        self.db.add(kb_entry)
        self.db.commit()
        
        return {
            "topic": topic,
            "synthesized_rules": synthesized,
            "confidence_score": kb_entry.confidence_score,
            "cached": False
        }

    def record_experiment(self, record: Dict[str, Any]) -> Experiment:
        """
        Record a single experiment directly to Neon DB and FAISS index.
        """
        logger.info(f"Recording custom experiment: {record.get('experiment_id')}")
        
        start_date = record.get("start_date") or datetime.date.today() - datetime.timedelta(days=14)
        end_date = record.get("end_date") or datetime.date.today()
        
        if isinstance(start_date, str):
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

        outcome = record.get("outcome", "neutral")
        confidence = float(record.get("confidence", 0.5))
        effect_pct = float(record.get("ATE") or record.get("observed_effect_pct") or 0.0)

        db_exp = Experiment(
            experiment_id=record.get("experiment_id", f"EXP_CUSTOM_{datetime.datetime.now().strftime('%m%d%H%M')}"),
            type=record.get("type", "Custom Experiment"),
            product_ids=record.get("product_id") or "P001",
            product_id=record.get("product_id") or "P001",
            category=record.get("category") or "Generic",
            subcategory=record.get("subcategory") or "General",
            brand=record.get("brand") or "Core",
            start_date=start_date,
            end_date=end_date,
            before_metrics=record.get("before_metrics") or {},
            after_metrics=record.get("after_metrics") or {},
            change_summary=record.get("notes") or record.get("change_summary") or "",
            improvement_pct=effect_pct,
            outcome=outcome,
            confidence_score=confidence,
            
            changed_features=record.get("changed_features") or {},
            primary_metric=record.get("primary_metric") or record.get("kpi_target") or "revenue",
            expected_direction=record.get("expected_direction") or "Increase",
            observed_effect_pct=effect_pct,
            result="Win" if outcome == "positive" else ("Loss" if outcome == "negative" else "Inconclusive"),
            notes=record.get("notes") or record.get("change_summary") or "",
            
            driver=record.get("driver", "discount_pct"),
            driver_delta=float(record.get("driver_delta") or 0.0),
            kpi_target=record.get("kpi_target") or "revenue",
            kpi_before=float(record.get("kpi_before") or 0.0),
            kpi_after=float(record.get("kpi_after") or 0.0),
            ATE=effect_pct,
            p_value=float(record.get("p_value") or (1.0 - confidence)),
            hypothesis_text=record.get("notes") or record.get("change_summary") or "",
            
            segment=record.get("category") or "Generic",
            season=record.get("season") or "Summer",
            outcome_score=effect_pct,
            confidence=confidence
        )
        self.db.add(db_exp)
        self.db.commit()

        structured_json = {
            "learnings": db_exp.notes,
            "recommendations": "Roll out change platform-wide." if db_exp.result == "Win" else "Refine or reject hypothesis."
        }
        
        human_text = (
            f"# Experiment Report: {db_exp.experiment_id}\n"
            f"**Product ID:** {db_exp.product_id}\n"
            f"**Category:** {db_exp.category} | **Subcategory:** {db_exp.subcategory}\n\n"
            f"## Strategic Notes\n{db_exp.notes}\n"
        )
        
        db_report = Report(
            experiment_id=db_exp.id,
            structured_json=structured_json,
            human_readable_text=human_text
        )
        self.db.add(db_report)
        self.db.commit()

        desc_text = (
            f"Brand: {db_exp.brand} | Category: {db_exp.category} | Subcategory: {db_exp.subcategory} | "
            f"Type: {db_exp.type} | Metric: {db_exp.primary_metric} | Notes: {db_exp.notes}"
        )
        vector = self.encoder.encode(desc_text)
        
        db_emb = ReportEmbedding(
            report_id=db_report.id,
            embedding=vector,
            meta_data={
                "experiment_id": db_exp.experiment_id,
                "type": db_exp.type,
                "category": db_exp.category,
                "outcome": outcome
            }
        )
        self.db.add(db_emb)
        self.db.commit()
        return db_exp
