"""
Excel Service for Outbound Calls

Manages reading patient data from Excel/CSV and updating call status
"""
from __future__ import annotations

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import re

import pandas as pd
from pydantic import BaseModel, Field, validator


class PatientServiceData(BaseModel):
    """Patient service data from Excel"""
    # Identity
    nombre_paciente: str
    apellido_paciente: str
    tipo_documento: str
    numero_documento: str
    eps: str
    departamento: str
    ciudad: str

    # Contact
    telefono: str
    nombre_familiar: Optional[str] = None
    parentesco: Optional[str] = None

    # Service details
    tipo_servicio: str  # TERAPIA, DIALISIS, CITA_ESPECIALISTA
    tipo_tratamiento: str
    frecuencia: str
    fecha_servicio: str  # Can be comma-separated dates
    hora_servicio: str
    destino_centro_salud: str
    modalidad_transporte: str  # RUTA or DESEMBOLSO

    # Logistics
    zona_recogida: str
    direccion_completa: str

    # Status and notes
    observaciones_especiales: Optional[str] = None
    estado_confirmacion: str = "Pendiente"

    # Internal tracking
    row_index: Optional[int] = None

    @validator('telefono')
    def validate_phone(cls, v):
        """Validate phone number has 10 digits"""
        phone_str = str(v).strip()
        if not phone_str.isdigit() or len(phone_str) != 10:
            raise ValueError(f"Phone number must be 10 digits, got: {v}")
        return phone_str

    @validator('estado_confirmacion', pre=True)
    def validate_status(cls, v):
        """Validate status is valid, default to Pendiente if empty"""
        # Handle NaN, None, empty string
        if v is None or str(v).strip() in ('', 'nan', 'NaN', 'None'):
            return "Pendiente"

        valid_statuses = [
            "Pendiente", "Confirmado", "Reprogramar",
            "Rechazado", "No contesta", "Zona sin cobertura"
        ]
        if v not in valid_statuses:
            # Try case-insensitive match
            for status in valid_statuses:
                if v.lower() == status.lower():
                    return status
            # If still not found, default to Pendiente
            return "Pendiente"
        return v

    @property
    def nombre_completo(self) -> str:
        """Get full patient name"""
        return f"{self.nombre_paciente} {self.apellido_paciente}"

    @property
    def nombre_contacto(self) -> str:
        """Get contact name (familiar or patient)"""
        return self.nombre_familiar if self.nombre_familiar else self.nombre_completo

    def to_dict(self) -> Dict:
        """Convert to dict for use in prompts"""
        return {
            'nombre_completo': self.nombre_completo,
            'nombre_paciente': self.nombre_paciente,
            'apellido_paciente': self.apellido_paciente,
            'nombre_familiar': self.nombre_familiar,
            'parentesco': self.parentesco,
            'tipo_documento': self.tipo_documento,
            'numero_documento': self.numero_documento,
            'eps': self.eps,
            'telefono': self.telefono,
            'ciudad': self.ciudad,
            'tipo_servicio': self.tipo_servicio,
            'tipo_tratamiento': self.tipo_tratamiento,
            'frecuencia': self.frecuencia,
            'fecha_servicio': self.fecha_servicio,
            'hora_servicio': self.hora_servicio,
            'destino_centro_salud': self.destino_centro_salud,
            'modalidad_transporte': self.modalidad_transporte,
            'direccion_completa': self.direccion_completa,
            'observaciones_especiales': self.observaciones_especiales or ''
        }


