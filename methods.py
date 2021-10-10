import json
import os
import requests
import urllib3
import yaml


def build_node_template(node_name=None, node_type=None, properties=None, requirements=None, interfaces=None):
    node_template = {node_name: {'properties': properties, 'requirements': requirements, 'interfaces': interfaces,
                                 'type': node_type}}
    return node_template


def translate_domain(cloud_provider, domain_name):
    if cloud_provider == 'Azure':
        return domain_name.lower().replace(' ', '')


def translate_vm_size(cloud_provider, vm_size):
    vm_specs = {}
    if vm_size == 'small':
        vm_specs['num_cores'] = '1'
        vm_specs['mem_size'] = '2048 MB'
        vm_specs['disk_size'] = '10000 MB'
    elif vm_size == 'medium':
        vm_specs['num_cores'] = '2'
        vm_specs['mem_size'] = '4048 MB'
        vm_specs['disk_size'] = '20000 MB'
    elif vm_size == 'large':
        vm_specs['num_cores'] = '4'
        vm_specs['mem_size'] = '8048 MB'
        vm_specs['disk_size'] = '40000 MB'
    elif vm_size == 'large_mem':
        vm_specs['num_cores'] = '4'
        vm_specs['mem_size'] = '256000 MB'
        vm_specs['disk_size'] = '40000 MB'
    return vm_specs


def replace_all(d, dict_value, value):
    for k, v in d.items():
        if isinstance(v, dict):
            replace_all(v, dict_value, value)
        else:
            if v == dict_value:
                v = value
            if isinstance(v, list):
                v = [value if i == dict_value else i for i in v]


def translate_vm_size(cloud_provider, vm_size):
    vm_specs = {}
    if vm_size == 'small':
        vm_specs['num_cores'] = '1'
        vm_specs['mem_size'] = '2048 MB'
        vm_specs['disk_size'] = '10000 MB'
    elif vm_size == 'medium':
        vm_specs['num_cores'] = '2'
        vm_specs['mem_size'] = '4048 MB'
        vm_specs['disk_size'] = '20000 MB'
    elif vm_size == 'large':
        vm_specs['num_cores'] = '4'
        vm_specs['mem_size'] = '8048 MB'
        vm_specs['disk_size'] = '40000 MB'
    elif vm_size == 'large_mem':
        vm_specs['num_cores'] = '4'
        vm_specs['mem_size'] = '256000 MB'
        vm_specs['disk_size'] = '40000 MB'
    return vm_specs


def get_template(url):
    r = requests.get(url)
    with open('interface.yaml', 'wb') as f:
        f.write(r.content)

    with open('interface.yaml') as f:
        interface = yaml.safe_load(f)
    return interface


def get_topology_info(topology_widget_children, topology_num):
    info = {'name': 'topology_' + str(topology_num)}

    for child in topology_widget_children:
        info[child.description.replace(':', '').replace(' ', '_')] = child.value
    return info


def get_vm_info(tpl_info=None, i=None, topology_properties=None):
    vm_name = 'compute_' + str(i) + '_' + tpl_info['name']
    role = 'master'
    assign_public_ip = 'yes'
    if i > 0:
        role = 'worker'
        assign_public_ip = 'no'
    vm_properties = {'os_distro': 'Ubuntu', 'os_version': '18.04', 'user_name': 'vm_user', 'role': role,
                     'assign_public_ip': assign_public_ip}
    vm_properties.update(translate_vm_size(topology_properties['provider'], tpl_info['VM_size']))
    vm_interfaces = {'Standard': {'create': 'dumy.yaml'}}

    info = {'name': vm_name, 'properties': vm_properties, 'interfaces': vm_interfaces,
            'type': 'tosca.nodes.QC.VM.Compute'}
    return info


def get_instance_properties(vm_name):
    props = {}
    for prop_name in ['user_name', 'user_name', 'os_version', 'disk_size', 'mem_size', 'num_cores', 'os_distro',
                      'role', 'assign_public_ip']:
        props[prop_name] = {'get_property': [vm_name, prop_name]}
    return props


def build_k8s_inventory(interface=None, count=None, info=None):
    for interface_action_name in interface['Kubernetes']:
        inv = \
            interface['Kubernetes'][interface_action_name]['inputs']['inventory']['all']['children']['cluster'][
                'children']
        props = {'ansible_host': {'get_attribute': [info['name'], 'public_ip']},
                 'ansible_python_interpreter': '/usr/bin/python3',
                 'ansible_ssh_user': {'get_property': [info['name'], 'user_name']}}
        if count <= 0:
            if not inv['master']['hosts']['m_0']:
                inv['master']['hosts']['m_0'] = props
            else:
                inv['master']['hosts']['m_0'].update(props)

        elif 'worker' in inv:
            host = {'w_' + str(count): props}
            if not inv['worker']['hosts']:
                inv['worker']['hosts'] = host
            else:
                inv['worker']['hosts'].update(host)
        interface['Kubernetes'][interface_action_name]['inputs']['inventory']['all']['children']['cluster'][
            'children'].update(inv)
    return interface


