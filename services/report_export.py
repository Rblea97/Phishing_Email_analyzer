"""
Report Export Service - Phase 4 Enhancement
PDF and JSON report generation for analysis results

Provides professional reporting capabilities for single analyses,
batch processing results, and system performance metrics.
"""

import base64
import json
import logging
import os
import sqlite3
import tempfile
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# PDF generation imports
try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Image as RLImage
    from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate,
                                    Spacer, Table, TableStyle)
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Alternative PDF generation
try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    # Handle both ImportError and OSError (for missing system libraries)
    WEASYPRINT_AVAILABLE = False
    if 'gobject' in str(e) or 'cannot load library' in str(e):
        pass  # Expected on Windows without GTK libraries
    else:
        import logging
        logging.getLogger(__name__).warning(f"WeasyPrint unavailable: {e}")

logger = logging.getLogger(__name__)

@dataclass
class ExportRequest:
    """Export request configuration"""
    request_id: str
    export_type: str  # 'pdf', 'json', 'csv', 'html'
    data_type: str   # 'single_analysis', 'batch_results', 'performance_report'
    reference_id: str  # ID of what's being exported
    settings: Dict = None
    created_at: datetime = None

@dataclass
class ExportResult:
    """Export operation result"""
    request_id: str
    status: str  # 'completed', 'failed', 'pending'
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime = None

class ReportExportError(Exception):
    """Custom exception for report export errors"""
    pass

