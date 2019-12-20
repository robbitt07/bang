from . import models

from rest_framework import serializers


class DAGProcessStatusSerializer(serializers.ModelSerializer):
    observed_time = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S")
    
    class Meta:
        model = models.DAGProcessStatus
        fields = (
            'pk', 
            'dag_process', 
            'pid_running', 
            'memory_consumption', 
            'cpu_consumption', 
            'child_processes', 
            'observed_time',
        )
