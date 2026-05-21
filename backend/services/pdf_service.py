"""
PDF Service - Generate PDF reports (wellness evaluations, invoices, etc.)
Uses ReportLab for PDF generation.

Migration Path: PDF generation is operational logic, no encryption needed.
"""
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class PDFService:
    """PDF generation service using ReportLab"""

    def _extract_report_data(self, evaluation, distributor):
        """Extract all necessary data into a dict to avoid lazy loading in threads"""
        return {
            'evaluation_id': evaluation.id,
            'distributor_name': distributor.name,
            'created_at': evaluation.created_at,
            'age': evaluation.age,
            'gender': evaluation.gender,
            'height_cm': evaluation.height_cm,
            'weight_kg': evaluation.weight_kg,
            'bmi': evaluation.bmi,
            'bmi_category': evaluation.get_bmi_category(),
            'activity_level': evaluation.activity_level,
            'exercise_frequency': evaluation.exercise_frequency,
            'meals_per_day': evaluation.meals_per_day,
            'water_intake_liters': evaluation.water_intake_liters,
            'sleep_hours': evaluation.sleep_hours,
            'sleep_quality': evaluation.sleep_quality,
            'primary_goal': evaluation.primary_goal,
            'target_weight_kg': evaluation.target_weight_kg,
            'motivation': evaluation.motivation,
            'diagnosis': evaluation.diagnosis,
            'recommendations': evaluation.recommendations,
            'recommended_products': evaluation.recommended_products,
            'language': getattr(evaluation, 'language', None) or distributor.language or 'es'
        }

    def _generate_pdf_from_data(self, data, output_dir):
        """Worker function to generate PDF from dictionary data"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib.colors import HexColor
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

            lang = data.get('language', 'es')
            
            # Localized Strings
            I18N = {
                'es': {
                    'title': '🌿 Evaluación de Bienestar',
                    'distributor': 'Distribuidor',
                    'date': 'Fecha',
                    'personal_data': '📋 Datos Personales',
                    'age': 'Edad',
                    'gender': 'Género',
                    'height': 'Altura (cm)',
                    'weight': 'Peso (kg)',
                    'bmi': 'IMC',
                    'lifestyle': '🏃 Estilo de Vida',
                    'activity_level': 'Nivel de actividad',
                    'exercise_freq': 'Frecuencia de ejercicio',
                    'meals_per_day': 'Comidas por día',
                    'water_intake': 'Agua (litros/día)',
                    'sleep_hours': 'Horas de sueño',
                    'sleep_quality': 'Calidad de sueño',
                    'goals': '🎯 Metas',
                    'primary_goal': 'Objetivo principal',
                    'target_weight': 'Peso objetivo',
                    'motivation': 'Motivación',
                    'no_specified': 'No especificado',
                    'diagnosis': '🔍 Diagnóstico AI',
                    'recommendations': '💡 Recomendaciones',
                    'products': '🛒 Productos Recomendados',
                    'footer': 'Generado por la plataforma de',
                    'activity_map': {
                        'sedentary': 'Sedentario',
                        'light': 'Ligero',
                        'moderate': 'Moderado',
                        'active': 'Activo',
                        'very_active': 'Muy Activo'
                    },
                    'sleep_map': {
                        'excellent': 'Excelente',
                        'good': 'Buena',
                        'fair': 'Regular',
                        'poor': 'Mala'
                    }
                },
                'en': {
                    'title': '🌿 Wellness Evaluation',
                    'distributor': 'Distributor',
                    'date': 'Date',
                    'personal_data': '📋 Personal Data',
                    'age': 'Age',
                    'gender': 'Gender',
                    'height': 'Height (cm)',
                    'weight': 'Weight (kg)',
                    'bmi': 'BMI',
                    'lifestyle': '🏃 Lifestyle',
                    'activity_level': 'Activity Level',
                    'exercise_freq': 'Exercise Frequency',
                    'meals_per_day': 'Meals per Day',
                    'water_intake': 'Water (liters/day)',
                    'sleep_hours': 'Sleep Hours',
                    'sleep_quality': 'Sleep Quality',
                    'goals': '🎯 Goals',
                    'primary_goal': 'Primary Goal',
                    'target_weight': 'Target Weight',
                    'motivation': 'Motivation',
                    'no_specified': 'Not specified',
                    'diagnosis': '🔍 AI Diagnosis',
                    'recommendations': '💡 Recommendations',
                    'products': '🛒 Recommended Products',
                    'footer': 'Generated by the platform of',
                    'activity_map': {
                        'sedentary': 'Sedentary',
                        'light': 'Light',
                        'moderate': 'Moderate',
                        'active': 'Active',
                        'very_active': 'Very Active'
                    },
                    'sleep_map': {
                        'excellent': 'Excellent',
                        'good': 'Good',
                        'fair': 'Fair',
                        'poor': 'Poor'
                    }
                },
                'pt': {
                    'title': '🌿 Avaliação de Bem-estar',
                    'distributor': 'Distribuidor',
                    'date': 'Data',
                    'personal_data': '📋 Dados Pessoais',
                    'age': 'Idade',
                    'gender': 'Gênero',
                    'height': 'Altura (cm)',
                    'weight': 'Peso (kg)',
                    'bmi': 'IMC',
                    'lifestyle': '🏃 Estilo de Vida',
                    'activity_level': 'Nível de atividade',
                    'exercise_freq': 'Frequência de exercício',
                    'meals_per_day': 'Refeições por dia',
                    'water_intake': 'Água (litros/dia)',
                    'sleep_hours': 'Horas de sono',
                    'sleep_quality': 'Qualidade do sono',
                    'goals': '🎯 Metas',
                    'primary_goal': 'Objetivo principal',
                    'target_weight': 'Peso ideal',
                    'motivation': 'Motivação',
                    'no_specified': 'Não especificado',
                    'diagnosis': '🔍 Diagnóstico de IA',
                    'recommendations': '💡 Recomendações',
                    'products': '🛒 Produtos Recomendados',
                    'footer': 'Gerado pela plataforma de',
                    'activity_map': {
                        'sedentary': 'Sedentário',
                        'light': 'Leve',
                        'moderate': 'Moderado',
                        'active': 'Ativo',
                        'very_active': 'Muito Ativo'
                    },
                    'sleep_map': {
                        'excellent': 'Excelente',
                        'good': 'Boa',
                        'fair': 'Regular',
                        'poor': 'Ruim'
                    }
                }
            }

            texts = I18N.get(lang, I18N['es'])

            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)

            # Generate filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"wellness_report_{data['evaluation_id']}_{timestamp}.pdf"
            filepath = os.path.join(output_dir, filename)

            # Create PDF
            doc = SimpleDocTemplate(filepath, pagesize=letter,
                                    topMargin=0.5 * inch, bottomMargin=0.5 * inch)
            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=HexColor('#2E7D32'),
                spaceAfter=20,
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=HexColor('#1B5E20'),
                spaceBefore=15,
                spaceAfter=10,
            )
            body_style = styles['Normal']

            elements = []

            # Title
            elements.append(Paragraph(texts['title'], title_style))
            elements.append(Paragraph(f"{texts['distributor']}: {data['distributor_name']}", body_style))
            elements.append(Paragraph(
                f"{texts['date']}: {data['created_at'].strftime('%d/%m/%Y') if data['created_at'] else 'N/A'}",
                body_style
            ))
            elements.append(Spacer(1, 20))

            # Personal Data
            elements.append(Paragraph(texts['personal_data'], heading_style))
            personal_data = [
                [texts['age'], str(data['age'] or 'N/A')],
                [texts['gender'], data['gender'] or 'N/A'],
                [texts['height'], str(data['height_cm'] or 'N/A')],
                [texts['weight'], str(data['weight_kg'] or 'N/A')],
                [texts['bmi'], f"{data['bmi'] or 'N/A'} ({data['bmi_category'] or ''})"],
            ]
            table = Table(personal_data, colWidths=[200, 300])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), HexColor('#E8F5E9')),
                ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#333333')),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 15))

            # Lifestyle
            elements.append(Paragraph(texts['lifestyle'], heading_style))
            
            activity_map = texts['activity_map']
            sleep_map = texts['sleep_map']
            
            lifestyle_data = [
                [texts['activity_level'], activity_map.get(data['activity_level'], data['activity_level'] or 'N/A')],
                [texts['exercise_freq'], data['exercise_frequency'] or 'N/A'],
                [texts['meals_per_day'], str(data['meals_per_day'] or 'N/A')],
                [texts['water_intake'], str(data['water_intake_liters'] or 'N/A')],
                [texts['sleep_hours'], str(data['sleep_hours'] or 'N/A')],
                [texts['sleep_quality'], sleep_map.get(data['sleep_quality'], data['sleep_quality'] or 'N/A')],
            ]
            table2 = Table(lifestyle_data, colWidths=[200, 300])
            table2.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), HexColor('#E8F5E9')),
                ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#333333')),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
            ]))
            elements.append(table2)
            elements.append(Spacer(1, 15))

            # Goals
            elements.append(Paragraph(texts['goals'], heading_style))
            elements.append(Paragraph(
                f"<b>{texts['primary_goal']}:</b> {data['primary_goal'] or texts['no_specified']}",
                body_style
            ))
            if data['target_weight_kg']:
                elements.append(Paragraph(
                    f"<b>{texts['target_weight']}:</b> {data['target_weight_kg']} kg", body_style
                ))
            if data['motivation']:
                elements.append(Paragraph(
                    f"<b>{texts['motivation']}:</b> {data['motivation']}", body_style
                ))
            elements.append(Spacer(1, 15))

            # Diagnosis (if AI-generated)
            if data['diagnosis']:
                elements.append(Paragraph(texts['diagnosis'], heading_style))
                elements.append(Paragraph(data['diagnosis'], body_style))
                elements.append(Spacer(1, 15))
            
            # Recommendations (if AI-generated)
            if data['recommendations']:
                elements.append(Paragraph(texts['recommendations'], heading_style))
                elements.append(Paragraph(data['recommendations'], body_style))
                elements.append(Spacer(1, 15))

            # Recommended Products
            if data['recommended_products']:
                elements.append(Paragraph(texts['products'], heading_style))
                for product in data['recommended_products']:
                    if isinstance(product, str):
                        elements.append(Paragraph(f"• {product}", body_style))
                    elif isinstance(product, dict):
                        elements.append(Paragraph(
                            f"• {product.get('name', 'Producto')}: {product.get('reason', '')}",
                            body_style
                        ))

            # Footer
            elements.append(Spacer(1, 30))
            footer_style = ParagraphStyle(
                'Footer', parent=body_style, fontSize=8,
                textColor=HexColor('#999999')
            )
            elements.append(Paragraph(
                f"{texts['footer']} {data['distributor_name']} | {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC",
                footer_style
            ))

            doc.build(elements)
            logger.info(f"Wellness PDF generated: {filepath}")
            return filepath

        except ImportError:
            logger.error("reportlab package not installed")
            return None
        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            return None

    def generate_wellness_report(self, evaluation, distributor, output_dir='uploads/reports'):
        """
        Generate a PDF wellness evaluation report (Synchronous).

        Args:
            evaluation: WellnessEvaluation model instance
            distributor: Distributor model instance
            output_dir: directory to save the PDF

        Returns:
            str: path to generated PDF
        """
        data = self._extract_report_data(evaluation, distributor)
        return self._generate_pdf_from_data(data, output_dir)

    def generate_wellness_report_async(self, evaluation, distributor, output_dir='uploads/reports'):
        """
        Generate a PDF wellness evaluation report (Asynchronous via Celery).
        Extracts data before dispatching to avoid lazy-loading issues.

        Args:
            evaluation: WellnessEvaluation model instance
            distributor: Distributor model instance
            output_dir: directory to save the PDF
        """
        data = self._extract_report_data(evaluation, distributor)
        try:
            from tasks import generate_pdf_report
            generate_pdf_report.delay(
                distributor_id=distributor.id,
                report_type='wellness',
                data=data
            )
            logger.info(f"PDF generation dispatched to Celery for eval {evaluation.id}")
        except Exception as e:
            logger.warning(f"Celery dispatch failed ({e}), falling back to sync generation")
            return self._generate_pdf_from_data(data, output_dir)


# Singleton instance
pdf_service = PDFService()