class ReportExportService:
    """
    Professional report generation service for phishing analysis results
    Supports multiple formats and comprehensive data visualization
    """
    
    def __init__(self):
        self.db_path = os.getenv('DATABASE_PATH', 'data/phishing_analyzer.db')
        self.export_dir = Path(os.getenv('EXPORT_DIR', 'data/exports'))
        self.template_dir = Path(os.getenv('TEMPLATE_DIR', 'templates/reports'))
        
        # Ensure directories exist
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Export settings
        self.max_export_age_hours = int(os.getenv('EXPORT_RETENTION_HOURS', '72'))  # 3 days
        self.max_file_size_mb = int(os.getenv('MAX_EXPORT_FILE_SIZE_MB', '100'))
        
        # PDF configuration
        self.pdf_available = REPORTLAB_AVAILABLE or WEASYPRINT_AVAILABLE
        
        logger.info(f"ReportExportService initialized - PDF: {self.pdf_available}")

    def _get_db_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def create_export_request(self, 
                            export_type: str,
                            data_type: str, 
                            reference_id: str,
                            settings: Optional[Dict] = None) -> str:
        """
        Create new export request
        
        Args:
            export_type: Format to export ('pdf', 'json', 'csv', 'html')
            data_type: Type of data to export
            reference_id: ID of the data to export
            settings: Additional export settings
            
        Returns:
            Export request ID
        """
        request_id = str(uuid.uuid4())
        
        try:
            conn = self._get_db_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO export_requests 
                    (id, export_type, data_type, reference_id, status, settings, created_at)
                    VALUES (?, ?, ?, ?, 'pending', ?, ?)
                """, (
                    request_id, export_type, data_type, reference_id,
                    json.dumps(settings or {}), datetime.now().isoformat()
                ))
                conn.commit()
                
                logger.info(f"Created export request {request_id}: {export_type} {data_type}")
                return request_id
                
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Failed to create export request: {e}")
            raise ReportExportError(f"Export request creation failed: {e}")

    def process_export_request(self, request_id: str) -> ExportResult:
        """
        Process an export request
        
        Args:
            request_id: Export request ID
            
        Returns:
            ExportResult with status and file info
        """
        try:
            # Get request details
            request = self._get_export_request(request_id)
            if not request:
                raise ReportExportError(f"Export request {request_id} not found")
            
            # Update status to processing
            self._update_export_status(request_id, 'generating')
            
            # Generate the report based on type
            file_path = None
            
            if request['data_type'] == 'single_analysis':
                file_path = self._export_single_analysis(
                    request['reference_id'],
                    request['export_type'], 
                    json.loads(request['settings'] or '{}')
                )
            elif request['data_type'] == 'batch_results':
                file_path = self._export_batch_results(
                    request['reference_id'],
                    request['export_type'],
                    json.loads(request['settings'] or '{}')
                )
            elif request['data_type'] == 'performance_report':
                file_path = self._export_performance_report(
                    request['reference_id'],
                    request['export_type'],
                    json.loads(request['settings'] or '{}')
                )
            else:
                raise ReportExportError(f"Unsupported data type: {request['data_type']}")
            
            if not file_path or not Path(file_path).exists():
                raise ReportExportError("Export file generation failed")
            
            # Get file size
            file_size = Path(file_path).stat().st_size
            
            # Update request with completion
            self._complete_export_request(request_id, file_path, file_size)
            
            return ExportResult(
                request_id=request_id,
                status='completed',
                file_path=file_path,
                file_size=file_size,
                created_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Export request {request_id} failed: {e}")
            self._update_export_status(request_id, 'failed', str(e))
            
            return ExportResult(
                request_id=request_id,
                status='failed',
                error_message=str(e),
                created_at=datetime.now()
            )

    def _get_export_request(self, request_id: str) -> Optional[Dict]:
        """Get export request details"""
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM export_requests WHERE id = ?", (request_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def _update_export_status(self, request_id: str, status: str, error_message: str = None):
        """Update export request status"""
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            if error_message:
                cursor.execute("""
                    UPDATE export_requests 
                    SET status = ?, error_message = ?, started_at = ?
                    WHERE id = ?
                """, (status, error_message, datetime.now().isoformat(), request_id))
            else:
                cursor.execute("""
                    UPDATE export_requests 
                    SET status = ?, started_at = ?
                    WHERE id = ?
                """, (status, datetime.now().isoformat(), request_id))
            conn.commit()
        finally:
            conn.close()

    def _complete_export_request(self, request_id: str, file_path: str, file_size: int):
        """Mark export request as completed"""
        # Set expiry time
        expiry_time = datetime.now() + timedelta(hours=self.max_export_age_hours)
        
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE export_requests 
                SET status = 'completed', file_path = ?, file_size = ?,
                    completed_at = ?, expires_at = ?
                WHERE id = ?
            """, (
                file_path, file_size, datetime.now().isoformat(),
                expiry_time.isoformat(), request_id
            ))
            conn.commit()
        finally:
            conn.close()

    def _export_single_analysis(self, analysis_id: str, export_type: str, settings: Dict) -> str:
        """Export single email analysis result"""
        # Get analysis data
        analysis_data = self._get_analysis_data(analysis_id)
        if not analysis_data:
            raise ReportExportError(f"Analysis {analysis_id} not found")
        
        filename = f"analysis_{analysis_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if export_type == 'json':
            return self._export_json(analysis_data, filename)
        elif export_type == 'pdf':
            return self._export_analysis_pdf(analysis_data, filename, settings)
        elif export_type == 'html':
            return self._export_analysis_html(analysis_data, filename, settings)
        else:
            raise ReportExportError(f"Unsupported export type: {export_type}")

    def _export_batch_results(self, batch_id: str, export_type: str, settings: Dict) -> str:
        """Export batch processing results"""
        # Get batch data
        batch_data = self._get_batch_data(batch_id)
        if not batch_data:
            raise ReportExportError(f"Batch {batch_id} not found")
        
        filename = f"batch_{batch_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if export_type == 'json':
            return self._export_json(batch_data, filename)
        elif export_type == 'pdf':
            return self._export_batch_pdf(batch_data, filename, settings)
        elif export_type == 'csv':
            return self._export_batch_csv(batch_data, filename)
        else:
            raise ReportExportError(f"Unsupported export type: {export_type}")

    def _export_performance_report(self, timeframe: str, export_type: str, settings: Dict) -> str:
        """Export system performance report"""
        # Get performance data
        performance_data = self._get_performance_data(timeframe)
        
        filename = f"performance_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if export_type == 'json':
            return self._export_json(performance_data, filename)
        elif export_type == 'pdf':
            return self._export_performance_pdf(performance_data, filename, settings)
        else:
            raise ReportExportError(f"Unsupported export type: {export_type}")

    def _export_json(self, data: Dict, filename: str) -> str:
        """Export data as JSON"""
        file_path = self.export_dir / f"{filename}.json"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"JSON export completed: {file_path}")
            return str(file_path)
            
        except Exception as e:
            raise ReportExportError(f"JSON export failed: {e}")

    def _export_analysis_pdf(self, data: Dict, filename: str, settings: Dict) -> str:
        """Export single analysis as PDF"""
        if not self.pdf_available:
            raise ReportExportError("PDF generation not available (missing dependencies)")
        
        file_path = self.export_dir / f"{filename}.pdf"
        
        try:
            if REPORTLAB_AVAILABLE:
                return self._create_analysis_pdf_reportlab(data, file_path, settings)
            elif WEASYPRINT_AVAILABLE:
                return self._create_analysis_pdf_weasyprint(data, file_path, settings)
            
        except Exception as e:
            raise ReportExportError(f"PDF export failed: {e}")

    def _create_analysis_pdf_reportlab(self, data: Dict, file_path: Path, settings: Dict) -> str:
        """Create analysis PDF using ReportLab"""
        doc = SimpleDocTemplate(str(file_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            alignment=TA_CENTER,
            spaceAfter=30
        )
        story.append(Paragraph("🛡️ Phishing Analysis Report", title_style))
        story.append(Spacer(1, 12))
        
        # Analysis metadata
        story.append(Paragraph("Analysis Details", styles['Heading2']))
        
        meta_data = [
            ['Analysis ID:', data.get('id', 'N/A')],
            ['Timestamp:', data.get('timestamp', 'N/A')],
            ['Email Hash:', data.get('email_hash', 'N/A')[:20] + '...'],
            ['Processing Time:', f"{data.get('processing_time_ms', 0)}ms"],
        ]
        
        meta_table = Table(meta_data, colWidths=[2*inch, 4*inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 20))
        
        # Rule-based analysis
        if 'rule_analysis' in data:
            story.append(Paragraph("Rule-Based Analysis", styles['Heading2']))
            rule_data = data['rule_analysis']
            
            # Score summary
            score_text = f"<b>Score:</b> {rule_data.get('score', 0)}/100 | <b>Label:</b> {rule_data.get('label', 'Unknown')}"
            story.append(Paragraph(score_text, styles['Normal']))
            story.append(Spacer(1, 10))
            
            # Evidence table
            if 'evidence' in rule_data and rule_data['evidence']:
                evidence_data = [['Rule ID', 'Description', 'Weight']]
                for evidence in rule_data['evidence']:
                    evidence_data.append([
                        evidence.get('id', ''),
                        evidence.get('description', '')[:60] + ('...' if len(evidence.get('description', '')) > 60 else ''),
                        str(evidence.get('weight', 0))
                    ])
                
                evidence_table = Table(evidence_data, colWidths=[1.5*inch, 3.5*inch, 1*inch])
                evidence_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(evidence_table)
            
            story.append(Spacer(1, 20))
        
        # AI analysis
        if 'ai_analysis' in data:
            story.append(Paragraph("AI Analysis", styles['Heading2']))
            ai_data = data['ai_analysis']
            
            score_text = f"<b>Score:</b> {ai_data.get('score', 0)}/100 | <b>Label:</b> {ai_data.get('label', 'Unknown')}"
            story.append(Paragraph(score_text, styles['Normal']))
            
            # Add explanation if available
            if 'explanation' in ai_data:
                story.append(Spacer(1, 10))
                story.append(Paragraph("<b>Explanation:</b>", styles['Normal']))
                story.append(Paragraph(ai_data['explanation'], styles['Normal']))
            
            # Add confidence if available
            if 'confidence_score' in ai_data:
                confidence_text = f"<b>Confidence:</b> {ai_data['confidence_score']:.2%}"
                story.append(Paragraph(confidence_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        logger.info(f"ReportLab PDF created: {file_path}")
        return str(file_path)

    def _get_analysis_data(self, analysis_id: str) -> Optional[Dict]:
        """Get analysis data from database"""
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM email_analysis WHERE id = ?", (analysis_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Parse JSON fields
            data = dict(row)
            if data.get('rule_analysis_json'):
                data['rule_analysis'] = json.loads(data['rule_analysis_json'])
            if data.get('ai_analysis_json'):
                data['ai_analysis'] = json.loads(data['ai_analysis_json'])
                
            return data
            
        finally:
            conn.close()

    def _get_batch_data(self, batch_id: str) -> Optional[Dict]:
        """Get batch processing data"""
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            
            # Get batch job info
            cursor.execute("SELECT * FROM batch_jobs WHERE id = ?", (batch_id,))
            batch_row = cursor.fetchone()
            
            if not batch_row:
                return None
            
            batch_data = dict(batch_row)
            
            # Get individual email results
            cursor.execute("""
                SELECT * FROM batch_job_emails 
                WHERE batch_job_id = ?
                ORDER BY created_at
            """, (batch_id,))
            
            batch_data['emails'] = [dict(row) for row in cursor.fetchall()]
            
            return batch_data
            
        finally:
            conn.close()

    def _get_performance_data(self, timeframe: str) -> Dict:
        """Get performance metrics data"""
        # Parse timeframe (e.g., "24h", "7d", "30d")
        if timeframe.endswith('h'):
            hours = int(timeframe[:-1])
        elif timeframe.endswith('d'):
            hours = int(timeframe[:-1]) * 24
        else:
            hours = 24  # Default to 24 hours
        
        since_time = datetime.now() - timedelta(hours=hours)
        
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM performance_metrics 
                WHERE recorded_at >= ?
                ORDER BY recorded_at DESC
            """, (since_time.isoformat(),))
            
            metrics = [dict(row) for row in cursor.fetchall()]
            
            return {
                'timeframe': timeframe,
                'period_start': since_time.isoformat(),
                'period_end': datetime.now().isoformat(),
                'metrics_count': len(metrics),
                'metrics': metrics
            }
            
        finally:
            conn.close()

    def get_export_status(self, request_id: str) -> Optional[Dict]:
        """Get export request status"""
        return self._get_export_request(request_id)

    def cleanup_expired_exports(self) -> int:
        """Clean up expired export files and requests"""
        cutoff_time = datetime.now() - timedelta(hours=self.max_export_age_hours)
        
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            
            # Get expired exports
            cursor.execute("""
                SELECT id, file_path FROM export_requests
                WHERE expires_at < ? AND file_path IS NOT NULL
            """, (cutoff_time.isoformat(),))
            
            expired_exports = cursor.fetchall()
            cleaned_count = 0
            
            for export in expired_exports:
                # Delete file if it exists
                if export['file_path'] and Path(export['file_path']).exists():
                    try:
                        Path(export['file_path']).unlink()
                        cleaned_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete export file {export['file_path']}: {e}")
            
            # Delete database records
            cursor.execute("""
                DELETE FROM export_requests WHERE expires_at < ?
            """, (cutoff_time.isoformat(),))
            
            conn.commit()
            
            logger.info(f"Cleaned up {cleaned_count} expired export files")
            return cleaned_count
            
        finally:
            conn.close()


# Global export service instance
_export_service = None

def get_export_service() -> ReportExportService:
    """Get global export service instance"""
    global _export_service
    if _export_service is None:
        _export_service = ReportExportService()
    return _export_service

def reset_export_service():
    """Reset global export service (mainly for testing)"""
    global _export_service
    _export_service = None