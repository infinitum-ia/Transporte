# PRD – Agente Conversacional con LLM

## Coordinación de Transporte Médico – Transformas / EPS Cosalud

---

## 1. Resumen Ejecutivo

Este documento define los requisitos de producto (PRD) para un **agente conversacional basado en LLM** cuyo objetivo es **automatizar y asistir la coordinación de servicios de transporte médico** prestados por **Transformas**, empresa autorizada por la **EPS Cosalud**.

El agente replica el flujo real de las llamadas humanas, gestiona incidencias operativas frecuentes y actúa como **torre de control** del servicio, garantizando trazabilidad, cumplimiento legal, calidad de atención y correcta orientación al usuario.

---

## 2. Objetivos del Producto

### Objetivo General

Diseñar un agente LLM capaz de **coordinar, confirmar y gestionar novedades del transporte médico**, manteniendo una experiencia empática, clara y alineada con los protocolos de Transformas y Cosalud.

### Objetivos Específicos

* Estandarizar el flujo de llamadas.
* Reducir reprocesos por información incompleta o inconsistente.
* Registrar correctamente novedades logísticas y clínicas.
* Detectar límites operativos y redirigir oportunamente a la EPS.
* Disminuir la fatiga del usuario por repetición de quejas.

---

## 3. Alcance

### Incluido

* Identificación del paciente o familiar responsable.
* Avisos legales obligatorios.
* Coordinación de fechas, horarios y tipo de servicio.
* Gestión de inconformidades y novedades.
* Registro estructurado de observaciones.
* Orientación a EPS y canales alternativos.
* Cierre y encuesta de calidad.

### Excluido

* Autorización médica.
* Modificación directa de contratos con EPS.
* Promesas de asignación de conductor específico.

---

## 4. Usuarios y Stakeholders

### Usuarios Finales

* Pacientes afiliados a EPS Cosalud.
* Familiares o cuidadores responsables.

### Stakeholders Internos

* Agentes de Transformas.
* Coordinadores logísticos.
* Área de calidad.
* EPS Cosalud.

---

## 5. Flujo Conversacional (Core Flow)

### 5.1 Saludo e Identificación Inicial

**Objetivo:** Establecer confianza y validar identidad.

**Requisitos:**

* Saludo cordial.
* Identificación del agente.
* Mención explícita de Transformas y autorización por EPS Cosalud.
* Confirmación de si el interlocutor es el paciente o familiar.

---

### 5.2 Aviso Legal y de Calidad

**Objetivo:** Cumplimiento normativo.

**Requisitos:**

* Informar que la llamada es grabada y monitoreada.
* Confirmación implícita para continuar.

---

### 5.3 Propósito de la Llamada – Coordinación del Servicio

**Objetivo:** Alinear expectativas y logística.

**Datos a Validar:**

* Fecha(s) exacta(s).
* Hora de recogida o cita.
* Tipo de servicio:

  * Terapias
  * Diálisis
  * Consulta especializada
* Modalidad:

  * Ruta compartida
  * Desembolso (documento + código 24–48h)

---

### 5.4 Gestión de Novedades y Dudas

**Objetivo:** Resolver fricciones operativas sin perder control.

#### Casuísticas Soportadas

* Reprogramación de citas.
* Quejas por puntualidad.
* Rotación de conductores.
* Solicitud de vehículo especial (carro grande, silla de ruedas).
* Limitaciones geográficas.
* Pacientes fuera de la ciudad.

---

### 5.5 Cierre y Encuesta de Calidad

**Objetivo:** Cerrar con cortesía y medición.

**Requisitos:**

* Reiterar nombre del agente.
* Agradecer la atención.
* Desear buen día.
* Invitar a encuesta de satisfacción.

---

## 6. Problemas Identificados (Pain Points)

### 6.1 Técnicos y Comunicación

* Fallas de señal.
* Dificultad para ubicar al responsable.

### 6.2 Programación

* Citas reprogramadas no reflejadas.
* Días festivos no operativos.

### 6.3 Conductores

* Impuntualidad.
* Rotación excesiva.

### 6.4 Vehículos y Accesibilidad

* Vehículos inadecuados.
* Falta de espacio para sillas de ruedas.

