#!/usr/bin/env python3
"""
Sample Python script for data analysis.
Demonstrates various Python programming concepts.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json
import csv


def load_data(file_path: str) -> pd.DataFrame:
    """
    Load data from CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        DataFrame with loaded data
    """
    try:
        df = pd.read_csv(file_path)
        print(f"Loaded {len(df)} rows from {file_path}")
        return df
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return pd.DataFrame()


def analyze_sales_data(df: pd.DataFrame) -> dict:
    """
    Perform basic analysis on sales data.
    
    Args:
        df: DataFrame containing sales data
        
    Returns:
        Dictionary with analysis results
    """
    if df.empty:
        return {}
    
    analysis = {
        'total_sales': df['amount'].sum() if 'amount' in df.columns else 0,
        'average_sale': df['amount'].mean() if 'amount' in df.columns else 0,
        'max_sale': df['amount'].max() if 'amount' in df.columns else 0,
        'min_sale': df['amount'].min() if 'amount' in df.columns else 0,
        'total_transactions': len(df),
        'unique_customers': df['customer_id'].nunique() if 'customer_id' in df.columns else 0
    }
    
    return analysis


def create_visualizations(df: pd.DataFrame, output_dir: str = './charts/'):
    """
    Create visualization charts from the data.
    
    Args:
        df: DataFrame with data to visualize
        output_dir: Directory to save charts
    """
    if df.empty:
        return
    
    # Sales over time
    if 'date' in df.columns and 'amount' in df.columns:
        plt.figure(figsize=(12, 6))
        df['date'] = pd.to_datetime(df['date'])
        daily_sales = df.groupby('date')['amount'].sum()
        
        plt.subplot(1, 2, 1)
        daily_sales.plot(kind='line')
        plt.title('Daily Sales Trend')
        plt.xlabel('Date')
        plt.ylabel('Sales Amount')
        
        # Sales distribution
        plt.subplot(1, 2, 2)
        df['amount'].hist(bins=20)
        plt.title('Sales Amount Distribution')
        plt.xlabel('Amount')
        plt.ylabel('Frequency')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/sales_analysis.png')
        plt.close()


def export_results(analysis: dict, file_path: str):
    """
    Export analysis results to JSON file.
    
    Args:
        analysis: Dictionary with analysis results
        file_path: Path to save the results
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        print(f"Results exported to {file_path}")
    except Exception as e:
        print(f"Error exporting results: {e}")


def generate_sample_data(num_records: int = 1000) -> pd.DataFrame:
    """
    Generate sample sales data for testing.
    
    Args:
        num_records: Number of records to generate
        
    Returns:
        DataFrame with sample data
    """
    np.random.seed(42)
    
    start_date = datetime.now() - timedelta(days=365)
    dates = [start_date + timedelta(days=x) for x in range(365)]
    
    data = {
        'date': np.random.choice(dates, num_records),
        'customer_id': np.random.randint(1, 100, num_records),
        'product': np.random.choice(['Widget A', 'Widget B', 'Service X', 'Service Y'], num_records),
        'amount': np.random.exponential(50, num_records).round(2),
        'region': np.random.choice(['North', 'South', 'East', 'West'], num_records)
    }
    
    return pd.DataFrame(data)


def main():
    """Main execution function."""
    print("Starting data analysis...")
    
    # Generate sample data
    sample_df = generate_sample_data(1000)
    
    # Perform analysis
    results = analyze_sales_data(sample_df)
    
    print("\nAnalysis Results:")
    for key, value in results.items():
        print(f"  {key}: {value}")
    
    # Create visualizations
    create_visualizations(sample_df)
    
    # Export results
    export_results(results, 'analysis_results.json')
    
    print("\nAnalysis completed successfully!")


if __name__ == "__main__":
    main()
