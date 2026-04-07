#!/usr/bin/env python3
"""
PhotSatQM Data Analyzer
Reads CSV files from Day1 to Day11, combines them, and generates visualizations
for all variables with respect to date and time.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import os
import glob
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set up plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class PhotSatQMDataAnalyzer:
    def __init__(self, data_directory="photsatQM"):
        """Initialize the analyzer with the data directory. Edit the directory for each case!!"""
        self.data_directory = Path(data_directory)
        self.combined_data = None
        # Create unique folder name to avoid conflicts
        base_name = "photsatqm_visualizations"
        counter = 1
        while Path(f"{base_name}-{counter}").exists():
            counter += 1
        self.output_dir = Path(f"{base_name}-{counter}")
        self.output_dir.mkdir(exist_ok=True)
        
    def load_and_combine_data(self):
        """Load and combine all CSV files from Day1 to Day11. Adjust for each case!!!"""
        print("Loading and combining PhotSatQM CSV files...")
        
        # Get all CSV files matching the pattern
        csv_files = sorted(glob.glob(str(self.data_directory / "PhotSatQM_Day*.csv")))
        
        if not csv_files:
            raise FileNotFoundError("No PhotSatQM CSV files found in the specified directory")
        
        print(f"Found {len(csv_files)} CSV files:")
        for file in csv_files:
            print(f"  - {Path(file).name}")
        
        # Read and combine all CSV files
        dataframes = []
        for file in csv_files:
            print(f"Reading {Path(file).name}...")
            try:
                # Try different encodings
                encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                df = None
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file, encoding=encoding)
                        print(f"  Successfully read with {encoding} encoding")
                        break
                    except UnicodeDecodeError:
                        continue
                
                if df is None:
                    print(f"  Could not read with any encoding")
                    continue
                    
                # Add source file column for reference
                df['Source_File'] = Path(file).stem
                dataframes.append(df)
            except Exception as e:
                print(f"Error reading {file}: {e}")
                continue
        
        if not dataframes:
            raise ValueError("No valid CSV files could be read")
        
        # Combine all dataframes
        self.combined_data = pd.concat(dataframes, ignore_index=True)
        
        # Convert the datetime column
        self.combined_data['Data Ora'] = pd.to_datetime(self.combined_data['Data Ora'])
        
        # Sort by datetime
        self.combined_data = self.combined_data.sort_values('Data Ora').reset_index(drop=True)
        
        print(f"Combined data shape: {self.combined_data.shape}")
        print(f"Date range: {self.combined_data['Data Ora'].min()} to {self.combined_data['Data Ora'].max()}")
        
        return self.combined_data
    
    def get_numeric_columns(self):
        """Get all numeric columns (excluding datetime and source file)."""
        numeric_cols = self.combined_data.select_dtypes(include=[np.number]).columns.tolist()
        # Remove source file if it's numeric
        if 'Source_File' in numeric_cols:
            numeric_cols.remove('Source_File')
        return numeric_cols
    
    def add_daily_grid(self, ax):
        """Add vertical grid lines for each day from Day1 to Day11."""
        import matplotlib.dates as mdates
        from datetime import datetime, timedelta
        
        # Get the actual date range from the data
        start_date = self.combined_data['Data Ora'].min().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = self.combined_data['Data Ora'].max().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Generate daily grid lines
        current_date = start_date
        while current_date <= end_date + timedelta(days=1):
            ax.axvline(x=current_date, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
            # Add date labels
            ax.text(current_date, ax.get_ylim()[1] * 0.95, current_date.strftime('%m/%d'), 
                   rotation=90, ha='right', va='top', fontsize=8, alpha=0.7)
            current_date += timedelta(days=1)
    
    def create_monitoring_tcs_with_pressure_chart(self):
        """Create chart showing all monitoring TCs (1-10) with chamber vacuum pressure on secondary axis."""
        print("Creating monitoring TCs with pressure chart...")
        
        # Get monitoring TC columns (A0-104 to A0-113, excluding TQCM)
        monitoring_tcs = [col for col in self.combined_data.columns 
                         if (col.startswith('[A0-10') and 'TC' in col and 'TQCM' not in col and 'A0-114' not in col) or 
                            (col.startswith('[A0-11') and 'TC' in col and 'TQCM' not in col)]
        
        print(f"Found {len(monitoring_tcs)} monitoring TCs: {monitoring_tcs}")
        
        fig, ax1 = plt.subplots(figsize=(20, 10))
        
        # Define distinct colors for better clarity
        tc_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        # Plot monitoring TCs on primary axis
        for i, col in enumerate(monitoring_tcs):
            ax1.plot(self.combined_data['Data Ora'], self.combined_data[col], 
                    linewidth=1, alpha=0.8, color=tc_colors[i], 
                    label=col.replace('[', '').replace(']', ''))
        
        ax1.set_xlabel('Date & Time', fontsize=12)
        ax1.set_ylabel('Temperature (°C)', fontsize=12, color='black')
        ax1.tick_params(axis='y', labelcolor='black')
        ax1.set_ylim(-50, 75)  # Adjusted range for PhotSatQM data
        ax1.set_yticks(range(-50, 76, 25))  # 25 degree intervals
        ax1.grid(True, alpha=0.5, color='lightgray', linewidth=0.5)
        
        # Set x-axis limits based on actual data range
        ax1.set_xlim(self.combined_data['Data Ora'].min(), self.combined_data['Data Ora'].max())
        
        # Create secondary axis for chamber vacuum pressure
        ax2 = ax1.twinx()
        ax2.plot(self.combined_data['Data Ora'], self.combined_data['Chamber Vacuum Pressure'], 
                linewidth=1, color='red', alpha=0.8, label='Chamber Vacuum Pressure')
        ax2.set_ylabel('Chamber Vacuum Pressure (mbar)', fontsize=12, color='red')
        ax2.tick_params(axis='y', labelcolor='red')
        ax2.set_yscale('log')
        ax2.set_ylim(1e-8, 1e3)
        # Set specific tick locations for orders of magnitude
        ax2.set_yticks([1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1e0, 1e1, 1e2, 1e3])
        ax2.set_yticklabels(['10$^{-8}$', '10$^{-7}$', '10$^{-6}$', '10$^{-5}$', '10$^{-4}$', '10$^{-3}$', '10$^{-2}$', '10$^{-1}$', '10$^{0}$', '10$^{1}$', '10$^{2}$', '10$^{3}$'])
        
        # Add daily vertical grid lines
        self.add_daily_grid(ax1)
        
        # Combine legends and place at top
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper center', 
                  bbox_to_anchor=(0.5, 1.15), ncol=6, fontsize=10)
        
        plt.title('PhotSatQM - Monitoring TCs (1-10) and Chamber Vacuum Pressure', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'monitoring_tcs_with_pressure.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("Monitoring TCs with pressure chart saved as 'monitoring_tcs_with_pressure.png'")
    
    def create_monitoring_tcs_with_slave_temps_chart(self):
        """Create chart showing all monitoring TCs and slave temperatures."""
        print("Creating monitoring TCs with slave temperatures chart...")
        
        # Get monitoring TC columns (A0-104 to A0-113, excluding TQCM)
        monitoring_tcs = [col for col in self.combined_data.columns 
                         if (col.startswith('[A0-10') and 'TC' in col and 'TQCM' not in col and 'A0-114' not in col) or 
                            (col.startswith('[A0-11') and 'TC' in col and 'TQCM' not in col)]
        
        # Get slave temperature columns
        slave_temps = [col for col in self.combined_data.columns 
                      if 'Slave Temperature' in col]
        
        print(f"Found {len(monitoring_tcs)} monitoring TCs: {monitoring_tcs}")
        print(f"Found {len(slave_temps)} slave temps: {slave_temps}")
        
        fig, ax = plt.subplots(figsize=(20, 10))
        
        # Define distinct colors for better clarity
        tc_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        slave_colors = ['#ff1493', '#00ced1']  # Distinct colors for slave temps
        
        # Plot monitoring TCs
        for i, col in enumerate(monitoring_tcs):
            ax.plot(self.combined_data['Data Ora'], self.combined_data[col], 
                   linewidth=1, alpha=0.8, color=tc_colors[i], 
                   label=col.replace('[', '').replace(']', ''))
        
        # Plot slave temperatures with same style as monitoring TCs
        for i, col in enumerate(slave_temps):
            ax.plot(self.combined_data['Data Ora'], self.combined_data[col], 
                   linewidth=1, alpha=0.8, color=slave_colors[i],
                   label=col.replace('[', '').replace(']', ''))
        
        ax.set_xlabel('Date & Time', fontsize=12)
        ax.set_ylabel('Temperature (°C)', fontsize=12)
        ax.set_ylim(-50, 75)  # Adjusted range for PhotSatQM data
        ax.set_yticks(range(-50, 76, 25))  # 25 degree intervals
        ax.grid(True, alpha=0.5, color='lightgray', linewidth=0.5)
        
        # Set x-axis limits based on actual data range
        ax.set_xlim(self.combined_data['Data Ora'].min(), self.combined_data['Data Ora'].max())
        
        # Add daily vertical grid lines
        self.add_daily_grid(ax)
        
        # Place legend at top to maximize data space
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=6, fontsize=10)
        
        plt.title('PhotSatQM - Monitoring TCs (1-10) and Slave Temperatures', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'monitoring_tcs_with_slave_temps.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("Monitoring TCs with slave temperatures chart saved as 'monitoring_tcs_with_slave_temps.png'")
    
    def create_pressure_measures_chart(self):
        """Create chart showing all pressure measures (V0) with logarithmic axis."""
        print("Creating pressure measures chart...")
        
        # Get pressure measure columns (V0-) excluding V0-211, plus chamber vacuum pressure
        pressure_cols = [col for col in self.combined_data.columns 
                        if col.startswith('V0-') and 'V0-211' not in col]
        
        # Add chamber vacuum pressure
        pressure_cols.append('Chamber Vacuum Pressure')
        
        print(f"Found {len(pressure_cols)} pressure measures: {pressure_cols}")
        
        fig, ax = plt.subplots(figsize=(20, 10))
        
        # Define colors: light grey tones for pressure measurements, green for chamber vacuum
        pressure_colors = ['#A0A0A0', '#C0C0C0', '#2ca02c']  # Light Grey, Lighter Grey, Green
        
        # Plot pressure measures
        for i, col in enumerate(pressure_cols):
            ax.plot(self.combined_data['Data Ora'], self.combined_data[col], 
                   linewidth=1, alpha=0.8, color=pressure_colors[i], 
                   label=col)
        
        ax.set_xlabel('Date & Time', fontsize=12)
        ax.set_ylabel('Pressure (mbar)', fontsize=12)
        ax.set_yscale('log')
        ax.set_ylim(1e-8, 1e3)
        # Set specific tick locations for orders of magnitude
        ax.set_yticks([1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1e0, 1e1, 1e2, 1e3])
        ax.set_yticklabels(['10$^{-8}$', '10$^{-7}$', '10$^{-6}$', '10$^{-5}$', '10$^{-4}$', '10$^{-3}$', '10$^{-2}$', '10$^{-1}$', '10$^{0}$', '10$^{1}$', '10$^{2}$', '10$^{3}$'])
        ax.grid(True, alpha=0.3)
        
        # Set x-axis limits based on actual data range
        ax.set_xlim(self.combined_data['Data Ora'].min(), self.combined_data['Data Ora'].max())
        
        # Add daily vertical grid lines
        self.add_daily_grid(ax)
        
        # Place legend at top to maximize data space
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=4, fontsize=10)
        
        plt.title('PhotSatQM - Pressure Measures (V0) and Chamber Vacuum Pressure - Logarithmic Scale', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'pressure_measures.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("Pressure measures chart saved as 'pressure_measures.png'")
    
    def generate_summary_report(self):
        """Generate a summary report of the analysis."""
        print("Generating summary report...")
        
        report_path = self.output_dir / 'analysis_summary.txt'
        
        with open(report_path, 'w') as f:
            f.write("PHOTSATQM DATA ANALYSIS SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Data Directory: {self.data_directory}\n\n")
            
            f.write("DATA OVERVIEW:\n")
            f.write(f"Total Records: {len(self.combined_data):,}\n")
            f.write(f"Date Range: {self.combined_data['Data Ora'].min()} to {self.combined_data['Data Ora'].max()}\n")
            f.write(f"Total Variables: {len(self.get_numeric_columns())}\n")
            f.write(f"Memory Usage: {self.combined_data.memory_usage(deep=True).sum() / 1024**2:.2f} MB\n\n")
            
            f.write("GENERATED VISUALIZATIONS:\n")
            f.write("1. monitoring_tcs_with_pressure.png - Monitoring TCs (1-10) with Chamber Vacuum Pressure (log scale)\n")
            f.write("2. monitoring_tcs_with_slave_temps.png - Monitoring TCs (1-10) with Slave Temperatures\n")
            f.write("3. pressure_measures.png - All Pressure Measures (V0) with Logarithmic Scale\n")
            
            f.write(f"\nCHART DETAILS:\n")
            f.write("-" * 30 + "\n")
            f.write("Chart 1: Monitoring TCs (1-10) + Chamber Vacuum Pressure\n")
            f.write("  - Primary axis: Temperature (°C) for monitoring TCs\n")
            f.write("  - Secondary axis: Chamber Vacuum Pressure (mbar, log scale 10^-8 to 10^3)\n")
            f.write("  - Excludes TQCM sensor\n")
            f.write("  - Temperature range: -50°C to 75°C\n\n")
            
            f.write("Chart 2: Monitoring TCs (1-10) + Slave Temperatures\n")
            f.write("  - All monitoring TCs (1-10) on same scale\n")
            f.write("  - Slave temperatures for Shroud and ThPlate\n")
            f.write("  - Excludes TQCM sensor\n")
            f.write("  - Temperature range: -50°C to 75°C\n\n")
            
            f.write("Chart 3: All Pressure Measures (V0)\n")
            f.write("  - All V0- pressure sensors\n")
            f.write("  - Logarithmic scale for better visualization\n")
            f.write("  - Includes: BackinglinePressure, Chamber High Vacuum, Vacuum Sensor CO2 Test\n")
        
        print(f"Summary report saved as 'analysis_summary.txt'")
    
    def run_complete_analysis(self):
        """Run the complete analysis pipeline."""
        print("Starting PhotSatQM Data Analysis...")
        print("=" * 50)
        
        try:
            # Load and combine data
            self.load_and_combine_data()
            
            # Create the three specific visualizations
            self.create_monitoring_tcs_with_pressure_chart()
            self.create_monitoring_tcs_with_slave_temps_chart()
            self.create_pressure_measures_chart()
            
            # Generate summary report
            self.generate_summary_report()
            
            print("\n" + "=" * 50)
            print("ANALYSIS COMPLETE!")
            print(f"All visualizations saved in: {self.output_dir}")
            print("=" * 50)
            
        except Exception as e:
            print(f"Error during analysis: {e}")
            raise

def main():
    """Main function to run the analysis."""
    # Initialize analyzer
    analyzer = PhotSatQMDataAnalyzer()
    
    # Run complete analysis
    analyzer.run_complete_analysis()

if __name__ == "__main__":
    main()
