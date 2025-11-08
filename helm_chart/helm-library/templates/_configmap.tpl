{{/*
ConfigMap template for deployment type
*/}}
{{- define "custom-lib.configmap" -}}
apiVersion: v1
kind: ConfigMap
metadata:
    name: {{ include "custom-lib.fullname" . }}-configmap
    labels:
       app: {{ .Release.Name }}
       release: {{ .Release.Name }}
data:
    myvalue: "Hello World"
    {{if .Values.configmap }}
    {{- toYaml .Values.configmap | nindent 2}}
    {{- end}}
{{- end}}
