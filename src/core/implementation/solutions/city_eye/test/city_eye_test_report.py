#!/usr/bin/env python3

"""
Unified Test Report Generation Tool for CityEye

This script generates combined reports for human and vehicle detection from test results
stored in the database
"""

import os
import sys
import argparse
import pandas as pd
# import matplotlib.pyplot as plt
from pathlib import Path

from core.implementation.common.sqlite_manager import DatabaseManager
from core.implementation.solutions.city_eye.test.test_utils import (
    get_test_results,
    export_test_results_csv,
    get_test_statistics
)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="CityEye Test Results Reporter")
    
    parser.add_argument(
        "--db-dir",
        required=True,
        help="Base directory for database files"
    )
    
    parser.add_argument(
        "--output-dir",
        default="../reports",
        help="Directory to save reports (default: ./reports)"
    )
    
    parser.add_argument(
        "--format",
        choices=["csv", "plot", "all"],
        default="all",
        help="Report format (default: all)"
    )
    
    parser.add_argument(
        "--video",
        help="Filter results for a specific video file"
    )
    
    return parser.parse_args()

def generate_csv_report(db_manager, output_dir, video_file=None):
    """Generate CSV report of test results"""
    try:
        # If video file specified, export only that result
        if video_file:
            results = get_test_results(db_manager, video_file)
            if not results:
                print(f"No test results found" + (f" for video: {video_file}" if video_file else ""))
                return None
                
            df = pd.DataFrame(results)


            output_file = os.path.join(output_dir, f"{video_file}_unified_test_results.csv")

            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)

            df.to_csv(output_file, index=False)
            print(f"Unified CSV report generated: {output_file}")

            return output_file
        else:
            print("No video file provided to produce test result for")

    except Exception as e:
        print(f"Error generating CSV report: {str(e)}")
        return None

def generate_plot_report(db_manager, output_dir, video_file=None):
    """Generate plot visualizations of test results"""
    try:
        results = get_test_results(db_manager, video_file)
        
        if not results:
            print("No test results found for plotting")
            return None
            
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert to DataFrame for easier plotting
        df = pd.DataFrame(results)
        
        # 1. Generate gender distribution plot
        plt.figure(figsize=(10, 6))
        
        if video_file:
            # Single video plot
            result = results[0]
            labels = ['Male', 'Female']
            values = [result['male_count'], result['female_count']]
            plt.pie(values, labels=labels, autopct='%1.1f%%')
            plt.title(f'Gender Distribution - {video_file}')
        else:
            # Aggregate plot
            male_total = df['male_count'].sum()
            female_total = df['female_count'].sum()
            labels = ['Male', 'Female']
            values = [male_total, female_total]
            plt.pie(values, labels=labels, autopct='%1.1f%%')
            plt.title('Gender Distribution - All Videos')
            
        gender_plot = os.path.join(output_dir, 'gender_distribution.png')
        plt.savefig(gender_plot)
        plt.close()
        
        # 2. Generate detailed age-gender distribution plot
        plt.figure(figsize=(14, 8))
        
        if video_file:
            # Single video plot
            result = results[0]
            age_categories = ['Child', 'Young', 'Middle', 'Senior', 'Silver']
            
            # Set up grouped bar chart
            x = np.arange(len(age_categories))
            width = 0.35
            
            # Get values from result
            male_values = [
                result['male_child'],
                result['male_young'],
                result['male_middle'],
                result['male_senior'],
                result['male_silver']
            ]
            
            female_values = [
                result['female_child'],
                result['female_young'],
                result['female_middle'],
                result['female_senior'],
                result['female_silver']
            ]
            
            # Create grouped bars
            plt.bar(x - width/2, male_values, width, label='Male')
            plt.bar(x + width/2, female_values, width, label='Female')
            
            plt.xlabel('Age Group')
            plt.ylabel('Count')
            plt.title(f'Age-Gender Distribution - {video_file}')
            plt.xticks(x, age_categories)
            plt.legend()
            
        else:
            # Aggregate plot for all videos
            age_categories = ['Child', 'Young', 'Middle', 'Senior', 'Silver']
            
            # Set up grouped bar chart
            x = np.arange(len(age_categories))
            width = 0.35
            
            # Sum values across all videos
            male_values = [
                df['male_child'].sum(),
                df['male_young'].sum(),
                df['male_middle'].sum(),
                df['male_senior'].sum(),
                df['male_silver'].sum()
            ]
            
            female_values = [
                df['female_child'].sum(),
                df['female_young'].sum(),
                df['female_middle'].sum(),
                df['female_senior'].sum(),
                df['female_silver'].sum()
            ]
            
            # Create grouped bars
            plt.bar(x - width/2, male_values, width, label='Male')
            plt.bar(x + width/2, female_values, width, label='Female')
            
            plt.xlabel('Age Group')
            plt.ylabel('Count')
            plt.title('Age-Gender Distribution - All Videos')
            plt.xticks(x, age_categories)
            plt.legend()
        
        plt.tight_layout()
        age_plot = os.path.join(output_dir, 'age_gender_distribution.png')
        plt.savefig(age_plot)
        plt.close()
        
        # Also generate a simpler age distribution chart (combined genders)
        plt.figure(figsize=(12, 6))
        
        if video_file:
            # Single video plot
            result = results[0]
            age_labels = ['Child', 'Young', 'Middle', 'Senior', 'Silver']
            age_values = [
                result['male_child'] + result['female_child'],
                result['male_young'] + result['female_young'],
                result['male_middle'] + result['female_middle'],
                result['male_senior'] + result['female_senior'],
                result['male_silver'] + result['female_silver']
            ]
            plt.bar(age_labels, age_values)
            plt.title(f'Age Distribution - {video_file}')
        else:
            # Aggregate plot
            age_labels = ['Child', 'Young', 'Middle', 'Senior', 'Silver']
            age_values = [
                df['male_child'].sum() + df['female_child'].sum(),
                df['male_young'].sum() + df['female_young'].sum(),
                df['male_middle'].sum() + df['female_middle'].sum(),
                df['male_senior'].sum() + df['female_senior'].sum(),
                df['male_silver'].sum() + df['female_silver'].sum()
            ]
            plt.bar(age_labels, age_values)
            plt.title('Age Distribution - All Videos')
            
        plt.ylabel('Count')
        simple_age_plot = os.path.join(output_dir, 'age_distribution.png')
        plt.savefig(simple_age_plot)
        plt.close()
        
        # 3. If multiple videos, generate video comparison plot
        if not video_file and len(results) > 1:
            plt.figure(figsize=(14, 8))
            
            # Sort by total count for better visualization
            df = df.sort_values(by='total_human', ascending=False)
            
            # Use bar plot for comparison
            plt.bar(df['video_file_name'], df['total_human'])
            plt.xticks(rotation=45, ha='right')
            plt.title('Detection Count Comparison by Video')
            plt.ylabel('Total Detections')
            plt.tight_layout()
            
            video_comp_plot = os.path.join(output_dir, 'video_comparison.png')
            plt.savefig(video_comp_plot)
            plt.close()
            
        print(f"Plot reports generated in: {output_dir}")
        return output_dir
        
    except Exception as e:
        print(f"Error generating plot report: {str(e)}")
        return None

