"""
Endpoints para métricas detalladas del CSV de reportes.
Solo accesible por administradores.
"""

import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, status, Depends
from pydantic import BaseModel

from api.routes.auth import get_current_admin

router = APIRouter(prefix="/metrics", tags=["Metrics"])
class MetricsReportResponse(BaseModel):
    """Respuesta con métricas agregadas del reporte CSV."""
    total_interactions: int
    date_range: Dict[str, Optional[str]]
    averages: Dict[str, float]
    totals: Dict[str, float]
    by_date: List[Dict[str, Any]]


def read_metrics_csv() -> List[Dict[str, Any]]:
    """Lee el archivo CSV de métricas y retorna una lista de diccionarios."""
    csv_path = Path("metrics/ia_metrics_report.csv")
    
    if not csv_path.exists():
        return []
    
    metrics = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    row['latency_ms'] = float(row.get('latency_ms', 0))
                    row['input_tokens'] = int(row.get('input_tokens', 0))
                    row['output_tokens'] = int(row.get('output_tokens', 0))
                    row['total_tokens'] = int(row.get('total_tokens', 0))
                    row['estimated_cost_usd'] = float(row.get('estimated_cost_usd', 0))
                    row['num_retrieved_docs'] = int(row.get('num_retrieved_docs', 0))
                    row['context_size'] = int(row.get('context_size', 0))
                    row['avg_similarity_score'] = float(row.get('avg_similarity_score', 0))
                    row['citations_total'] = int(row.get('citations_total', 0))
                    row['citations_valid'] = int(row.get('citations_valid', 0))
                    row['citation_validity_ratio'] = float(row.get('citation_validity_ratio', 0))
                    row['hallucination_rate'] = float(row.get('hallucination_rate', 0))
                except (ValueError, KeyError):
                    continue
                
                metrics.append(row)
    except Exception as e:
        print(f"Error leyendo CSV: {e}")
        return []
    
    return metrics


@router.get(
    "/report",
    response_model=MetricsReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Métricas detalladas del reporte CSV (Admin)",
    description="Obtiene métricas agregadas y estadísticas del archivo CSV de reportes. Requiere rol de administrador."
)
async def get_metrics_report(_admin = Depends(get_current_admin)):
    """
    Lee el CSV de métricas y retorna estadísticas agregadas.
    
    Returns:
        MetricsReportResponse: Métricas agregadas del reporte
    """
    metrics = read_metrics_csv()
    
    if not metrics:
        return MetricsReportResponse(
            total_interactions=0,
            date_range={"start": None, "end": None},
            averages={},
            totals={},
            by_date=[]
        )
    
    # Calcular totales
    total_interactions = len(metrics)
    total_cost = sum(m.get('estimated_cost_usd', 0) for m in metrics)
    total_tokens = sum(m.get('total_tokens', 0) for m in metrics)
    total_input_tokens = sum(m.get('input_tokens', 0) for m in metrics)
    total_output_tokens = sum(m.get('output_tokens', 0) for m in metrics)
    total_citations = sum(m.get('citations_total', 0) for m in metrics)
    total_valid_citations = sum(m.get('citations_valid', 0) for m in metrics)
    
    # Calcular promedios
    avg_latency = sum(m.get('latency_ms', 0) for m in metrics) / total_interactions if total_interactions > 0 else 0
    avg_tokens = total_tokens / total_interactions if total_interactions > 0 else 0
    avg_cost = total_cost / total_interactions if total_interactions > 0 else 0
    avg_docs_retrieved = sum(m.get('num_retrieved_docs', 0) for m in metrics) / total_interactions if total_interactions > 0 else 0
    avg_similarity = sum(m.get('avg_similarity_score', 0) for m in metrics) / total_interactions if total_interactions > 0 else 0
    avg_citation_validity = sum(m.get('citation_validity_ratio', 0) for m in metrics) / total_interactions if total_interactions > 0 else 0
    avg_hallucination = sum(m.get('hallucination_rate', 0) for m in metrics) / total_interactions if total_interactions > 0 else 0
    
    # Rango de fechas
    timestamps = [m.get('timestamp', '') for m in metrics if m.get('timestamp')]
    date_range = {
        "start": min(timestamps) if timestamps else None,
        "end": max(timestamps) if timestamps else None
    }
    
    # Agrupar por fecha (solo fecha, sin hora)
    by_date_dict = {}
    for m in metrics:
        timestamp = m.get('timestamp', '')
        if timestamp:
            # Extraer solo la fecha (YYYY-MM-DD)
            date_key = timestamp.split(' ')[0] if ' ' in timestamp else timestamp[:10]
            if date_key not in by_date_dict:
                by_date_dict[date_key] = {
                    'date': date_key,
                    'count': 0,
                    'avg_latency': 0,
                    'total_cost': 0,
                    'total_tokens': 0
                }
            
            by_date_dict[date_key]['count'] += 1
            by_date_dict[date_key]['avg_latency'] += m.get('latency_ms', 0)
            by_date_dict[date_key]['total_cost'] += m.get('estimated_cost_usd', 0)
            by_date_dict[date_key]['total_tokens'] += m.get('total_tokens', 0)
    
    # Calcular promedios por fecha
    by_date = []
    for date_key, data in sorted(by_date_dict.items()):
        count = data['count']
        by_date.append({
            'date': date_key,
            'count': count,
            'avg_latency': round(data['avg_latency'] / count, 2) if count > 0 else 0,
            'total_cost': round(data['total_cost'], 6),
            'total_tokens': data['total_tokens']
        })
    
    return MetricsReportResponse(
        total_interactions=total_interactions,
        date_range=date_range,
        averages={
            "latency_ms": round(avg_latency, 2),
            "tokens": round(avg_tokens, 2),
            "cost_usd": round(avg_cost, 6),
            "docs_retrieved": round(avg_docs_retrieved, 2),
            "similarity_score": round(avg_similarity, 4),
            "citation_validity": round(avg_citation_validity, 4),
            "hallucination_rate": round(avg_hallucination, 4)
        },
        totals={
            "cost_usd": round(total_cost, 6),
            "tokens": total_tokens,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "citations": total_citations,
            "valid_citations": total_valid_citations
        },
        by_date=by_date
    )