def get_azure_topology_interface(input_instances, topology_info):
    azure_remote_topology_interface = get_template(
        'https://raw.githubusercontent.com/qcdis-sdia/sdia-tosca/develop/templates/azure_topology_interface.yaml')
    azure_remote_topology_interface = yaml.safe_load(
        yaml.dump(azure_remote_topology_interface).replace('TOPOLOGY_NAME', topology_info['name']))
    for interface_action_name in azure_remote_topology_interface['Azure']:
        if 'instances' in \
                azure_remote_topology_interface['Azure'][interface_action_name]['inputs']['inventory']['all']['hosts'][
                    'localhost']:
            azure_remote_topology_interface['Azure'][interface_action_name]['inputs']['inventory']['all']['hosts'][
                'localhost']['instances'] = input_instances
    return azure_remote_topology_interface


def get_azure_workflows(topology_info):
    wfs = {}
    az_workflows = get_template(
        'https://raw.githubusercontent.com/qcdis-sdia/sdia-tosca/develop/templates/azure_prov_workflow.yaml')

    az_workflows = yaml.safe_load(
        yaml.dump(az_workflows).replace('TOPOLOGY_NAME', topology_info['name']))

    for workflow_name in az_workflows:
        for step_name in az_workflows[workflow_name]['steps']:
            az_workflows[workflow_name]['steps'][step_name]['target'] = topology_info['name']
        if 'preconditions' in az_workflows[workflow_name]:
            for preconditions in az_workflows[workflow_name]['preconditions']:
                preconditions['target'] = topology_info['name']
        wf = {workflow_name + '_' + topology_info['name']: az_workflows[workflow_name]}
        wfs.update(wf)
    return wfs


def get_k8s_workflows(input_topology_names, monitoring, helm_app_name, topology_info=None):
    if monitoring:
        k8s_remote_workflows = get_template(
            'https://raw.githubusercontent.com/qcdis-sdia/sdia-tosca/develop/templates/k8s_workflow_heml_monitoring'
            '.yaml')
    else:
        k8s_remote_workflows = get_template(
            'https://raw.githubusercontent.com/qcdis-sdia/sdia-tosca/develop/templates/k8s_workflow.yaml')

    k8s_remote_workflows = yaml.safe_load(
        yaml.dump(k8s_remote_workflows).replace('KUBERNETES_NAME', 'kubernetes').replace('HELM_NAME', helm_app_name))

    k8s_remote_workflows = yaml.safe_load(
        yaml.dump(k8s_remote_workflows).replace('TOPOLOGY_NAME', topology_info['name']))

    topology_preconditions = []

    for topology_name in input_topology_names:
        precondition = {'condition': [{'assert': [{'current_state': [{'equal': 'RUNNING'}]}]}], 'target': topology_name}
        topology_preconditions.append(precondition)

    return k8s_remote_workflows


def parse_helm_values(helm_values):
    str_dict = '{\"'
    for item in helm_values.split("."):
        if '=' not in item:
            str_dict += item + '\":{'
        if '=' in item:
            str_dict += '\"' + item.split("=")[0] + '\":\"' + item.split("=")[1] + '\"}}'
    return json.loads(str_dict)


def get_helm_monitoring_info(vm_master_name=None):
    monitoring_info = {}
    helm_req = {'kubernetes': {'capability': 'tosca.capabilities.QC.Kubernetes', 'node': 'kubernetes',
                               'relationship': 'tosca.relationships.HostedOn'}}
    helm_requirements = [helm_req]
    monitoring_info['requirements'] = helm_requirements

    monitoring_interface = get_template(
        'https://raw.githubusercontent.com/qcdis-sdia/sdia-tosca/develop/templates/helm_interface.yaml')

    ansible_vars = {'ansible_host': {'get_attribute': [vm_master_name, 'public_ip']},
                    'ansible_python_interpreter': '/usr/bin/python3',
                    'ansible_ssh_user': {'get_property': [vm_master_name, 'user_name']}}

    for interface_action_name in monitoring_interface['Helm']:
        monitoring_interface['Helm'][interface_action_name]['inputs']['inventory']['all']['hosts'][
            'master'] = ansible_vars

    monitoring_interface['Helm']['install_chart']['inputs']['extra_variables'][
        'chart_name'] = 'prometheus-community/kube-prometheus-stack'
    monitoring_interface['Helm']['install_chart']['inputs']['extra_variables']['repo_name'] = 'prometheus-community'
    monitoring_interface['Helm']['install_chart']['inputs']['extra_variables'][
        'repo_url'] = 'https://prometheus-community.github.io/helm-charts'
    monitoring_interface['Helm']['install_chart']['inputs']['extra_variables']['helm_name'] = 'monitoring'
    monitoring_interface['Helm']['install_chart']['inputs']['extra_variables']['values'] = {
        'grafana': {'service': {'type': 'NodePort'}}}

    monitoring_info['interfaces'] = monitoring_interface

    monitoring_info['name'] = 'monitoring'
    return monitoring_info