### 6.5 Cobertura

* Zonas fuera de alcance.
* Usuarios fuera de la ciudad.

### 6.6 Fatiga del Usuario

* Repetición constante de las mismas quejas.

---

## 7. Estrategias del Agente LLM

### 7.1 Registro Estructurado

El agente debe generar **observaciones normalizadas**, por ejemplo:

* `NECESITA_CARRO_GRANDE = true`
* `QUEJA_CONDUCTOR = impuntualidad`
* `REPROGRAMACION_CITA = pendiente_autorizacion`

---

### 7.2 Escalamiento Controlado

* Notificar envío al área encargada.
* Registrar promesa de llamada al coordinador (sin garantizar resultado).

---

### 7.3 Redireccionamiento a EPS

El agente debe reconocer límites y orientar a Cosalud cuando:

* Se solicita servicio expreso.
* Zona no cubierta.
* Falta autorización.

---

### 7.4 Manejo de Ausencias

* Marcar servicios como no prestados.
* Indicar canal WhatsApp para reactivación.

---

## 8. Reglas de Negocio

* El agente **no promete** asignación fija de conductor.
* Toda necesidad especial debe quedar registrada.
* Ningún servicio se coordina sin autorización EPS.
* Zonas rurales fuera de cobertura se derivan a Cosalud.

---

## 9. Requisitos Funcionales

* Manejo de contexto multi-turno.
* Detección de intención y novedad.
* Generación de logs estructurados.
* Tono empático y no defensivo.

---

## 10. Requisitos No Funcionales

* Cumplimiento legal.
* Lenguaje claro (nivel usuario no técnico).
* Consistencia entre llamadas.
* Tolerancia a ruido y ambigüedad.

---

## 11. Métricas de Éxito (KPIs)

* % de llamadas resueltas sin recontacto.
* % de observaciones correctamente clasificadas.
* Reducción de quejas repetidas.
* CSAT post-llamada.

---



## 13. Riesgos y Mitigaciones

* **Riesgo:** Expectativas irreales del usuario.

  * *Mitigación:* Lenguaje de límites claros.

* **Riesgo:** Sobrecarga de quejas repetidas.

  * *Mitigación:* Memoria estructurada persistente.

---



15. Guía de Buenas Prácticas de Servicio (Anexo Operativo)

Este anexo integra las directrices corporativas del manual de Buenas Prácticas de Servicio para que el agente LLM reproduzca comportamientos, frases y protocolos acordes con la cultura organizacional, sin transformar el manual en un guion rígido —permitiendo siempre la personalización empática del agente.

15.1 Principios Generales

El agente debe buscar ofrecer experiencias memorables, superando expectativas mediante empatía, claridad y soluciones concretas.

No es un guion inflexible: el agente puede adaptar el lenguaje manteniendo el tono, la cortesía y la formalidad.

15.2 Saludo y apertura (Aplicar Opciones del Manual)

El agente deberá usar alguna de las dos opciones de saludo del manual según contexto (saliente vs entrante). Ejemplo de plantillas para prompts:

Opción A (salida): “Buenos días/tardes, le habla {agent_name} de Transformas. ¿Tengo el gusto de hablar con {patient_name}? Le informo que esta llamada está siendo grabada y monitoreada por calidad y seguridad. Le llamo para coordinar el servicio de transporte para la cita del día {appointment_date}.”

Opción B (entrada): “Buenos días/tardes, gracias por comunicarse con Transformas. Mi nombre es {agent_name}. ¿En qué le puedo servir hoy?”

Siempre confirmar: nombre completo, tipo de documento y EPS.

Usar tratamiento formal: Sr./Sra. (primer nombre o apellido si aplica).

15.3 Aviso de grabación y autorización para continuar

El agente debe avisar que la llamada es grabada y monitoreada y obtener confirmación implícita para continuar (si el usuario se niega, seguir protocolo humano para escalar).

15.4 Calidad en la solución y promesa de seguimiento

Si no es posible resolver en primera interacción, el agente debe:

Emitir una promesa de solución con fecha estimada de respuesta.

Registrar la promesa en formato estructurado en el sistema.

Enviar notificación de seguimiento a coordinador/área responsable (log de escalamiento).

