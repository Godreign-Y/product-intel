import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from typing import Dict

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # Avoid division by zero in MAPE
    non_zero = y_true != 0
    if np.sum(non_zero) > 0:
        mape = np.mean(np.abs((y_true[non_zero] - y_pred[non_zero]) / y_true[non_zero])) * 100
    else:
        mape = 0.0
        
    # SMAPE formula
    smape_denominator = (np.abs(y_true) + np.abs(y_pred)) / 2.0
    smape_mask = smape_denominator != 0
    if np.sum(smape_mask) > 0:
        smape = np.mean(np.abs(y_true[smape_mask] - y_pred[smape_mask]) / smape_denominator[smape_mask]) * 100
    else:
        smape = 0.0
        
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true, y_pred)
    
    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "mape": float(mape),
        "smape": float(smape),
        "r2": float(r2)
    }
