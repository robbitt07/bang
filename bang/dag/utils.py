import datetime
from hashlib import sha1
import pytz
import time


class DAGItemLogger(object):
	def __init__(self, dag_item_id):
		from dag.models import DAGItem, DAGItemLogging, LoggingEvent
		self.dag_item_id = dag_item_id
		self.dag_item = DAGItem.objects.get(pk=self.dag_item_id)
		self.LoggingEvent = LoggingEvent
		self.run_hash = sha1("{}{}".format(self.dag_item_id, time.time()).encode('utf-8')).hexdigest()
		self.dag_item_logging = DAGItemLogging.objects.create(dag_item=self.dag_item
																,run_hash=self.run_hash
																,start_time=pytz.utc.localize(datetime.datetime.utcnow()))

	def add(self, log_metric, log_value):
		self.LoggingEvent.objects.create(dag_item_logging=self.dag_item_logging
											,log_metric=log_metric
											,log_value=log_value)
	
	def finish(self):
		self.dag_item_logging.end_time = pytz.utc.localize(datetime.datetime.utcnow())
		self.dag_item_logging.save()