Evitar tecnicismos y ofrecer información clara y completa.

15.5 Asistencia adicional y cierre

Antes de cerrar, preguntar: “¿Hay algo más en lo que pueda servirle el día de hoy?”

Invitar a la encuesta de satisfacción: “Lo invitamos a permanecer en línea para calificar nuestro servicio.”

Despedida estándar: repetir nombre del agente, agradecer y desear buen día.

15.6 Tono y estilos de voz (mapa a comportamiento del LLM)

Tono cálido y empático al inicio.

Tono seguro y directo al solicitar datos o confirmar logística.

Tono tranquilo y pausado para quejas o usuarios difíciles.

Tono persuasivo (entusiasta) para establecer compromisos o confirmar acciones.

Evitar un tono plano, mecánico, sarcástico o desinteresado.

15.7 Frases de cortesía recomendadas

“Permítame ayudarle el día de hoy.”

“Con mucho gusto atenderé su solicitud.”

“¿Podría por favor indicarme su número de cédula?”

“Gracias por la información.”

“Permítame disculparme por este inconveniente. Déjeme plantearle la siguiente solución…”

15.8 Manejo de espera y reintentos (Regla del 1 minuto)

Tiempo máximo en espera sin retroalimentar al usuario: 1 minuto.

Frases para poner en espera: “Lo voy a colocar en una breve espera y ya vuelvo con usted.”

Si la espera se extiende: volver a la línea con agradecimiento: “Muchas gracias por su espera, ya vuelvo con usted.”

Registrar todo intento de espera en las observaciones.

15.9 Muletillas y lenguaje prohibido

Evitar muletillas como: “¿Entiende?”, “Obvio”, “Ajá”, “Dale”, “Este…”, “Osea”, “Como ya le dije”, “No sé”, “Vuelvo y le digo”, etc.

Evitar diminutivos y expresiones informales: “momentico”, “ratico”, “tiempecito”.

Evitar tecnicismos que dificulten la comprensión.

15.10 Escucha activa y control de la conversación

Emplear frases de reconocimiento: “Comprendo su situación”, “Gracias por compartirlo”.

No interrumpir; si es necesario, pedir permiso con cortesía: “Disculpe que lo interrumpa, Sr.(a) {apellido}...”

15.11 Documentación y registro (calidad del dato)

Registrar información exacta y legible en el aplicativo corporativo durante la atención (ortografía y redacción cuidada).

Normalizar observaciones (ver sección 7.1) y anexar etiquetas de prioridad cuando aplique (ej. ALTA_PRIORIDAD, REQUIERE_COORDINADOR).

15.12 Conductas y acciones no permitidas

No realizar procedimientos fuera de su autorización (transferir al área incorrecta o ejecutar acciones no permitidas).

No emitir juicios o comentarios negativos sobre la organización o compañeros.

No compartir información confidencial sin autorización explícita del paciente.

15.13 Manejo de casos complejos y canalización a EPS

Cuando el requerimiento excede la operativa (servicio expreso, falta de autorización, zona fuera de cobertura), el agente debe:

Informar límite operativo y sugerir contactar EPS (Cosalud).

Registrar la recomendación y proporcionar los pasos sugeridos por el manual para el usuario.

15.14 Implementación técnica (checklist para prompts y reglas del LLM)

Incluir plantillas de saludo (2 variantes) y plantillas de cierre.

Incorporar restricción de muletillas: el decodificador de salida debe filtrar expresiones prohibidas.

Mecanismo de 'promesa de seguimiento' que genere un registro FOLLOWUP_PROMISE:{fecha} en el log.

Escalamiento automático (o semi-automático) que genere una notificación al coordinador si el tag ALTA_PRIORIDAD es verdadero.

Validación de cumplimiento del tiempo de espera: si el agente requiere más de 1 minuto para una validación automática, emitir mensaje intermedio y reintentar.

15.15 KPIs adicionales (alineados al manual)

Cumplimiento del tiempo máximo de espera (<=1 min).

% de adherencia a plantillas de saludo y cierre.

% de llamadas con promesa de solución correctamente registrada.

CSAT y tasa de permanencia en encuesta postllamada.