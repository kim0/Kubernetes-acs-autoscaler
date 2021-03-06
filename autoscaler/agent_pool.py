from azure.cli.core.util import get_file_json
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.mgmt.resource.resources import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
import logging
import autoscaler.utils as utils


logger = logging.getLogger(__name__)

class AgentPool(object):

    def __init__(self, pool_name, nodes):
        self.name = pool_name
        self.nodes = nodes
        self.unschedulable_nodes = list(filter(lambda n: n.unschedulable, self.nodes))

        
       
        self.max_size = 100
      
    @property
    def actual_capacity(self):
        return len(self.nodes)
    
    @property
    def unit_capacity(self):
        #Within a pool, every node should have the same capacity
        return self.nodes[0].capacity
    
    @property
    def instance_type(self):
        #TODO: when running on acs-engine, we could infer the instance type from the ARM template
        #that would allow having pools with 0 nodes
        return self.nodes[0].instance_type
    
    def reclaim_unschedulable_nodes(self, new_desired_capacity):
        """
        Try to get the number of schedulable nodes up if we don't have enough before scaling
        """
        desired_capacity = min(self.max_size, new_desired_capacity)
        num_unschedulable = len(self.unschedulable_nodes)
        num_schedulable = self.actual_capacity - num_unschedulable
     
        if num_schedulable < desired_capacity:
            for node in self.unschedulable_nodes:
                if node.uncordon():
                    num_schedulable += 1
                    # Uncordon only what we need
                    if num_schedulable == desired_capacity:
                        break    
    