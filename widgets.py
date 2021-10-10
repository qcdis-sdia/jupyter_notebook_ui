import ipywidgets as widgets

sdia_conf_url_widget = widgets.Text(
    value='https://lifewatch.lab.uvalight.net:30003/orchestrator',
    placeholder='Enter SDIA API endpoint. e.g. https://lifewatch.lab.uvalight.net:30003/orchestrator',
    description='SDIA API URL:',
    disabled=False
)
sdia_conf_username_widget = widgets.Text(
    value='notebook_user',
    placeholder='Enter SDIA username',
    description='SDIA username:',
    disabled=False
)

sdia_conf_token_widget = widgets.Password(
    value='',
    placeholder='Enter your SDIA token',
    description='Password:',
    disabled=False
)

sdia_conf_login_button = widgets.Button(
    description='Login',
    disabled=False,
    button_style='',  # 'success', 'info', 'warning', 'danger' or ''
    tooltip='Run report',
    #     icon='check' # (FontAwesome names without the `fa-` prefix)
)

sdia_conf_output = widgets.Output()
sdia_conf_box = widgets.VBox(
    [sdia_conf_url_widget, sdia_conf_username_widget, sdia_conf_token_widget, sdia_conf_login_button])

application_type_widget = widgets.Dropdown(
    options=['Helm'],
    value='Helm',
    description='Application Type:',
    disabled=False
)

application_type_output = widgets.Output()
application_type_box = widgets.VBox([application_type_widget])

docker_app_image_name_widget = widgets.Textarea(
    value='cloudcells/classifiers',
    placeholder='image name e.g. cloudcells/classifiers',
    description='Docker Image Name:',
    disabled=False
)

docker_app_image_ports_widget = widgets.Textarea(
    value='',
    placeholder='the ports to expose e.g. 80',
    description='Ports:',
    disabled=False
)

enable_monitoring_widget = widgets.Checkbox(
    value=True,
    description='Monitoring',
    disabled=False
)

app_name_widget = widgets.Text(
    value='argowf',
    placeholder='the applications name',
    description='Application Name:',
    disabled=False
)

docker_app_box = widgets.VBox(
    [app_name_widget, docker_app_image_name_widget, docker_app_image_ports_widget, enable_monitoring_widget])

helm_app_chart_name_widget = widgets.Text(
    value='argo/argo-workflows',
    placeholder='the chart name e.g. argo/argo',
    description='Chart Name:',
    disabled=False
)

helm_app_repo_name_widget = widgets.Text(
    value='argo',
    placeholder='the name of the repoitory name',
    description='Reposetory Name:',
    disabled=False
)

helm_app_repo_url_widget = widgets.Text(
    value='https://argoproj.github.io/argo-helm',
    placeholder='the url',
    description='Reposetory URL:',
    disabled=False
)

helm_app_values = widgets.Text(
    value='server.serviceType=NodePort',
    placeholder='helm values',
    description='helm values',
    disabled=False
)

helm_app_box = widgets.VBox(
    [app_name_widget, helm_app_chart_name_widget, helm_app_repo_name_widget, helm_app_repo_url_widget, helm_app_values,
     enable_monitoring_widget])

app_conf_output = widgets.Output()

num_of_topologies_widget = widgets.BoundedIntText(
    value=1,
    min=1,
    max=4,
    step=1,
    description='Num. Of Topologies:',
    disabled=False
)

topologies_output = widgets.Output()
number_of_topology_box = widgets.VBox([num_of_topologies_widget])

topologies_boxes = []
domain_names = ['East US', 'Central US', 'South Central US', 'West US', 'Australia East', 'Southeast Asia', 'UK South',
                'West Europe', 'North Europe', 'South Africa North', 'Central India']

for i in range(0, num_of_topologies_widget.value):
    cloud_provider_name_widget = widgets.Dropdown(
        options=['Azure'],
        value='Azure',
        description='Cloud Provider:',
        name='cloud_provider_name',
        disabled=False
    )

    num_of_vms_widget = widgets.BoundedIntText(
        value=6,
        min=1,
        max=100,
        step=1,
        description='Num. Of VMs:',
        disabled=False
    )
    vm_size_name_widget = widgets.Dropdown(
        options=['small', 'medium', 'large', 'large_mem'],
        value='small',
        description='VM size:',
        disabled=False
    )
    topology_domain_widget = widgets.Dropdown(
        options=domain_names,
        value=domain_names[7],
        description='Topology Domain:',
        disabled=False
    )
    topology_box = widgets.VBox(
        [cloud_provider_name_widget, num_of_vms_widget, vm_size_name_widget, topology_domain_widget])
    topologies_boxes.append(topology_box)

topologies_conf_tab = widgets.Tab()
topologies_conf_tab.children = topologies_boxes
for i in range(len(topologies_boxes)):
    topologies_conf_tab.set_title(i, 'topology_' + str(i + 1))

topologies_conf_output = widgets.Output()
topologies_conf_tab_box = widgets.VBox([topologies_conf_tab])

node_templates = {}
app_prop = []

if application_type_widget.value == 'Docker':
    app_prop.append('Image Name: ' + docker_app_image_name_widget.value)
    app_prop.append('Ports: ' + docker_app_image_ports_widget.value)
elif application_type_widget.value == 'Helm':
    app_prop.append('Application Type: ' + application_type_widget.value)
    app_prop.append('Chart name: ' + helm_app_chart_name_widget.value)
    app_prop.append('Reposetory name: ' + helm_app_repo_name_widget.value)
    app_prop.append('Reposetory URL: ' + helm_app_repo_url_widget.value)

text = 'Application\n'
for line in app_prop:
    text += line + '\n'

text += '\nInfrastructure\n'
