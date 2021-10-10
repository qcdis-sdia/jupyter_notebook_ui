# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import configparser
import csv
import time
import traceback
from datetime import datetime

from methods import *
from widgets import *

topology_names = []


# Press the green button in the gutter to run the script.


def build_topologies_boxes(vm_num=None):
    for i in range(0, num_of_topologies_widget.value):
        cloud_provider_name_widget = widgets.Dropdown(options=['Azure'], value='Azure',
                                                      description='Cloud Provider:',
                                                      name='cloud_provider_name',
                                                      disabled=False
                                                      )

        num_of_vms_widget = widgets.BoundedIntText(
            value=vm_num,
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
    return topologies_boxes


if __name__ == '__main__':

    config = configparser.ConfigParser()
    config.read('conf.ini')
    sure_tosca_base_url = config['sdia']['base_url']

    base_url = config['sdia']['base_url']
    username = config['sdia']['username']
    password = config['sdia']['password']
    header = ['num_of_vm', 'build_tosca_time', 'upload_tosca_time', 'provision_time', 'deploy_time', 'delete_time',
              'total_time']
    data = []
    now = datetime.now().strftime('%M:%S.%f')[:-4]
    csv_name = str(now) + '_elapsed.csv'
    with open(csv_name, 'w', encoding='UTF8') as f:
        writer = csv.writer(f)
        writer.writerow(header)

    for num_of_vm in [2]:
        print('Building tosca. Num of VMs: ' + str(num_of_vm))
        new_topologies_boxes = build_topologies_boxes(num_of_vm)
        start = time.time()
        total_start = time.time()
        build_tosca(topologies_boxes=new_topologies_boxes, enable_monitoring_widget=enable_monitoring_widget,
                    app_name_widget=app_name_widget,
                    helm_app_chart_name_widget=helm_app_chart_name_widget,
                    helm_app_repo_name_widget=helm_app_repo_name_widget, helm_app_values=helm_app_values,
                    helm_app_repo_url_widget=helm_app_repo_url_widget, file_name=str(num_of_vm) + '_vms_tosca.yaml')
        build_tosca_time = (time.time() - start)

        start = time.time()
        print('Uploading tosca')
        tosca_id = upload_tosca(base_url=base_url, username=username, password=password,
                                file_name=str(num_of_vm) + '_vms_tosca.yaml')
        upload_tosca_time = (time.time() - start)
        print('tosca_id: ' + tosca_id)

        start = time.time()
        print('Provisioning')
        prov_id = provision(username=username, base_url=base_url, tosca_id=tosca_id, password=password)
        print('Provisioned: ' + prov_id)
        provision_time = (time.time() - start)

        start = time.time()
        print('Deploying')
        deploy_time = -1
        try:
            deploy_id = deploy(username=username, base_url=base_url, tosca_id=prov_id, password=password)
            print('Deployed: ' + deploy_id)
            deploy_time = (time.time() - start)
        except Exception as e:
            traceback.print_exc()
            pass

        # start = time.time()
        # print('Deleting')
        # delete(username=username, base_url=base_url, tosca_id=prov_id, password=password)
        # delete_time = (time.time() - start)
        #
        # total_time = (time.time() - total_start)
        # line = [num_of_vm, build_tosca_time, upload_tosca_time, provision_time, deploy_time, delete_time, total_time]
        #
        # with open(csv_name, 'a', encoding='UTF8') as f:
        #     writer = csv.writer(f)
        #     writer.writerow(line)
