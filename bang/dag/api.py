from dag.models import DAGProcessStatus
from dag.serializers import DAGProcessStatusSerializer
from rest_framework.response import Response
from rest_framework.views import APIView


class DAGProcessStatusListView(APIView):

    def get(self, request, format=None):
        dag_process = self.request.query_params.get('dag_process', None)
        if dag_process is not None:
            qs = DAGProcessStatus.objects.filter(dag_process_id=dag_process)
        else:
            qs = DAGProcessStatus.objects.all()
        serializer = DAGProcessStatusSerializer(qs, many=True)
        return Response(serializer.data)
