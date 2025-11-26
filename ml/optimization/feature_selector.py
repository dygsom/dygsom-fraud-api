"""
Feature selector for model optimization.
Analyzes feature importance and selects top features.
"""

import logging
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class FeatureSelector:
    """
    Select most important features from XGBoost model.
    
    Uses feature importance scores to identify top features
    and remove low-importance ones.
    """

    def __init__(self, model, feature_names: List[str]):
        """
        Initialize FeatureSelector.
        
        Args:
            model: Trained XGBoost model
            feature_names: List of feature names
        """
        self.model = model
        self.feature_names = feature_names
        logger.info(
            "FeatureSelector initialized",
            extra={"feature_count": len(feature_names)},
        )

    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get feature importance scores from model.
        
        Returns:
            DataFrame with features and their importance scores
        """
        try:
            # Get importance scores from XGBoost model
            importance_dict = self.model.get_score(importance_type="weight")
            
            # Create DataFrame
            importance_data = []
            for feature_name in self.feature_names:
                # XGBoost uses f0, f1, f2... format
                feature_idx = self.feature_names.index(feature_name)
                xgb_feature_name = f"f{feature_idx}"
                
                importance = importance_dict.get(xgb_feature_name, 0.0)
                importance_data.append(
                    {"feature": feature_name, "importance": importance}
                )
            
            df = pd.DataFrame(importance_data)
            df = df.sort_values("importance", ascending=False).reset_index(drop=True)
            
            logger.info(
                "Feature importance calculated",
                extra={
                    "total_features": len(df),
                    "top_feature": df.iloc[0]["feature"] if len(df) > 0 else None,
                    "top_importance": float(df.iloc[0]["importance"])
                    if len(df) > 0
                    else 0,
                },
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating feature importance: {e}", exc_info=True)
            return pd.DataFrame(columns=["feature", "importance"])

    def select_top_features(
        self, n_features: Optional[int] = None, threshold: Optional[float] = None
    ) -> List[str]:
        """
        Select top N features or features above threshold.
        
        Args:
            n_features: Number of top features to select (if None, use threshold)
            threshold: Minimum importance threshold (if None, use n_features)
            
        Returns:
            List of selected feature names
        """
        try:
            importance_df = self.get_feature_importance()
            
            if n_features is not None:
                # Select top N features
                selected = importance_df.head(n_features)["feature"].tolist()
                logger.info(
                    "Selected top N features",
                    extra={"n_features": n_features, "selected_count": len(selected)},
                )
            elif threshold is not None:
                # Select features above threshold
                selected = importance_df[importance_df["importance"] >= threshold][
                    "feature"
                ].tolist()
                logger.info(
                    "Selected features above threshold",
                    extra={
                        "threshold": threshold,
                        "selected_count": len(selected),
                        "total_features": len(importance_df),
                    },
                )
            else:
                # Default: top 20 features
                selected = importance_df.head(20)["feature"].tolist()
                logger.info("Selected default top 20 features")
            
            return selected
            
        except Exception as e:
            logger.error(f"Error selecting features: {e}", exc_info=True)
            return self.feature_names  # Return all features on error

    def plot_feature_importance(
        self, top_n: int = 20, output_file: Optional[str] = None
    ) -> None:
        """
        Plot feature importance as bar chart.
        
        Args:
            top_n: Number of top features to plot
            output_file: Path to save plot (if None, show plot)
        """
        try:
            importance_df = self.get_feature_importance()
            top_features = importance_df.head(top_n)
            
            # Create bar plot
            plt.figure(figsize=(12, 8))
            plt.barh(
                range(len(top_features)),
                top_features["importance"],
                tick_label=top_features["feature"],
            )
            plt.xlabel("Importance Score")
            plt.ylabel("Feature")
            plt.title(f"Top {top_n} Feature Importance")
            plt.gca().invert_yaxis()  # Highest importance at top
            plt.tight_layout()
            
            if output_file:
                plt.savefig(output_file, dpi=300, bbox_inches="tight")
                logger.info(f"Feature importance plot saved to {output_file}")
            else:
                plt.show()
            
            plt.close()
            
        except Exception as e:
            logger.error(f"Error plotting feature importance: {e}", exc_info=True)

    def remove_low_importance_features(
        self, threshold: float = 0.0
    ) -> Tuple[List[str], List[str]]:
        """
        Identify features to remove based on low importance.
        
        Args:
            threshold: Minimum importance threshold
            
        Returns:
            Tuple of (features_to_keep, features_to_remove)
        """
        try:
            importance_df = self.get_feature_importance()
            
            features_to_keep = importance_df[importance_df["importance"] > threshold][
                "feature"
            ].tolist()
            
            features_to_remove = importance_df[
                importance_df["importance"] <= threshold
            ]["feature"].tolist()
            
            logger.info(
                "Low importance features identified",
                extra={
                    "threshold": threshold,
                    "keep_count": len(features_to_keep),
                    "remove_count": len(features_to_remove),
                },
            )
            
            return features_to_keep, features_to_remove
            
        except Exception as e:
            logger.error(
                f"Error identifying low importance features: {e}", exc_info=True
            )
            return self.feature_names, []  # Keep all on error
