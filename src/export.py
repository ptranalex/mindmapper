"""CSV export functionality."""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Union

logger = logging.getLogger(__name__)


class CSVExporter:
    """Exports roadmap data to CSV format."""
    
    CSV_COLUMNS = ['Category', 'Subcategory', 'Topic', 'Description', 'Resources']
    
    def __init__(self, output_dir: str = 'output') -> None:
        """Initialize CSV exporter.
        
        Args:
            output_dir: Directory to save CSV files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export(self, data: List[Dict[str, str]], output_path: Optional[str] = None, roadmap_name: Optional[str] = None) -> Optional[str]:
        """Export data to CSV.
        
        Args:
            data: List of dictionaries with roadmap data
            output_path: Optional custom output path
            roadmap_name: Optional roadmap name for default filename generation
        
        Returns:
            Path to created CSV file
        """
        if not data:
            logger.warning("No data to export")
            return None
        
        # Generate output path if not provided
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # Use roadmap_name if provided, otherwise default to 'roadmap'
            name = roadmap_name.replace('-', '_') if roadmap_name else 'roadmap'
            final_path = self.output_dir / f'roadmap_{name}_{timestamp}.csv'
        else:
            final_path = Path(output_path)
        
        logger.info(f"Exporting {len(data)} rows to {final_path}")
        
        # Write to CSV using built-in csv module
        with open(final_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=self.CSV_COLUMNS,
                quoting=csv.QUOTE_ALL
            )
            writer.writeheader()
            
            # Write each row, ensuring all columns exist
            for row in data:
                formatted_row = {col: row.get(col, '') for col in self.CSV_COLUMNS}
                writer.writerow(formatted_row)
        
        logger.info(f"Successfully exported to {final_path}")
        return str(final_path)
    
    def format_row(self, category: str, subcategory: str, topic: str, 
                   description: str, resources: str) -> Dict[str, str]:
        """Format a single row for export.
        
        Args:
            category: Category name
            subcategory: Subcategory name
            topic: Topic name
            description: Topic description
            resources: Pipe-separated resource URLs
        
        Returns:
            Dictionary with formatted data
        """
        return {
            'Category': category or '',
            'Subcategory': subcategory or '',
            'Topic': topic or '',
            'Description': description or '',
            'Resources': resources or ''
        }

