{{/*
Expand the name of the chart.
*/}}
{{- define "calculaud-be.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "calculaud-be.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "calculaud-be.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "calculaud-be.labels" -}}
helm.sh/chart: {{ include "calculaud-be.chart" . }}
{{ include "calculaud-be.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "calculaud-be.selectorLabels" -}}
app.kubernetes.io/name: {{ include "calculaud-be.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "calculaud-be.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "calculaud-be.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
PostgreSQL host
*/}}
{{- define "calculaud-be.postgresql.host" -}}
{{- if .Values.postgresql.enabled }}
{{- printf "%s-postgresql" (include "calculaud-be.fullname" .) }}
{{- else }}
{{- .Values.postgresql.external.host }}
{{- end }}
{{- end }}

{{/*
PostgreSQL port
*/}}
{{- define "calculaud-be.postgresql.port" -}}
{{- if .Values.postgresql.enabled }}
{{- .Values.postgresql.port | default 5432 }}
{{- else }}
{{- .Values.postgresql.external.port | default 5432 }}
{{- end }}
{{- end }}

{{/*
PostgreSQL database name
*/}}
{{- define "calculaud-be.postgresql.database" -}}
{{- if .Values.postgresql.enabled }}
{{- .Values.postgresql.database | default "calculaud" }}
{{- else }}
{{- .Values.postgresql.external.database }}
{{- end }}
{{- end }}

{{/*
PostgreSQL username
*/}}
{{- define "calculaud-be.postgresql.username" -}}
{{- if .Values.postgresql.enabled }}
{{- .Values.postgresql.username | default "calculaud" }}
{{- else }}
{{- .Values.postgresql.external.username }}
{{- end }}
{{- end }}

{{/*
Database URL
*/}}
{{- define "calculaud-be.databaseUrl" -}}
{{- printf "postgresql://%s:%s@%s:%s/%s" (include "calculaud-be.postgresql.username" .) "$(DATABASE_PASSWORD)" (include "calculaud-be.postgresql.host" .) (include "calculaud-be.postgresql.port" .) (include "calculaud-be.postgresql.database" .) }}
{{- end }}

{{/*
Create image name
*/}}
{{- define "calculaud-be.image" -}}
{{- printf "%s:%s" .Values.image.repository (.Values.image.tag | default .Chart.AppVersion) }}
{{- end }}