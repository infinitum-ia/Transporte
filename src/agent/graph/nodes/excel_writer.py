# Excel writer node
from typing import Dict, Any

def excel_writer(state: Dict[str, Any]) -> Dict[str, Any]:
    """Write results to Excel (simplified)"""
    # For now, just log that we would write
    # In Fase 5, this will write to actual Excel
    excel_row = state.get('excel_row_index')
    if excel_row is not None:
        print(f"Would write to Excel row {excel_row}")
    
    # Mark as completed
    state['excel_written'] = True
    
    return state
