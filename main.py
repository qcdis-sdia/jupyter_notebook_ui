# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import os

from methods import *
from widgets import *

topology_names = []
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    index = 0
    node_templates = {}

    k8s_interface = get_template(
        'https://raw.githubusercontent.com/qcdis-sdia/sdia-tosca/develop/templates/k8s_interface.yaml')
    k8_requirements = []
    workflows = {}

    for topology in topologies_boxes:
        index += 1

        topology_info = get_topology_info(topology.children, index)
        topology_names.append(topology_info['name'])

        topology_properties = {'domain': translate_domain(topology_info['Cloud_Provider'],
                                                          topology_info['Topology_Domain']),
                               'provider': topology_info['Cloud_Provider']}
        topology_requirements = []
        instances = {}

    for i in range(topology_info['Num._Of_VMs']):
        vm_info = get_vm_info(tpl_info=topology_info, i=i, topology_properties=topology_properties)
        node_templates.update(
            build_node_template(node_name=vm_info['name'], node_type=vm_info['type'], properties=vm_info['properties'],
                                interfaces=vm_info['interfaces']))
        vm_req = {'vm': {'capability': 'tosca.capabilities.QC.VM', 'node': vm_info['name'],
                         'relationship': 'tosca.relationships.DependsOn'}}
        topology_requirements.append(vm_req)
        instance_props = get_instance_properties(vm_info['name'])
        instances[vm_info['name']] = instance_props
        k8s_interface.update(build_k8s_inventory(interface=k8s_interface, count=i, info=vm_info))

    azure_topology_interface = get_azure_topology_interface(instances, topology_info=topology_info)

    azure_workflows = get_azure_workflows(topology_info=topology_info)
    workflows.update(azure_workflows)

    node_templates.update(
        build_node_template(node_name=topology_info['name'], node_type='tosca.nodes.QC.VM.topology',
                            properties=topology_properties, requirements=topology_requirements,
                            interfaces=azure_topology_interface))
    k8_requirement = {'host': {'capability': 'tosca.capabilities.QC.VM.topology', 'node': topology_info['name'],
                               'relationship': 'tosca.relationships.HostedOn'}}
    k8_requirements.append(k8_requirement)

    k8s_workflows = get_k8s_workflows(topology_names, enable_monitoring_widget.value, app_name_widget.value,topology_info=topology_info)
    workflows.update(k8s_workflows)

    vm_master_name = 'compute_' + str(0) + '_' + topology_info['name']
    credential_properties = {'credential': {'get_attribute': [vm_master_name, 'user_key_pair']}}
    ks8s_node = build_node_template(node_name='kubernetes', node_type='tosca.nodes.QC.docker.Orchestrator.Kubernetes',
                                    properties=credential_properties, requirements=k8_requirements,
                                    interfaces=k8s_interface)
    node_templates.update(ks8s_node)

    if enable_monitoring_widget.value:
        helm_monitoring_info = get_helm_monitoring_info(vm_master_name=vm_master_name)
        node_templates.update(build_node_template(node_name=helm_monitoring_info['name'],
                                                  node_type='tosca.nodes.QC.Container.Application.Helm',
                                                  properties=credential_properties,
                                                  requirements=helm_monitoring_info['requirements'],
                                                  interfaces=helm_monitoring_info['interfaces']))

    helm_app_info = get_helm_app_info(helm_app_chart_name_widget.value, helm_app_repo_name_widget.value,
                                      helm_app_repo_url_widget.value, app_name_widget.value, helm_app_values.value,vm_master_name=vm_master_name)

    node_templates.update(build_node_template(node_name=helm_app_info['name'],
                                              node_type='tosca.nodes.QC.Container.Application.Helm',
                                              properties=credential_properties,
                                              requirements=helm_app_info['requirements'],
                                              interfaces=helm_app_info['interfaces']))

    topology_template = {'node_templates': node_templates, 'workflows': workflows}
    tosca = {'tosca_definitions_version': 'tosca_simple_yaml_1_2'}
    imports = [{'nodes': 'https://raw.githubusercontent.com/qcdis-sdia/sdia-tosca/master/types/nodes.yaml',
                'data': 'https://raw.githubusercontent.com/qcdis-sdia/sdia-tosca/master/types/data.yml',
                'capabilities': 'https://raw.githubusercontent.com/qcdis-sdia/sdia-tosca/master/types/capabilities.yaml',
                'policies': 'https://raw.githubusercontent.com/qcdis-sdia/sdia-tosca/master/types/policies.yaml',
                'interfaces': 'https://raw.githubusercontent.com/qcdis-sdia/sdia-tosca/master/types/interfaces.yml'}]
    tosca['imports'] = imports
    repositories = {'docker_hub': 'https://hub.docker.com/'}
    tosca['repositories'] = repositories
    tosca['topology_template'] = topology_template


    class NoAliasDumper(yaml.Dumper):
        def ignore_aliases(self, data):
            return True


    filePath = 'generated_tosca.yaml'
    if os.path.exists(filePath):
        os.remove(filePath)

    with open(filePath, 'w') as file:
        yaml.dump(tosca, file, default_flow_style=False, Dumper=NoAliasDumper)