def get_helm_app_info(chart_name, repo_name, repo_url, app_name, helm_application_values, vm_master_name=None):
    helm_application_info = {}
    helm_interface = get_template(
        'https://raw.githubusercontent.com/qcdis-sdia/sdia-tosca/develop/templates/helm_interface.yaml')
    helm_interface['Helm']['install_chart']['inputs']['extra_variables'][
        'chart_name'] = chart_name
    helm_interface['Helm']['install_chart']['inputs']['extra_variables']['repo_name'] = repo_name
    helm_interface['Helm']['install_chart']['inputs']['extra_variables']['repo_url'] = repo_url
    helm_interface['Helm']['install_chart']['inputs']['extra_variables']['helm_name'] = app_name

    ansible_vars = {'ansible_host': {'get_attribute': [vm_master_name, 'public_ip']},
                    'ansible_python_interpreter': '/usr/bin/python3',
                    'ansible_ssh_user': {'get_property': [vm_master_name, 'user_name']}}

    for interface_action_name in helm_interface['Helm']:
        if not helm_interface['Helm'][interface_action_name]['inputs']['inventory']['all']['hosts']['master']:
            helm_interface['Helm'][interface_action_name]['inputs']['inventory']['all']['hosts'][
                'master'] = ansible_vars
        else:
            helm_interface['Helm'][interface_action_name]['inputs']['inventory']['all']['hosts'][
                'master'].update(ansible_vars)

    helm_req = {'kubernetes': {'capability': 'tosca.capabilities.QC.Kubernetes', 'node': 'kubernetes',
                               'relationship': 'tosca.relationships.HostedOn'}}
    helm_requirements = [helm_req]
    helm_application_info['requirements'] = helm_requirements
    helm_application_info['interfaces'] = helm_interface
    helm_application_info['name'] = app_name

    helm_dict_value = {}
    if helm_application_values:
        helm_dict_value.update(parse_helm_values(helm_application_values))
    if chart_name == 'argo/argo-workflows':
        container_runtime_executor_val = {'containerRuntimeExecutor': 'k8sapi'}
        helm_dict_value.update(container_runtime_executor_val)

    if helm_dict_value:
        helm_interface['Helm']['install_chart']['inputs']['extra_variables']['values'] = helm_dict_value
    return helm_application_info


def build_tosca(topologies_boxes=None, enable_monitoring_widget=None, app_name_widget=None,
                helm_app_chart_name_widget=None,
                helm_app_repo_name_widget=None, helm_app_values=None, helm_app_repo_url_widget=None, file_name=None):
    index = 0
    node_templates = {}
    topology_names = []
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

    k8s_workflows = get_k8s_workflows(topology_names, enable_monitoring_widget.value, app_name_widget.value,
                                      topology_info=topology_info)
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
                                      helm_app_repo_url_widget.value, app_name_widget.value, helm_app_values.value,
                                      vm_master_name=vm_master_name)

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

    if os.path.exists(file_name):
        os.remove(file_name)

    with open(file_name, 'w') as file:
        yaml.dump(tosca, file, default_flow_style=False, Dumper=NoAliasDumper)


def upload_tosca(base_url=None, username=None, password=None, file_name=None):
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    path = "/tosca_template"
    payload = {}
    fin = open(file_name, 'rb')
    files = {'file': fin}

    headers = {}

    response = requests.request("POST", base_url + path, headers=headers, files=files, verify=False,
                                auth=(username, password))
    tosca_id = response.text

    return tosca_id


def provision(tosca_id=None, base_url=None, username=None, password=None):
    path = "/provisioner/provision/" + tosca_id
    payload = {}
    headers = {'accept': 'text/plain'}

    response = requests.request("GET", base_url + path, headers=headers, data=payload, verify=False,
                                auth=(username, password))
    if response.status_code != 200:
        raise Exception('Something was wrong with the request: ' + str(response))
    provisioned_tosca_id = response.text
    return provisioned_tosca_id


def deploy(tosca_id=None, base_url=None, username=None, password=None):
    path = "/deployer/deploy/" + tosca_id
    payload = {}
    headers = {'accept': 'text/plain'}

    response = requests.request("GET", base_url + path, headers=headers, data=payload, verify=False,
                                auth=(username, password))
    if response.status_code != 200:
        raise Exception('Something was wrong with the request')
    deployed_tosca_id = response.text
    return deployed_tosca_id


def delete(tosca_id=None, base_url=None, username=None, password=None):
    path = "/tosca_template/" + tosca_id
    payload = {}
    headers = {'accept': 'text/plain'}

    response = requests.request("DELETE", base_url + path, headers=headers, data=payload, verify=False,
                                auth=(username, password))
    if response.status_code != 200:
        raise Exception('Something was wrong with the request')
    deleted_tosca_id = response.text
    return deleted_tosca_id
