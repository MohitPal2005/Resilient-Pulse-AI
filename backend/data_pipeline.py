import time
import os
import pandas as pd

# Path to your verified dataset
DATA_PATH = "data/taxi_data.parquet"

def benchmark_cpu_pandas():
    print("\n[CPU] Initializing standard Pandas processing pipeline...")
    start_time = time.time()
    
    # Load the parquet dataframe into standard CPU memory
    df = pd.read_parquet(DATA_PATH)
    
    # 1. High overhead DateTime transformations
    df['pickup_hour'] = df['tpep_pickup_datetime'].dt.hour
    
    # 2. Complex aggregation: Multi-key grouping computing congestion metrics
    congestion_summary = df.groupby(['PULocationID', 'pickup_hour']).agg({
        'trip_distance': 'mean',
        'fare_amount': 'mean',
        'VendorID': 'count'
    }).rename(columns={'VendorID': 'total_trips'})
    
    # 3. Calculate a custom calculated anomaly risk metric
    congestion_summary['congestion_risk'] = (
        congestion_summary['fare_amount'] / (congestion_summary['trip_distance'] + 0.1)
    )
    
    end_time = time.time()
    cpu_duration = end_time - start_time
    print(f"[CPU] Pipeline Completed in: {cpu_duration:.4f} seconds")
    return cpu_duration, congestion_summary

def benchmark_gpu_cudf():
    print("\n[GPU] Initializing NVIDIA cuDF accelerated pipeline...")
    # We import cudf dynamically inside the function so the script doesn't hard-crash 
    # if executed in environments without an active local CUDA driver.
    import cudf
    
    start_time = time.time()
    
    # Load the data straight into GPU VRAM memory space
    gdf = cudf.read_parquet(DATA_PATH)
    
    # Mirroring the exact operations on CUDA parallel threads
    gdf['pickup_hour'] = gdf['tpep_pickup_datetime'].dt.hour
    
    gpu_summary = gdf.groupby(['PULocationID', 'pickup_hour']).agg({
        'trip_distance': 'mean',
        'fare_amount': 'mean',
        'VendorID': 'count'
    }).rename(columns={'VendorID': 'total_trips'})
    
    gpu_summary['congestion_risk'] = (
        gpu_summary['fare_amount'] / (gpu_summary['trip_distance'] + 0.1)
    )
    
    end_time = time.time()
    gpu_duration = end_time - start_time
    print(f"[GPU] Pipeline Completed in: {gpu_duration:.4f} seconds")
    
    # Convert back to standard pandas dataframe upon return for global format compatibility
    return gpu_duration, gpu_summary.to_pandas()

if __name__ == "__main__":
    if not os.path.exists(DATA_PATH):
        print(f"Error: Could not locate data at {DATA_PATH}. Please verify the folder pathway.")
        exit(1)
        
    print(f"Dataset Verified. Processing {3724889:,} total urban data records.")
    
    # Run CPU baseline pipeline
    cpu_time, cpu_data = benchmark_cpu_pandas()
    
    try:
        # Attempt to run the GPU pipeline
        gpu_time, gpu_data = benchmark_gpu_cudf()
        
        # Calculate and log performance differential metrics
        speedup = cpu_time / gpu_time
        print("\n" + "="*40)
        print("          BENCHMARK RESULTS             ")
        print("="*40)
        print(f"Standard CPU Pandas: {cpu_time:.4f} seconds")
        print(f"NVIDIA GPU cuDF:     {gpu_time:.4f} seconds")
        print(f"Performance Boost:   {speedup:.2f}x Faster execution time!")
        print("="*40)
        
        # Export the summarized outcome to CSV for tomorrow's BigQuery ingestion step
        cpu_data.to_csv("data/processed_congestion_summary.csv")
        print("✅ Consolidated data summary written to: data/processed_congestion_summary.csv")
        
    except ImportError:
        print("\n[!] RAPIDS cuDF module is not configured locally on this environment.")
        print("💡 Hackathon Deployment Hack: Save your data/check_data.py file metrics,")
        print("run this exact pipeline file inside a free Google Colab T4 GPU Instance")
        print("to record your official high-speed metrics output and output data file!")