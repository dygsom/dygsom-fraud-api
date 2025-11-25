"""
Data preparation script for fraud detection model training.

Loads transactions from database and extracts features using FeatureEngineer.
Saves training data to CSV for model training.

Usage:
    python -m ml.training.prepare_data --output training_data.csv --limit 10000
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.database import get_prisma_client
from src.ml.features.feature_engineering import FeatureEngineer
from src.repositories.velocity_repository import VelocityRepository
from src.core.cache import get_redis_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def load_transactions(limit: int = None) -> List[Dict[str, Any]]:
    """Load transactions from database
    
    Args:
        limit: Maximum number of transactions to load
        
    Returns:
        List of transaction dictionaries
    """
    logger.info(f"Loading transactions (limit={limit})")
    
    prisma = await get_prisma_client()
    
    try:
        # Query transactions
        if limit:
            transactions = await prisma.transaction.find_many(
                take=limit,
                order={'created_at': 'desc'},
                include={
                    'customer': True,
                    'payment_method': True,
                    'merchant': True,
                    'risk_assessment': True
                }
            )
        else:
            transactions = await prisma.transaction.find_many(
                order={'created_at': 'desc'},
                include={
                    'customer': True,
                    'payment_method': True,
                    'merchant': True,
                    'risk_assessment': True
                }
            )
        
        logger.info(f"Loaded {len(transactions)} transactions")
        
        # Convert to dictionaries
        transaction_dicts = []
        for tx in transactions:
            tx_dict = tx.dict()
            transaction_dicts.append(tx_dict)
        
        return transaction_dicts
        
    except Exception as e:
        logger.error(f"Error loading transactions: {str(e)}", exc_info=True)
        raise
    finally:
        await prisma.disconnect()


async def extract_features_for_transactions(
    transactions: List[Dict[str, Any]],
    use_velocity: bool = True
) -> pd.DataFrame:
    """Extract features from transactions
    
    Args:
        transactions: List of transaction dictionaries
        use_velocity: Whether to include velocity features
        
    Returns:
        DataFrame with extracted features
    """
    logger.info(f"Extracting features for {len(transactions)} transactions")
    
    feature_engineer = FeatureEngineer()
    
    # Initialize velocity repository if needed
    velocity_repo = None
    if use_velocity:
        try:
            redis_client = get_redis_client()
            velocity_repo = VelocityRepository(redis_client)
            logger.info("Velocity repository initialized")
        except Exception as e:
            logger.warning(f"Could not initialize velocity repository: {e}")
            use_velocity = False
    
    # Extract features for each transaction
    all_features = []
    for i, tx in enumerate(transactions):
        try:
            # Get velocity features if available
            velocity_features = {}
            if use_velocity and velocity_repo:
                velocity_features = await velocity_repo.get_velocity_features(
                    customer_id=tx.get('customer_id'),
                    ip_address=tx.get('ip_address'),
                    device_id=tx.get('device_id')
                )
            
            # Extract features
            features = feature_engineer.extract_all_features(tx, velocity_features)
            
            # Add target variable (fraud label)
            if tx.get('risk_assessment'):
                fraud_score = tx['risk_assessment'].get('fraud_score', 0.0)
                # Convert score to binary label (threshold 0.7)
                features['is_fraud'] = int(fraud_score >= 0.7)
            else:
                features['is_fraud'] = 0
            
            # Add transaction ID for reference
            features['transaction_id'] = tx.get('id', '')
            
            all_features.append(features)
            
            if (i + 1) % 100 == 0:
                logger.info(f"Processed {i + 1}/{len(transactions)} transactions")
                
        except Exception as e:
            logger.warning(f"Error extracting features for transaction {tx.get('id')}: {e}")
            continue
    
    # Convert to DataFrame
    df = pd.DataFrame(all_features)
    
    logger.info(
        f"Feature extraction complete",
        extra={
            "total_transactions": len(transactions),
            "successful_extractions": len(df),
            "total_features": len(df.columns),
            "fraud_count": df['is_fraud'].sum() if 'is_fraud' in df.columns else 0
        }
    )
    
    return df


async def prepare_training_data(
    output_file: str,
    limit: int = None,
    use_velocity: bool = True
) -> None:
    """Prepare training data and save to CSV
    
    Args:
        output_file: Path to output CSV file
        limit: Maximum number of transactions to load
        use_velocity: Whether to include velocity features
    """
    logger.info("Starting data preparation")
    
    try:
        # Load transactions
        transactions = await load_transactions(limit)
        
        if not transactions:
            logger.error("No transactions loaded")
            return
        
        # Extract features
        df = await extract_features_for_transactions(transactions, use_velocity)
        
        if df.empty:
            logger.error("No features extracted")
            return
        
        # Save to CSV
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_path, index=False)
        
        logger.info(
            f"Training data saved to {output_path}",
            extra={
                "rows": len(df),
                "columns": len(df.columns),
                "fraud_percentage": (df['is_fraud'].sum() / len(df) * 100) if 'is_fraud' in df.columns else 0
            }
        )
        
        # Print summary statistics
        print("\n=== Data Preparation Summary ===")
        print(f"Total transactions: {len(df)}")
        print(f"Total features: {len(df.columns)}")
        if 'is_fraud' in df.columns:
            print(f"Fraud transactions: {df['is_fraud'].sum()} ({df['is_fraud'].sum() / len(df) * 100:.2f}%)")
            print(f"Legitimate transactions: {(~df['is_fraud'].astype(bool)).sum()}")
        print(f"\nOutput file: {output_path.absolute()}")
        print("=" * 35)
        
    except Exception as e:
        logger.error(f"Error preparing training data: {str(e)}", exc_info=True)
        raise


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Prepare training data for fraud detection model"
    )
    parser.add_argument(
        '--output',
        type=str,
        default='ml/training/training_data.csv',
        help='Output CSV file path'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of transactions to load'
    )
    parser.add_argument(
        '--no-velocity',
        action='store_true',
        help='Exclude velocity features'
    )
    
    args = parser.parse_args()
    
    # Run preparation
    asyncio.run(prepare_training_data(
        output_file=args.output,
        limit=args.limit,
        use_velocity=not args.no_velocity
    ))


if __name__ == '__main__':
    main()
