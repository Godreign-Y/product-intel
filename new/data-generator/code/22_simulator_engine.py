"""
Main orchestrator for Simulator Engine.
"""
import json
import uuid
from simulator.core.models import SimulationConfig
from simulator.physics.config_loader import ConfigLoader
from simulator.physics.curves import CurveEngine
from simulator.physics.interactions import InteractionEngine
from simulator.physics.propagation import MarketPropagationEngine
from simulator.core.state_transition import StateTransitionEngine
from simulator.core.trajectory_simulator import AnchorStateResolver, TrajectorySimulator, BaselineTrajectoryGenerator
from simulator.writers.csv_writer import CsvStreamWriter
from simulator.writers.report_generator import ReportGenerator

def load_json(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    # 1. Configuration
    config = SimulationConfig(simulation_days=365)
    
    # 2. Load Physics
    loader = ConfigLoader("simulator/config")
    curve_engine = CurveEngine(loader.get_curve_profiles())
    interaction_engine = InteractionEngine(loader.get_interaction_rules())
    propagation_engine = MarketPropagationEngine(loader.get_market_graph(), loader.get_elasticities())
    
    transition_engine = StateTransitionEngine(
        curve_engine, 
        interaction_engine, 
        propagation_engine, 
        loader.get_elasticities(), 
        loader.get_archetypes(),
        loader.get_simulation_assumptions()
    )
    
    resolver = AnchorStateResolver()
    trajectory_engine = TrajectorySimulator(transition_engine)
    baseline_engine = BaselineTrajectoryGenerator(transition_engine)
    
    writer = CsvStreamWriter("output", "trajectories_v8.csv")
    report = ReportGenerator("simulation_report_v8.json")
    
    # 3. Load Inputs
    try:
        products = load_json("products.json")
        schedules = load_json("action_schedules.json")
    except Exception as e:
        print(f"Error loading inputs: {e}")
        return

    # Extract unique categories and build map
    categories = list(set(p.get("category", "Unknown") for p in products))
    category_map = {cat: idx + 1 for idx, cat in enumerate(sorted(categories))}
    
    # Save category mapping
    with open("output/category_mapping.json", "w") as f:
        json.dump(category_map, f, indent=4)
        
    # Inject category_id into products
    for p in products:
        p["category_id"] = category_map.get(p.get("category", "Unknown"), 0)

    # To test without doing 876k rows, we can slice products/schedules
    # products = products[:2]
    # schedules = schedules[:10]
    
    prod_dict = {p["product_id"]: p for p in products}

    # 4. Execute Simulation
    for product in products:
        report.record_product()
        
    for schedule in schedules:
        report.record_trajectory()
        prod_id = schedule.get("product_id")
        product = prod_dict.get(prod_id)
        if not product:
            continue
            
        anchor_day = schedule.get("anchor_day", 0)
        initial_state = resolver.resolve(product, anchor_day)
        
        # We can also generate baseline if we want (Ground Truth)
        # baseline_traj = baseline_engine.generate(initial_state, config)
        
        traj_id = str(uuid.uuid4())
        sched_id = schedule.get("schedule_id", "")
        events = schedule.get("events", [])
        
        inventory_policy = product.get("inventory_policy", "weekly")
        simulated_traj = trajectory_engine.simulate(initial_state, events, config, inventory_policy)
        
        for day, state in enumerate(simulated_traj):
            report.record_state(state)
            writer.append(traj_id, sched_id, prod_id, day, state)

    # Flush remaining data and save report
    writer.flush()
    report.save()
    
    print("Simulation Complete!")

if __name__ == "__main__":
    main()
