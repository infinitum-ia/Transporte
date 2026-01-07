"""
Sistema de Procesamiento de Llamadas Salientes
Lee el archivo Excel con datos de pacientes y gestiona las llamadas de confirmación
"""

import pandas as pd
import os
from datetime import datetime, timedelta
import time
import shutil

# Configuración
ARCHIVO_DATOS = "datos_llamadas_salientes.csv"
RUTA_COMPLETA = r"C:\Users\Administrador\Documents\Transporte\datos_llamadas_salientes.csv"
BACKUP_FOLDER = r"C:\Users\Administrador\Documents\Transporte\backups"


class ProcesadorLlamadasSalientes:
    def __init__(self, archivo_path):
        self.archivo_path = archivo_path
        self.df = None
        self.registros_procesados = 0
        self.registros_confirmados = 0
        self.registros_fallidos = 0

    def crear_backup(self):
        """Crea backup del archivo antes de modificarlo"""
        if not os.path.exists(BACKUP_FOLDER):
            os.makedirs(BACKUP_FOLDER)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"datos_backup_{timestamp}.csv"
        backup_path = os.path.join(BACKUP_FOLDER, backup_filename)

        shutil.copy2(self.archivo_path, backup_path)
        print(f"✅ Backup creado: {backup_filename}")

    def cargar_datos(self):
        """Carga los datos del archivo CSV"""
        try:
            self.df = pd.read_csv(self.archivo_path, encoding='utf-8')
            print(f"✅ Archivo cargado: {len(self.df)} registros totales")
            return True
        except Exception as e:
            print(f"❌ Error al cargar archivo: {str(e)}")
            return False

    def filtrar_pendientes(self):
        """Filtra solo los registros pendientes de confirmar"""
        pendientes = self.df[self.df['estado_confirmacion'] == 'Pendiente'].copy()
        print(f"📋 Registros pendientes: {len(pendientes)}")
        return pendientes

    def validar_telefono(self, telefono):
        """Valida que el teléfono tenga 10 dígitos"""
        telefono_str = str(telefono).strip()
        if len(telefono_str) == 10 and telefono_str.isdigit():
            return True
        return False

    def validar_fecha_futura(self, fecha_str):
        """Valida que la fecha del servicio sea futura"""
        try:
            # Puede contener múltiples fechas separadas por coma
            fechas = fecha_str.split(',')
            primera_fecha = fechas[0].strip()
            fecha_servicio = datetime.strptime(primera_fecha, "%d/%m/%Y")

            if fecha_servicio.date() >= datetime.now().date():
                return True
            return False
        except:
            return False

    def obtener_datos_paciente(self, row):
        """Extrae y estructura los datos del paciente para la llamada"""
        datos = {
            'nombre_completo': f"{row['nombre_paciente']} {row['apellido_paciente']}",
            'nombre_paciente': row['nombre_paciente'],
            'apellido_paciente': row['apellido_paciente'],
            'tipo_documento': row['tipo_documento'],
            'numero_documento': row['numero_documento'],
            'eps': row['eps'],
            'telefono': row['telefono'],
            'ciudad': row['ciudad'],
            'departamento': row['departamento'],

            # Datos del familiar (si existe)
            'nombre_familiar': row.get('nombre_familiar', ''),
            'parentesco': row.get('parentesco', ''),

            # Datos del servicio
            'tipo_servicio': row['tipo_servicio'],
            'tipo_tratamiento': row['tipo_tratamiento'],
            'frecuencia': row['frecuencia'],
            'fecha_servicio': row['fecha_servicio'],
            'hora_servicio': row['hora_servicio'],
            'destino_centro_salud': row['destino_centro_salud'],
            'modalidad_transporte': row['modalidad_transporte'],
            'direccion_completa': row['direccion_completa'],

            # Observaciones especiales
            'observaciones_especiales': row.get('observaciones_especiales', ''),

            # Índice para actualizar después
            'index': row.name
        }
        return datos

    def generar_script_llamada(self, datos):
        """Genera el script personalizado para la llamada según los datos del paciente"""

        # Determinar si es familiar o paciente directo
        contacto = datos['nombre_familiar'] if datos['nombre_familiar'] else datos['nombre_completo']

        script = []

        # 1. Identificación
        script.append(f"Habla con [NOMBRE_AGENTE_IA] de Transformas, empresa de transporte autorizada por la EPS {datos['eps']}.")
        script.append(f"¿Me confirma, por favor, su nombre?")
        script.append("# [ESPERAR RESPUESTA - debe coincidir con contacto esperado]")
        script.append("")

        # 2. Aviso de grabación
        script.append("Le indico que la llamada está siendo grabada y monitoreada.")
        script.append("")

        # 3. Información del servicio según tipo
        if datos['tipo_servicio'] == 'Diálisis':
            script.append(f"Mi llamada es para coordinar los servicios de diálisis {datos['frecuencia']} "
                         f"a las {datos['hora_servicio']} en {datos['destino_centro_salud']}.")
        elif datos['tipo_servicio'] == 'Terapia':
            script.append(f"El paciente {datos['nombre_completo']} tiene programado servicio de transporte "
                         f"para {datos['tipo_tratamiento']} el/los día(s) {datos['fecha_servicio']} "
                         f"a las {datos['hora_servicio']} hacia {datos['destino_centro_salud']}.")
        else:  # Cita con especialista
            script.append(f"El paciente {datos['nombre_completo']} tiene una cita programada "
                         f"para el {datos['fecha_servicio']} a las {datos['hora_servicio']} "
                         f"en {datos['destino_centro_salud']}.")

        script.append("¿Confirma la asistencia?")
        script.append("# [ESPERAR RESPUESTA]")
        script.append("")

        # 4. Modalidad de transporte
        if datos['modalidad_transporte'] == 'Ruta':
            script.append(f"El servicio le queda coordinado por medio de ruta. "
                         f"Debe estar listo a las {datos['hora_servicio']} y atento a la llamada del conductor.")
        else:  # Desembolso
            script.append("El servicio le queda coordinado por medio de desembolso.")
            script.append("Me confirma, por favor, su número de documento.")
            script.append("# [ESPERAR DOCUMENTO]")
            script.append("Se va a acercar a Efecty en el transcurso de 24 a 48 horas "
                         "para realizar el retiro con el documento y el código de retiro.")
        script.append("")

        # 5. Observaciones especiales
        if datos['observaciones_especiales'] and datos['observaciones_especiales'] != '':
            if 'silla de ruedas' in datos['observaciones_especiales'].lower() or 'carro grande' in datos['observaciones_especiales'].lower():
                script.append("Tengo registrado que el paciente requiere un vehículo grande por silla de ruedas. "
                             "Esta observación está en el sistema y se validará con el coordinador antes de asignar el vehículo.")
            elif 'zona sin cobertura' in datos['observaciones_especiales'].lower():
                script.append(f"El servicio de ruta opera únicamente interno {datos['ciudad']}. "
                             f"Debe acercarse a su EPS para que autoricen el servicio desde su ubicación.")
            else:
                script.append(f"Nota: {datos['observaciones_especiales']}")
            script.append("")

        # 6. Preguntas del usuario
        script.append("¿Tiene alguna pregunta o inquietud sobre el servicio?")
        script.append("# [ESPERAR Y RESPONDER SEGÚN CASOS ESPECIALES - Ver sección 4 de especificación]")
        script.append("")

        # 7. Cierre
        script.append("Le confirmo que el servicio queda coordinado. ¿Le puedo ayudar en algo más?")
        script.append("# [SI NO HAY MÁS PREGUNTAS]")
        script.append(f"Gracias por su tiempo. El servicio queda confirmado. Que tenga un excelente día.")

        return "\n".join(script)

    def realizar_llamada(self, datos):
        """
        Simula la realización de la llamada
        En producción, aquí se integraría con la API de telefonía (Twilio, etc.)
        """
        print("\n" + "="*80)
        print(f"📞 INICIANDO LLAMADA")
        print(f"Paciente: {datos['nombre_completo']}")
        print(f"Teléfono: {datos['telefono']}")
        print(f"Servicio: {datos['tipo_servicio']} - {datos['fecha_servicio']}")
        print("="*80)

        # Generar y mostrar script
        script = self.generar_script_llamada(datos)
        print("\n📄 SCRIPT DE LA LLAMADA:")
        print("-" * 80)
        print(script)
        print("-" * 80)

        # Simulación: En producción esto sería reemplazado por la integración real
        print("\n⏳ Ejecutando llamada...")
        time.sleep(2)  # Simular duración de llamada

        # Simular resultado (en producción vendría de la conversación real)
        # Aquí podrías integrar con reconocimiento de voz, etc.
        resultado = {
            'estado': 'Confirmado',  # Confirmado, Reprogramar, Rechazado, No contesta, Zona sin cobertura
            'observaciones': 'Paciente confirmó asistencia. Sin novedades.'
        }

        print(f"✅ Llamada completada - Estado: {resultado['estado']}")
        print(f"📝 Observaciones: {resultado['observaciones']}")

        return resultado

    def actualizar_registro(self, index, resultado):
        """Actualiza el registro en el DataFrame con el resultado de la llamada"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Actualizar estado
        self.df.loc[index, 'estado_confirmacion'] = resultado['estado']

        # Agregar observaciones (sin borrar las anteriores)
        obs_anteriores = self.df.loc[index, 'observaciones_especiales']
        obs_anteriores = '' if pd.isna(obs_anteriores) else str(obs_anteriores)

        nueva_obs = f"[{timestamp}] Llamada realizada - {resultado['observaciones']}"

        if obs_anteriores:
            self.df.loc[index, 'observaciones_especiales'] = f"{obs_anteriores} | {nueva_obs}"
        else:
            self.df.loc[index, 'observaciones_especiales'] = nueva_obs

    def guardar_cambios(self):
        """Guarda los cambios en el archivo CSV"""
        try:
            self.df.to_csv(self.archivo_path, index=False, encoding='utf-8')
            print("💾 Cambios guardados en el archivo")
            return True
        except Exception as e:
            print(f"❌ Error al guardar: {str(e)}")
            return False

    def procesar_llamadas(self):
        """Proceso principal: procesa todas las llamadas pendientes"""
        print("\n" + "="*80)
        print("🚀 INICIANDO PROCESAMIENTO DE LLAMADAS SALIENTES")
        print("="*80 + "\n")

        # 1. Crear backup
        self.crear_backup()

        # 2. Cargar datos
        if not self.cargar_datos():
            return

        # 3. Filtrar pendientes
        pendientes = self.filtrar_pendientes()

        if len(pendientes) == 0:
            print("✅ No hay llamadas pendientes por realizar")
            return

        # 4. Procesar cada registro
        for idx, row in pendientes.iterrows():
            self.registros_procesados += 1

            print(f"\n📊 Procesando registro {self.registros_procesados}/{len(pendientes)}")

            # Validaciones
            if not self.validar_telefono(row['telefono']):
                print(f"⚠️  Teléfono inválido: {row['telefono']} - SALTANDO")
                continue

            if not self.validar_fecha_futura(row['fecha_servicio']):
                print(f"⚠️  Fecha del servicio ya pasó: {row['fecha_servicio']} - SALTANDO")
                continue

            # Obtener datos del paciente
            datos = self.obtener_datos_paciente(row)

            # Realizar llamada
            resultado = self.realizar_llamada(datos)

            # Actualizar registro
            self.actualizar_registro(idx, resultado)

            # Guardar cambios inmediatamente
            self.guardar_cambios()

            if resultado['estado'] == 'Confirmado':
                self.registros_confirmados += 1
            else:
                self.registros_fallidos += 1

            # Esperar antes del siguiente registro
            if self.registros_procesados < len(pendientes):
                print("\n⏸️  Esperando 10 segundos antes de la siguiente llamada...")
                time.sleep(10)

        # 5. Reporte final
        self.generar_reporte()

    def generar_reporte(self):
        """Genera reporte final del procesamiento"""
        print("\n" + "="*80)
        print("📊 REPORTE FINAL")
        print("="*80)
        print(f"Total procesados: {self.registros_procesados}")
        print(f"✅ Confirmados: {self.registros_confirmados}")
        print(f"⚠️  Otros estados: {self.registros_fallidos}")
        print(f"Tasa de éxito: {(self.registros_confirmados/self.registros_procesados*100):.1f}%" if self.registros_procesados > 0 else "0%")
        print("="*80 + "\n")


def main():
    """Función principal"""
    procesador = ProcesadorLlamadasSalientes(RUTA_COMPLETA)
    procesador.procesar_llamadas()


if __name__ == "__main__":
    main()
