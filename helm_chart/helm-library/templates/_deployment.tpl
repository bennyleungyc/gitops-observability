{{/*
Deployment template for deployment kind
*/}}
{{- define "custom-lib.deployment" -}}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "custom-lib.fullname" . }}
  labels:
    {{- include "custom-lib.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  strategy:
    {{- toYaml .Values.strategy | nindent 4 }}
  selector:
    matchLabels:
      {{- include "custom-lib.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "custom-lib.selectorLabels" . | nindent 8 }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      containers:
        - name: {{ .Release.Name }}
          image: {{ .Values.image.repository }}:{{ .Values.image.tag | default "latest" }}
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: {{ .Values.service.targetPort }}
              protocol: TCP
          {{- if .Values.livenessProbe.enabled }}
          livenessProbe:
            httpGet:
              path: {{ .Values.livenessProbe.path }}
              port: {{ .Values.livenessProbe.port }}
            initialDelaySeconds: {{ .Values.livenessProbe.initialDelaySeconds }}
            periodSeconds: {{ .Values.livenessProbe.periodSeconds }}
            timeoutSeconds: {{ .Values.livenessProbe.timeoutSeconds }}
            successThreshold: {{ .Values.livenessProbe.successThreshold }}
            failureThreshold: {{ .Values.livenessProbe.failureThreshold }}
          {{- end }}
          {{- if .Values.readinessProbe.enabled }}
          readinessProbe:
            httpGet:
              path: {{ .Values.readinessProbe.path }}
              port: {{ .Values.readinessProbe.port }}
            initialDelaySeconds: {{ .Values.readinessProbe.initialDelaySeconds }}
            periodSeconds: {{ .Values.readinessProbe.periodSeconds }}
            timeoutSeconds: {{ .Values.readinessProbe.timeoutSeconds }}
            successThreshold: {{ .Values.readinessProbe.successThreshold }}
            failureThreshold: {{ .Values.readinessProbe.failureThreshold }}
          {{- end }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
      nodeSelector:
        {{- toYaml .Values.nodeSelector | nindent 8 }}
      tolerations:
        {{- toYaml .Values.tolerations | nindent 8 }}
      affinity:
        {{- toYaml .Values.affinity | nindent 8 }}
{{- end}}