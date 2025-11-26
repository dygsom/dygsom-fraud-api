"""
Drift detector for monitoring feature distribution changes.
Detects when feature distributions deviate from baseline.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional
from scipy import stats

logger = logging.getLogger(__name__)


class DriftDetector:
    """
    Detect feature drift using statistical tests.
    
    Compares current feature distributions against baseline
    using Kolmogorov-Smirnov test.
    """

    def __init__(self, baseline_features: List[Dict[str, float]]):
        """
        Initialize DriftDetector with baseline feature set.
        
        Args:
            baseline_features: List of feature dictionaries from training/baseline period
        """
        self.baseline_features = baseline_features
        self.baseline_stats = self._calculate_stats(baseline_features)
        self.drift_threshold = 0.05  # p-value threshold for KS test
        
        logger.info(
            "DriftDetector initialized",
            extra={
                "baseline_size": len(baseline_features),
                "feature_count": len(self.baseline_stats),
            },
        )

    def _calculate_stats(
        self, features_list: List[Dict[str, float]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate statistics for each feature.
        
        Args:
            features_list: List of feature dictionaries
            
        Returns:
            Dict mapping feature names to their stats (mean, std, min, max)
        """
        if not features_list:
            return {}
        
        # Get all feature names
        feature_names = set()
        for features in features_list:
            feature_names.update(features.keys())
        
        stats_dict = {}
        
        for feature_name in feature_names:
            # Extract values for this feature (skip None values)
            values = [
                f[feature_name]
                for f in features_list
                if feature_name in f and f[feature_name] is not None
            ]
            
            if values:
                stats_dict[feature_name] = {
                    "mean": float(np.mean(values)),
                    "std": float(np.std(values)),
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                    "count": len(values),
                }
            else:
                stats_dict[feature_name] = {
                    "mean": 0.0,
                    "std": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "count": 0,
                }
        
        return stats_dict

    def detect_drift(
        self, current_features: List[Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        Detect drift between baseline and current features.
        
        Uses Kolmogorov-Smirnov test to compare distributions.
        
        Args:
            current_features: List of current feature dictionaries
            
        Returns:
            Dict with drift analysis results
        """
        try:
            if not current_features:
                logger.warning("No current features provided for drift detection")
                return {
                    "drift_detected": False,
                    "drifted_features": [],
                    "total_features": 0,
                    "error": "No current features",
                }
            
            current_stats = self._calculate_stats(current_features)
            drifted_features = []
            
            # Compare each feature
            for feature_name in self.baseline_stats.keys():
                if feature_name not in current_stats:
                    logger.warning(f"Feature {feature_name} missing in current data")
                    continue
                
                # Extract values for KS test
                baseline_values = [
                    f[feature_name]
                    for f in self.baseline_features
                    if feature_name in f and f[feature_name] is not None
                ]
                
                current_values = [
                    f[feature_name]
                    for f in current_features
                    if feature_name in f and f[feature_name] is not None
                ]
                
                if len(baseline_values) < 2 or len(current_values) < 2:
                    continue
                
                # Perform Kolmogorov-Smirnov test
                try:
                    ks_statistic, p_value = stats.ks_2samp(
                        baseline_values, current_values
                    )
                    
                    # Drift detected if p-value < threshold
                    if p_value < self.drift_threshold:
                        drift_info = {
                            "feature": feature_name,
                            "ks_statistic": float(ks_statistic),
                            "p_value": float(p_value),
                            "baseline_mean": self.baseline_stats[feature_name]["mean"],
                            "current_mean": current_stats[feature_name]["mean"],
                            "mean_change_pct": (
                                (
                                    current_stats[feature_name]["mean"]
                                    - self.baseline_stats[feature_name]["mean"]
                                )
                                / (self.baseline_stats[feature_name]["mean"] + 1e-10)
                            )
                            * 100,
                        }
                        drifted_features.append(drift_info)
                        
                        logger.warning(
                            "Drift detected",
                            extra={
                                "feature": feature_name,
                                "p_value": p_value,
                                "ks_statistic": ks_statistic,
                            },
                        )
                
                except Exception as e:
                    logger.error(f"Error in KS test for {feature_name}: {e}")
                    continue
            
            # Sort by KS statistic (most drifted first)
            drifted_features.sort(key=lambda x: x["ks_statistic"], reverse=True)
            
            result = {
                "drift_detected": len(drifted_features) > 0,
                "drifted_features": drifted_features,
                "drift_count": len(drifted_features),
                "total_features": len(self.baseline_stats),
                "drift_percentage": (len(drifted_features) / len(self.baseline_stats))
                * 100
                if self.baseline_stats
                else 0,
                "threshold": self.drift_threshold,
            }
            
            if drifted_features:
                logger.warning(
                    "Feature drift summary",
                    extra={
                        "drift_count": len(drifted_features),
                        "total_features": len(self.baseline_stats),
                        "drift_pct": result["drift_percentage"],
                    },
                )
            else:
                logger.debug("No feature drift detected")
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting drift: {e}", exc_info=True)
            return {
                "drift_detected": False,
                "drifted_features": [],
                "total_features": len(self.baseline_stats),
                "error": str(e),
            }

    def get_drift_summary(self) -> Dict[str, Any]:
        """
        Get summary of baseline feature statistics.
        
        Returns:
            Dict with baseline statistics
        """
        return {
            "baseline_size": len(self.baseline_features),
            "feature_count": len(self.baseline_stats),
            "features": self.baseline_stats,
            "drift_threshold": self.drift_threshold,
        }