def main():
    """Main function"""
    args = parse_args()
    
    # Create database manager
    db_manager = DatabaseManager(args.db_dir)
    
    # Generate requested reports
    if args.format in ['csv', 'all']:
        generate_csv_report(db_manager, args.output_dir, args.video)
        
    # if args.format in ['plot', 'all']:
    #     generate_plot_report(db_manager, args.output_dir, args.video)
    
    # Print statistics
    stats = get_test_statistics(db_manager)
    
    print("\n== CityEye Test Statistics ==")
    print(f"Total videos processed: {stats['total_videos']}")
    print(f"Total detections: {stats['total_human']}")
    print("\nGender Ratio:")
    print(f"  Male: {stats['gender_ratio']['male']:.1f}%")
    print(f"  Female: {stats['gender_ratio']['female']:.1f}%")
    print("\nAge Distribution:")
    print(f"  Child: {stats['age_distribution']['child']:.1f}%")
    print(f"  Young: {stats['age_distribution']['young']:.1f}%")
    print(f"  Middle: {stats['age_distribution']['middle']:.1f}%")
    print(f"  Senior: {stats['age_distribution']['senior']:.1f}%")
    print(f"  Silver: {stats['age_distribution']['silver']:.1f}%")
    
    print("\nDetailed Age-Gender Counts:")
    print(f"  Male Child: {stats['age_gender_distribution']['male_child']}")
    print(f"  Female Child: {stats['age_gender_distribution']['female_child']}")
    print(f"  Male Young: {stats['age_gender_distribution']['male_young']}")
    print(f"  Female Young: {stats['age_gender_distribution']['female_young']}")
    print(f"  Male Middle: {stats['age_gender_distribution']['male_middle']}")
    print(f"  Female Middle: {stats['age_gender_distribution']['female_middle']}")
    print(f"  Male Senior: {stats['age_gender_distribution']['male_senior']}")
    print(f"  Female Senior: {stats['age_gender_distribution']['female_senior']}")
    print(f"  Male Silver: {stats['age_gender_distribution']['male_silver']}")
    print(f"  Female Silver: {stats['age_gender_distribution']['female_silver']}")
    print(f"  Bus: {stats['traffic_distribution']['bus']}")
    print(f"  Truck: {stats['traffic_distribution']['truck']}")
    print(f"  Motocycle: {stats['traffic_distribution']['motorcycle']}")
    print(f"  Bicycle: {stats['traffic_distribution']['bicycle']}")
    print(f"  Car: {stats['traffic_distribution']['car']}")

    
    if args.video:
        print(f"\nResults filtered for video: {args.video}")
    else:
        print("\nVideos processed:")
        for i, video in enumerate(stats['videos_processed'], 1):
            print(f"  {i}. {video}")

    print(stats)
    
if __name__ == "__main__":
    main()