class ExcelOutboundService:
    """Service for managing outbound call data from Excel"""

    @staticmethod
    def _normalize_phone(value: object) -> str:
        """
        Normalize phone values coming from CSV/pandas.

        Handles common cases like numeric columns (int/float) and stray whitespace.
        """
        phone = str(value).strip()
        phone = re.sub(r"\.0$", "", phone)  # pandas may render integer-like floats as "300...0.0"
        return phone

    def __init__(self, excel_path: str, backup_folder: Optional[str] = None):
        """
        Initialize Excel service

        Args:
            excel_path: Path to the Excel/CSV file
            backup_folder: Path to backup folder (optional)
        """
        self.excel_path = Path(excel_path)
        self.backup_folder = Path(backup_folder) if backup_folder else self.excel_path.parent / "backups"
        self.backup_folder.mkdir(parents=True, exist_ok=True)

        if not self.excel_path.exists():
            raise FileNotFoundError(f"Excel file not found: {excel_path}")

    def create_backup(self) -> str:
        """
        Create backup of current Excel file

        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{self.excel_path.stem}_backup_{timestamp}{self.excel_path.suffix}"
        backup_path = self.backup_folder / backup_name

        shutil.copy2(self.excel_path, backup_path)
        return str(backup_path)

    def load_data(self) -> pd.DataFrame:
        """
        Load data from Excel file

        Returns:
            DataFrame with all data
        """
        try:
            # Auto-detect delimiter (supports both comma and semicolon)
            df = pd.read_csv(self.excel_path, encoding='utf-8', sep=None, engine='python')
            return df
        except Exception as e:
            raise RuntimeError(f"Error loading Excel file: {str(e)}")

    def get_pending_calls(self) -> List[PatientServiceData]:
        """
        Get list of pending calls to make

        Returns:
            List of PatientServiceData for pending calls
        """
        df = self.load_data()

        # Filter for pending status
        pending = df[df['estado_confirmacion'] == 'Pendiente'].copy()

        # Convert to PatientServiceData objects
        result = []
        for idx, row in pending.iterrows():
            try:
                data = PatientServiceData(
                    nombre_paciente=str(row['nombre_paciente']),
                    apellido_paciente=str(row['apellido_paciente']),
                    tipo_documento=str(row['tipo_documento']),
                    numero_documento=str(row['numero_documento']),
                    eps=str(row['eps']),
                    departamento=str(row['departamento']),
                    ciudad=str(row['ciudad']),
                    telefono=str(row['telefono']),
                    nombre_familiar=str(row.get('nombre_familiar')) if pd.notna(row.get('nombre_familiar')) else None,
                    parentesco=str(row.get('parentesco')) if pd.notna(row.get('parentesco')) else None,
                    tipo_servicio=str(row['tipo_servicio']),
                    tipo_tratamiento=row['tipo_tratamiento'],
                    frecuencia=row['frecuencia'],
                    fecha_servicio=row['fecha_servicio'],
                    hora_servicio=row['hora_servicio'],
                    destino_centro_salud=row['destino_centro_salud'],
                    modalidad_transporte=row['modalidad_transporte'],
                    zona_recogida=str(row['zona_recogida']),
                    direccion_completa=str(row['direccion_completa']),
                    observaciones_especiales=str(row.get('observaciones_especiales')) if pd.notna(row.get('observaciones_especiales')) else None,
                    estado_confirmacion=str(row['estado_confirmacion']),
                    row_index=idx
                )
                result.append(data)
            except Exception as e:
                print(f"Warning: Skipping row {idx} due to validation error: {str(e)}")
                continue

        return result

    def update_call_status(
        self,
        row_index: int,
        new_status: str,
        observations: Optional[str] = None
    ) -> bool:
        """
        Update call status in Excel file

        Args:
            row_index: Index of the row to update
            new_status: New status (Confirmado, Reprogramar, etc.)
            observations: Additional observations to append

        Returns:
            True if successful
        """
        try:
            # Create backup before modifying
            self.create_backup()

            # Load current data
            df = self.load_data()

            # Update status
            df.loc[row_index, 'estado_confirmacion'] = new_status

            # Append observations if provided
            if observations:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                obs_entry = f"[{timestamp}] {observations}"

                current_obs = df.loc[row_index, 'observaciones_especiales']
                if pd.isna(current_obs) or current_obs == '':
                    df.loc[row_index, 'observaciones_especiales'] = obs_entry
                else:
                    df.loc[row_index, 'observaciones_especiales'] = f"{current_obs} | {obs_entry}"

            # Save back to file
            df.to_csv(self.excel_path, index=False, encoding='utf-8')

            return True
        except Exception as e:
            print(f"ERROR: Error updating call status: {str(e)}")
            return False

    def get_patient_by_phone(self, phone: str) -> Optional[PatientServiceData]:
        """
        Get patient data by phone number

        Args:
            phone: Phone number to search

        Returns:
            PatientServiceData if found, None otherwise
        """
        df = self.load_data()
        phone_norm = self._normalize_phone(phone)
        phone_series = df['telefono'].map(self._normalize_phone)
        matches = df[phone_series == phone_norm]

        if len(matches) == 0:
            return None

        if len(matches) > 1:
            print(f"Warning: Multiple patients found with phone {phone}, returning first")

        row = matches.iloc[0]
        idx = matches.index[0]

        try:
            return PatientServiceData(
                nombre_paciente=str(row['nombre_paciente']),
                apellido_paciente=str(row['apellido_paciente']),
                tipo_documento=str(row['tipo_documento']),
                numero_documento=str(row['numero_documento']),
                eps=str(row['eps']),
                departamento=str(row['departamento']),
                ciudad=str(row['ciudad']),
                telefono=str(row['telefono']),
                nombre_familiar=str(row.get('nombre_familiar')) if pd.notna(row.get('nombre_familiar')) else None,
                parentesco=str(row.get('parentesco')) if pd.notna(row.get('parentesco')) else None,
                tipo_servicio=str(row['tipo_servicio']),
                tipo_tratamiento=row['tipo_tratamiento'],
                frecuencia=row['frecuencia'],
                fecha_servicio=row['fecha_servicio'],
                hora_servicio=row['hora_servicio'],
                destino_centro_salud=row['destino_centro_salud'],
                modalidad_transporte=row['modalidad_transporte'],
                zona_recogida=str(row['zona_recogida']),
                direccion_completa=str(row['direccion_completa']),
                observaciones_especiales=str(row.get('observaciones_especiales')) if pd.notna(row.get('observaciones_especiales')) else None,
                estado_confirmacion=str(row['estado_confirmacion']),
                row_index=idx
            )
        except Exception as e:
            print(f"ERROR: Error parsing patient data: {str(e)}")
            return None

    def get_statistics(self) -> Dict:
        """
        Get statistics about calls

        Returns:
            Dict with statistics
        """
        df = self.load_data()

        return {
            'total': len(df),
            'pendiente': len(df[df['estado_confirmacion'] == 'Pendiente']),
            'confirmado': len(df[df['estado_confirmacion'] == 'Confirmado']),
            'reprogramar': len(df[df['estado_confirmacion'] == 'Reprogramar']),
            'rechazado': len(df[df['estado_confirmacion'] == 'Rechazado']),
            'no_contesta': len(df[df['estado_confirmacion'] == 'No contesta']),
            'zona_sin_cobertura': len(df[df['estado_confirmacion'] == 'Zona sin cobertura']),
            'by_service_type': df['tipo_servicio'].value_counts().to_dict(),
            'by_modality': df['modalidad_transporte'].value_counts().to_dict()
        }
