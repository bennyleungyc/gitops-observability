{{/*
Service template for deployment type
*/}}
{{- define "custom-lib.service" -}}
apiVersion: v1
kind: Service
metadata:
  name: {{ include "custom-lib.fullname" . }}
  labels:
    {{- include "custom-lib.labels" . | nindent 4 }}
spec:
  type: {{ .Values.service.type }}
  selector:
    {{- include "custom-lib.selectorLabels" . | nindent 4 }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: {{ .Values.service.targetPort }}
      protocol: TCP
      name: http
{{- end}}