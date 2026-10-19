{{/*
Nombre base del release. Usa .Values.nombre si viene definido (nombre
lógico del componente Solventa); si no, cae al nombre del chart.
*/}}
{{- define "microservicio.name" -}}
{{- default .Chart.Name .Values.nombre | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Nombre completo del recurso (release + nombre), truncado a 63 caracteres
por el límite de nombres de Kubernetes (DNS-1123).
*/}}
{{- define "microservicio.fullname" -}}
{{- $name := default .Chart.Name .Values.nombre -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/*
Nombre y versión del chart, usado en la label app.kubernetes.io/version.
*/}}
{{- define "microservicio.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Labels comunes de Solventa: además de las labels estándar de
app.kubernetes.io, se incluye solventa.io/scaling-group para poder filtrar
o inspeccionar por grupo de escalado con kubectl (kubectl get pods -l
solventa.io/scaling-group=a).
*/}}
{{- define "microservicio.labels" -}}
helm.sh/chart: {{ include "microservicio.chart" . }}
{{ include "microservicio.selectorLabels" . }}
app.kubernetes.io/version: {{ .Values.imagen.tag | default .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
solventa.io/scaling-group: {{ .Values.grupoEscalado | quote }}
{{- end -}}

{{/*
Selector labels: deben mantenerse estables entre upgrades (no incluyen
version ni chart) porque son inmutables en Deployment.spec.selector.
*/}}
{{- define "microservicio.selectorLabels" -}}
app.kubernetes.io/name: {{ include "microservicio.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Nombre del ServiceAccount a usar por los pods: el definido explícitamente
en values, o el nombre completo del release si no se define ninguno,
cuando serviceAccount.crear=true. Si crear=false, se usa "default".
*/}}
{{- define "microservicio.serviceAccountName" -}}
{{- if .Values.serviceAccount.crear -}}
{{- default (include "microservicio.fullname" .) .Values.serviceAccount.nombre -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.nombre -}}
{{- end -}}
{{- end -}}
