import requests
import allure
import sys
import json
from common.getConfig import get_apiserver
from common import commonFunction
from step import multi_workspace_steps

env_url = get_apiserver()
sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from common.getHeader import get_header, get_header_for_patch


@allure.step('在企业空间指定集群创建普通项目')
def step_create_project_in_ws(ws_name, cluster_name, project_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/tenant.kubesphere.io/v1alpha2/workspaces/' \
          + ws_name + '/namespaces'
    data = {"apiVersion": "v1", "kind": "Namespace",
            "metadata": {"name": project_name, "labels": {"kubesphere.io/workspace": ws_name},
                         "annotations": {"kubesphere.io/creator": "admin"}}, "cluster": cluster_name}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('删除在企业空间创建的普通项目')
def step_delete_project_in_ws(ws_name, cluster_name, project_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + \
          '/namespaces/' + project_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('在多集群环境创建存储卷')
def step_create_volume_in_fed_project(cluster_name, project_name, volume_name):
    url = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedpersistentvolumeclaims'
    url2 = url + '?dryRun=All'
    clusters = []
    overrides = []
    for name in cluster_name:
        override = {}
        cluster = {'name': name}
        override['clusterName'] = name
        override['clusterOverrides'] = []
        clusters.append(cluster)
        overrides.append(override)
        # 获取集群的默认存储类
    data = {"apiVersion": "types.kubefed.io/v1beta1",
            "kind": "FederatedPersistentVolumeClaim",
            "metadata": {"namespace": project_name, "name": volume_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"placement": {"clusters": clusters},
                     "template": {"metadata": {"namespace": project_name, "labels": {}},
                                  "spec": {"accessModes": ["ReadWriteOnce"],
                                           "resources": {"requests": {"storage": "10Gi"}},
                                           }},
                     "overrides": overrides}}

    requests.post(url=url2, headers=get_header(), data=json.dumps(data))
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在多集群环境指定项目创建部署并挂载存储卷')
def step_create_workload_in_multi_project(cluster_name, project_name, work_name, pvc_name, container_name='', image='nginx'):
    base_url = env_url + '/apis/clusters/' + cluster_name + '/apps/v1/namespaces/' + project_name + '/deployments'
    url = base_url + '?dryRun=All'
    container_name = container_name if container_name else work_name + '-container' + str(commonFunction.get_random())
    volume_name = pvc_name + '-volume' + str(commonFunction.get_random())
    data = {"apiVersion": "apps/v1", "kind": "Deployment",
            "metadata": {"namespace": project_name, "labels": {"app": work_name}, "name": work_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"replicas": 1, "selector": {"matchLabels": {"app": work_name}}, "template": {
                "metadata": {"labels": {"app": work_name}, "annotations": {"kubesphere.io/imagepullsecrets": "{}",
                                                                      "logging.kubesphere.io/logsidecar-config": "{}",
                                                                      "kubesphere.io/creator": "admin"}}, "spec": {
                    "containers": [{"name": container_name, "imagePullPolicy": "IfNotPresent",
                                    "ports": [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}],
                                    "image": image, "volumeMounts": [
                            {"name": volume_name, "readOnly": False, "mountPath": "/data"}]}],
                    "serviceAccount": "default", "terminationGracePeriodSeconds": 30, "initContainers": [], "volumes": [
                        {"name": volume_name, "persistentVolumeClaim": {"claimName": pvc_name}}],
                    "imagePullSecrets": None}}, "strategy": {"type": "RollingUpdate",
                                                             "rollingUpdate": {"maxUnavailable": "25%",
                                                                               "maxSurge": "25%"}}}}
    requests.post(url=url, headers=get_header(), data=json.dumps(data))
    response = requests.post(url=base_url, headers=get_header(), data=json.dumps(data))
    return response

@allure.step('删除多集群环境指定项目的部署')
def step_delete_workload_in_multi_project(cluster_name, project_name, work_name):
    url = env_url + '/apis/clusters/' + cluster_name + '/apps/v1/namespaces/' + project_name + '/deployments/' + work_name
    response = requests.delete(url=url, headers=get_header())
    return response

@allure.step('在多集群项目创建deployment')
def step_create_deploy_in_fed_project(cluster_name, project_name, work_name, container_name, image, replicas, ports,
                                        volumemount, volume_info, strategy):
    """
    :param cluster_name:
    :param strategy: 策略信息
    :param ports: 容器的端口信息
    :param volumemount: 绑定存储卷的设置
    :return: 接口响应对象
    :param replicas: 副本数
    :return: 接口对象
    :param volume_info: 绑定的存储卷信息
    :param project_name: 项目名称
    :param work_name: 工作负载名称
    :param container_name: 容器名称
    :param image: 镜像名称
    """
    url1 = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federateddeployments'
    url2 = url1 + '?dryRun=All'
    clusters = []
    overrides = []
    for name in cluster_name:
        override = {}
        cluster = {'name': name}
        override['clusterName'] = name
        override['clusterOverrides'] = []
        clusters.append(cluster)
        overrides.append(override)
    data = {"apiVersion": "types.kubefed.io/v1beta1", "kind": "FederatedDeployment",
            "metadata": {"namespace": project_name,
                         "name": work_name,
                         "labels": {"app": work_name},
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"placement": {"clusters": clusters},
                     "template": {"metadata": {"namespace": project_name, "labels": {"app": work_name}},
                                  "spec": {"replicas": replicas,
                                           "selector": {"matchLabels": {"app": work_name}},
                                           "template": {"metadata": {"labels": {"app": work_name}},
                                                        "spec": {
                                                            "containers": [
                                                                {"name": container_name,
                                                                 "imagePullPolicy": "IfNotPresent",
                                                                 "image": image,
                                                                 "ports": ports,
                                                                 "volumeMounts": volumemount
                                                                 }],
                                                            "serviceAccount": "default",
                                                            "affinity": {},
                                                            "initContainers": [],
                                                            "volumes": volume_info,
                                                            "imagePullSecrets": None
                                                        }},
                                           "strategy": strategy}},
                     "overrides": overrides}}

    requests.post(url=url2, headers=get_header(), data=json.dumps(data))
    response = requests.post(url=url1, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在多集群环境获取指定的工作负载')
def step_get_workload_in_multi_project(cluster_name, project_name, type, condition):
    """
    :param cluster_name:
    :param project_name: 项目名称
    :param type: 负载类型
    :param condition: 查询条件
    :return:
    """
    url = env_url + '/apis/clusters/' + cluster_name + '/apps/v1/namespaces/' \
          + project_name + '/' + type + '/' + condition
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群项目/工作负载列表中获取指定的工作负载')
def step_get_workload_in_fed_project_list(project_name, type, condition):
    """
    :param project_name: 项目名称
    :param type: 负载类型
    :param condition: 查询条件
    :return:
    """
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + '/federated' + type + '?name=' + condition
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在集群详情获取存储卷状态')
def step_get_volume_status(cluster_name, volume_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/persistentvolumeclaims?name=' + volume_name + '&sortBy=createTime&limit=10'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除多集群项目指定的工作负载')
def step_delete_workload_in_fed_project(project_name, type, work_name):
    url = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federated' + type + '/' + work_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('删除多集群项目的存储卷')
def step_delete_volume_in_fed_project(project_name, volume_name):
    url = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + \
          '/federatedpersistentvolumeclaims/' + volume_name
    # 删除存储卷
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('在多集群环境创建无状态服务')
def step_create_service_in_fed_project(cluster_name, project_name, service_name, port):
    url1 = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedservices?dryRun=All'
    url2 = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedservices'

    clusters = []
    overrides = []
    for name in cluster_name:
        override = {}
        cluster = {'name': name}
        override['clusterName'] = name
        override['clusterOverrides'] = []
        clusters.append(cluster)
        overrides.append(override)

    data = {"apiVersion": "types.kubefed.io/v1beta1",
            "kind": "FederatedService",
            "metadata": {"namespace": project_name,
                         "annotations": {
                             "kubesphere.io/serviceType": "statelessservice",
                             "kubesphere.io/workloadName": service_name + "-v1",
                             "kubesphere.io/workloadModule": "deployments",
                             "kubesphere.io/creator": "admin"},
                         "labels": {
                             "app": service_name},
                         "name": service_name},
            "spec": {"placement": {"clusters": clusters}, "template": {
                "metadata": {"namespace": project_name, "labels": {"version": "v1", "app": service_name}},
                "spec": {"sessionAffinity": "None", "selector": {"app": service_name},
                         "template": {"metadata": {"labels": {"version": "v1", "app": service_name}}},
                         "ports": port}},
                     "overrides": overrides}}
    requests.post(url=url1, headers=get_header(), data=json.dumps(data))
    response = requests.post(url=url2, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查询指定的多集群项目')
def step_get_project_in_multi_project(ws_name, project_name):
    url1 = env_url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + \
           '/federatednamespaces?name=' + project_name
    response = requests.get(url=url1, headers=get_header())
    return response


@allure.step('获取环境中所有的多集群项目的名称和部署集群')
def step_get_multi_project_all(ws):
    """
    :param ws: 查询的企业空间名称
    :return:
    """
    multi_projects = []
    response = multi_workspace_steps.step_query_ws(ws)
    ws_count = response.json()['totalItems']
    for k in range(0, ws_count):
        # 获取每个企业空间的名称
        ws_name = response.json()['items'][k]['metadata']['name']
        if ws_name != 'system-workspace':
            # 查询环境中存在的所有多集群项目
            r = step_get_project_in_multi_project(ws_name, '')
            project_count = r.json()['totalItems']
            for i in range(0, project_count):
                project_info = []
                project_name = r.json()['items'][i]['metadata']['name']
                project_info.append(project_name)
                overrides = r.json()['items'][i]['spec']['overrides']
                override_count = len(overrides)
                for j in range(0, override_count):
                    cluster_name = overrides[j]['clusterName']
                    project_info.append(cluster_name)
                project_info.append(ws_name)
                multi_projects.append(project_info)
    return multi_projects


@allure.step('在多集群项目创建statefulsets')
def step_create_sts_in_fed_project(cluster_name, project_name, work_name, container_name, image, replicas, ports,
                                     service_ports,
                                     volumemount, volume_info, service_name):
    url1 = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedstatefulsets?dryRun=All'
    url3 = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedstatefulsets'
    url2 = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedservices?dryRun=All'
    url4 = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedservices'
    clusters = []
    overrides = []
    for name in cluster_name:
        override = {}
        cluster = {'name': name}
        override['clusterName'] = name
        override['clusterOverrides'] = []
        clusters.append(cluster)
        overrides.append(override)
    data1 = {"apiVersion": "types.kubefed.io/v1beta1",
             "kind": "FederatedStatefulSet",
             "metadata": {"namespace": project_name,
                          "name": work_name,
                          "labels": {"app": work_name},
                          "annotations": {"kubesphere.io/creator": "admin"}},
             "spec": {"placement": {"clusters": clusters},
                      "template": {"metadata": {"namespace": project_name, "labels": {"app": work_name}},
                                   "spec": {"replicas": replicas, "selector": {"matchLabels": {"app": work_name}},
                                            "template": {
                                                "metadata": {"labels": {"app": work_name},
                                                             "annotations": {
                                                                 "logging.kubesphere.io/logsidecar-config": "{}"}},
                                                "spec": {"containers": [
                                                    {"name": container_name, "imagePullPolicy": "IfNotPresent",
                                                     "image": image, "ports": ports,
                                                     "volumeMounts": volumemount}],
                                                    "serviceAccount": "default", "affinity": {}, "initContainers": [],
                                                    "volumes": volume_info,
                                                    "imagePullSecrets": None}},
                                            "updateStrategy": {"type": "RollingUpdate",
                                                               "rollingUpdate": {
                                                                   "partition": 0}},
                                            "serviceName": service_name}},
                      "overrides": overrides}}

    data2 = {"apiVersion": "types.kubefed.io/v1beta1",
             "kind": "FederatedService",
             "metadata": {"namespace": project_name, "name": work_name,
                          "annotations": {"kubesphere.io/alias-name": "test",
                                          "kubesphere.io/serviceType": "statefulservice",
                                          "kubesphere.io/creator": "admin"},
                          "labels": {"app": work_name}},
             "spec": {"placement":
                          {"clusters": clusters},
                      "template": {"metadata": {"namespace": project_name, "labels": {}},
                                   "spec": {"sessionAffinity": "None",
                                            "selector": {"app": work_name},
                                            "ports": service_ports,
                                            "clusterIP": "None"}},
                      "overrides": overrides}}

    requests.post(url=url1, headers=get_header(), data=json.dumps(data1))
    requests.post(url=url2, headers=get_header(), data=json.dumps(data2))
    requests.post(url=url3, headers=get_header(), data=json.dumps(data1))
    response = requests.post(url=url4, headers=get_header(), data=json.dumps(data2))
    return response


@allure.step('在多集群项目创建路由')
def step_create_route_in_fed_project(cluster_name, project_name, ingress_name, host, service_info):
    url1 = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedingresses?dryRun=All'
    url2 = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedingresses'
    clusters = []
    overrides = []
    for name in cluster_name:
        cluster = {'name': name}
        clusters.append(cluster)
        override = {"clusterName": name, "clusterOverrides": [{"path": "/spec/rules", "value": [
            {"clusters": [name], "protocol": "http", "host": host,
             "http": {"paths": [
                 {"path": "/", "backend": service_info}]}}]},
                                                              {"path": "/spec/tls",
                                                               "value": []}]}
        overrides.append(override)

    data = {"apiVersion": "types.kubefed.io/v1beta1",
            "kind": "FederatedIngress",
            "metadata": {"namespace": project_name, "name": ingress_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"placement": {"clusters": clusters},
                     "template": {"metadata": {"namespace": project_name, "labels": {}},
                                  "spec": {"rules": [
                                      {"clusters": cluster_name, "protocol": "http", "host": host,
                                       "http": {"paths": [
                                           {"path": "/", "backend": service_info
                                            }]}}],
                                      "tls": []}},
                     "overrides": overrides}}
    requests.post(url=url1, headers=get_header(), data=json.dumps(data))
    response = requests.post(url=url2, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在多集群项目删除路由')
def step_delete_route_in_fed_project(project_name, ingress_name):
    url = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedingresses/' + ingress_name
    requests.delete(url=url, headers=get_header())


@allure.step('在多集群项目设置网关')
def step_create_gateway_in_multi_project(cluster_name, project_name, type, annotations):
    url = env_url + '/kapis/clusters/' + cluster_name + \
          '/resources.kubesphere.io/v1alpha2/namespaces/' + project_name + '/router'
    data = {"type": type, "annotations": annotations}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('编辑多集群项目的网关')
def step_edit_gateway_in_multi_project(cluster_name, project_name, type, annotations):
    url = env_url + '/kapis/clusters/' + cluster_name + \
          '/resources.kubesphere.io/v1alpha2/namespaces/' + project_name + '/router'
    data = {"type": type, "annotations": annotations}
    response = requests.put(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在多集群项目删除网关')
def step_delete_gateway_in_multi_project(cluster_name, project_name):
    url = env_url + '/kapis/clusters/' + cluster_name + \
          '/resources.kubesphere.io/v1alpha2/namespaces/' + project_name + '/router'
    data = {}
    response = requests.delete(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查看多集群项目网关')
def step_get_gateway_in_multi_project(cluster_name, project_name):
    url = env_url + '/kapis/clusters/' + cluster_name + \
          '/resources.kubesphere.io/v1alpha2/namespaces/' + project_name + '/router'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('修改多集群项目工作负载副本数')
def step_modify_work_replicas_in_fed_project(cluster_name, project_name, type, work_name, replicas):
    """
    :param project_name: 项目名称
    :param work_name: 工作负载名称
    :param replicas: 副本数
    """
    url1 = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federated' + type + '/' + work_name
    url2 = env_url + '/apis/clusters/' + cluster_name + '/apps/v1/namespaces/' + project_name + '/' + type + '/' + work_name
    data1 = {
        "spec": {"overrides": [{"clusterName": cluster_name,
                                "clusterOverrides": [{"path": "/spec/replicas", "value": replicas}]
                                }
                               ]
                 }
    }
    data2 = {"spec": {"replicas": replicas}}
    requests.patch(url=url1, headers=get_header_for_patch(), data=json.dumps(data1))
    response = requests.patch(url=url2, headers=get_header_for_patch(), data=json.dumps(data2))
    return response


@allure.step('获取多集群项目的工作负载中所有的容器组的运行情况')
def step_get_work_pod_info_in_multi_project(cluster_name, project_name, work_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/namespaces/' + \
          project_name + '/pods?ownerKind=ReplicaSet&labelSelector=app%3D' + work_name

    r = requests.get(url=url, headers=get_header())
    return r


@allure.step('在多集群项目获取项目配额的resourceVersion')
def step_get_project_quota_version_in_multi_project(cluster_name, project_name):
    url = env_url + '/api/clusters/' + cluster_name + '/v1/namespaces/' + project_name + \
          '/resourcequotas/' + project_name
    response = requests.get(url=url, headers=get_header())
    try:
        if response.json():
            return response.json()['metadata']['resourceVersion']
        else:
            return None
    except Exception as e:
        print(e)


@allure.step('在多集群项目编辑项目配额')
def step_edit_project_quota_in_multi_project(cluster_name, project_name, hard, resource_version):
    url_put = env_url + '/api/clusters/' + cluster_name + '/v1/namespaces/' + project_name + \
              '/resourcequotas/' + project_name
    url_post = env_url + '/api/clusters/' + cluster_name + '/v1/namespaces/' + project_name + '/resourcequotas'

    data_post = {"apiVersion": "v1",
                 "kind": "ResourceQuota",
                 "metadata": {
                     "name": project_name,
                     "namespace": project_name,
                     "cluster": cluster_name,
                     "annotations": {"kubesphere.io/creator": "admin"}}, "spec": {
            "hard": hard}}

    data_put = {"apiVersion": "v1",
                "kind": "ResourceQuota",
                "metadata": {
                    "name": project_name,
                    "namespace": project_name,
                    "cluster": cluster_name,
                    "resourceVersion": resource_version},
                "spec": {
                    "hard": hard}}

    if resource_version is None:
        response = requests.post(url=url_post, headers=get_header(), data=json.dumps(data_post))
    else:
        response = requests.put(url=url_put, headers=get_header(), data=json.dumps(data_put))
    return response


@allure.step('在多集群项目查询项目配额')
def step_get_project_quota_in_multi_project(cluster_name, project_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha2/namespaces/' + \
          project_name + '/quotas'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取多集群环境容器默认资源请求')
def step_get_container_quota_in_fed_project(project_name, ws_name):
    url = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + \
          '/federatedlimitranges?workspace=' + ws_name
    try:
        response = requests.get(url=url, headers=get_header())
        return response
    except Exception as e:
        print(e)


@allure.step('在多集群项目编辑容器资源默认请求')
def step_edit_container_quota_in_fed_project(cluster_name, project_name, resource_version, limit, request):
    url_post = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedlimitranges'
    url_put = url_post + project_name
    limits = [{"defaultRequest": request, "type": "Container", "default": limit}]
    clusters = []
    overrides = []
    for name in cluster_name:
        override = {}
        cluster = {'name': name}
        override['clusterName'] = name
        override['clusterOverrides'] = []
        clusters.append(cluster)
        overrides.append(override)

    data_post = {"apiVersion": "types.kubefed.io/v1beta1",
                 "kind": "FederatedLimitRange",
                 "metadata": {"name": project_name,
                              "annotations": {"kubesphere.io/creator": "admin"}},
                 "spec": {"placement": {"clusters": clusters},
                          "template": {"metadata": {}, "spec": {
                              "limits": [
                                  {"default": limit,
                                   "defaultRequest": request,
                                   "type": "Container"}
                              ]}},
                          "overrides": overrides}}

    data_put = {"apiVersion": "types.kubefed.io/v1beta1",
                "kind": "FederatedLimitRange",
                "metadata": {"annotations": {"kubesphere.io/creator": "admin"},
                             "finalizers": ["kubefed.io/sync-controller"],
                             "name": project_name,
                             "namespace": project_name,
                             "resourceVersion": resource_version},
                "spec": {"overrides": overrides,
                         "placement": {"clusters": clusters},
                         "template": {"metadata": {}, "spec": {
                             "limits": limits
                         }}}}
    if resource_version is None:
        response = requests.post(url=url_post, headers=get_header(), data=json.dumps(data_post))
    else:
        response = requests.put(url=url_put, headers=get_header(), data=json.dumps(data_put))
    return response


@allure.step('创建多集群项目')
def step_create_fed_project(ws_name, project_name, clusters):
    url = env_url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/namespaces'
    url1 = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatednamespaces?dryRun=All'
    url2 = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatednamespaces'
    cluster_actual = []
    overrides = []
    if isinstance(clusters, str):
        cluster_actual.append({"name": clusters})
        overrides.append({"clusterName": clusters,
                          "clusterOverrides": [
                              {"path": "/metadata/annotations",
                               "value": {"kubesphere.io/creator": "admin"}}]})

    else:
        for cluster in clusters:
            cluster_actual.append({"name": cluster})
            overrides.append({"clusterName": cluster,
                              "clusterOverrides": [
                                  {"path": "/metadata/annotations",
                                   "value": {"kubesphere.io/creator": "admin"}}]})
    data = {"apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": project_name,
                "labels": {
                    "kubesphere.io/workspace": ws_name,
                    "kubesphere.io/kubefed-host-namespace": "true",
                    "kubefed.io/managed": "false"
                },
                "annotations": {"kubesphere.io/creator": "admin"}}, "spec": {}}

    data1 = {"apiVersion": "types.kubefed.io/v1beta1",
             "kind": "FederatedNamespace",
             "metadata": {
                 "name": project_name, "namespace": project_name,
                 "labels": {"kubesphere.io/workspace": ws_name},
                 "annotations": {"kubesphere.io/creator": "admin"}},
             "spec": {"placement":
                          {"clusters": cluster_actual},
                      "template": {"metadata": {"labels": {"kubesphere.io/workspace": ws_name}}},
                      "overrides": overrides}}
    requests.post(url=url, headers=get_header(), data=json.dumps(data))
    requests.post(url=url1, headers=get_header(), data=json.dumps(data1))
    requests.post(url=url2, headers=get_header(), data=json.dumps(data1))


@allure.step('编辑多集群项目')
def step_edit_project_in_fed_project(cluster_name, ws_name, project_name, alias_name, description):
    url = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + \
          '/federatednamespaces/' + project_name

    clusters = []
    overrides = []
    for name in cluster_name:
        override = {}
        cluster = {'name': name}
        override['clusterName'] = name
        override['clusterOverrides'] = [{"path": "/metadata/annotations", "value": {"kubesphere.io/creator": "admin"}}]
        clusters.append(cluster)
        overrides.append(override)

    data = {"metadata": {"name": project_name, "namespace": project_name,
                         "labels": {"kubesphere.io/workspace": ws_name},
                         "annotations": {"kubesphere.io/alias-name": alias_name,
                                         "kubesphere.io/creator": "admin",
                                         "kubesphere.io/description": description},
                         "finalizers": ["kubefed.io/sync-controller"]},
            "spec": {"template": {"spec": {}}, "placement": {"clusters": clusters},
                     "overrides": overrides}}
    response = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('在多集群项目创建默认密钥')
def step_create_secret_default_in_fed_project(cluster_name, project_name, secret_name, key, value):
    url = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedsecrets'
    url1 = url + '?dryRun=All'
    clusters = []
    overrides = []
    for name in cluster_name:
        override = {}
        cluster = {'name': name}
        override['clusterName'] = name
        override['clusterOverrides'] = []
        clusters.append(cluster)
        overrides.append(override)

    data = {"apiVersion": "types.kubefed.io/v1beta1",
            "kind": "FederatedSecret",
            "metadata": {"namespace": project_name,
                         "name": secret_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"placement": {"clusters": clusters},
                     "template": {"metadata":
                                      {"namespace": project_name, "labels": {}},
                                  "type": "Opaque",
                                  "spec": {"template": {"metadata": {"labels": {}}}},
                                  "data": {key: value}},
                     "overrides": overrides}}

    requests.post(url=url1, headers=get_header(), data=json.dumps(data))
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在多集群项目创建TLS类型密钥')
def step_create_secret_tls_in_fed_project(cluster_name, project_name, secret_name, credential, key):
    url = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedsecrets'
    url1 = url + '?dryRun=All'
    clusters = []
    overrides = []
    for name in cluster_name:
        override = {}
        cluster = {'name': name}
        override['clusterName'] = name
        override['clusterOverrides'] = []
        clusters.append(cluster)
        overrides.append(override)

    data = {"apiVersion": "types.kubefed.io/v1beta1",
            "kind": "FederatedSecret",
            "metadata": {"namespace": project_name,
                         "name": secret_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"placement": {"clusters": clusters},
                     "template": {"metadata":
                                      {"namespace": project_name, "labels": {}},
                                  "type": "kubernetes.io/tls",
                                  "spec": {"template": {"metadata": {"labels": {}}}},
                                  "data": {"tls.crt": credential, "tls.key": key}},
                     "overrides": overrides}}
    requests.post(url=url1, headers=get_header(), data=json.dumps(data))
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在多集群项目查询密钥')
def step_get_federatedsecret(project_name, secret_name):
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + \
          '/federatedsecrets?name=' + secret_name + '&sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群项目删除密钥')
def step_delete_fed_secret(project_name, secret_name):
    url = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedsecrets/' + secret_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('在多集群项目删除配置')
def step_delete_fed_config_map(project_name, config_name):
    url = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + \
          '/federatedconfigmaps/' + config_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('在多集群项目创建配置')
def step_create_config_map_in_fed_project(cluster_name, project_name, config_name, key, value):
    url = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedconfigmaps'
    url1 = url + '?dryRun=All'
    clusters = []
    overrides = []
    for name in cluster_name:
        override = {}
        cluster = {'name': name}
        override['clusterName'] = name
        override['clusterOverrides'] = []
        clusters.append(cluster)
        overrides.append(override)

    data = {"apiVersion": "types.kubefed.io/v1beta1",
            "kind": "FederatedConfigMap",
            "metadata": {
                "namespace": project_name,
                "name": config_name,
                "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"placement": {"clusters": clusters},
                     "template": {"metadata": {"namespace": project_name, "labels": {},
                                               "annotations": {"kubesphere.io/creator": "admin"}},
                                  "spec": {"template": {"metadata": {"labels": {}}}},
                                  "data": {value: key}},
                     "overrides": overrides}}
    requests.post(url=url1, headers=get_header(), data=json.dumps(data))
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在多集群环境设置落盘日志收集功能')
def step_set_disk_log_collection(project_name, set):
    url = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + \
          '/federatednamespaces/' + project_name
    data = {"metadata":
                {"labels":
                     {"logging.kubesphere.io/logsidecar-injection": set}},
            "spec":
                {"template":
                     {"metadata":
                          {"labels":
                               {"logging.kubesphere.io/logsidecar-injection": set}}}}}
    response = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('在多集群环境查询项目的监控信息')
def step_get_project_metrics_in_multi_project(cluster_name, project_name, start_time, end_time, step, times):
    url = env_url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/namespaces/' + \
          project_name + '?namespace=' + project_name + '&start=' + start_time + '&end=' + end_time + \
          '&step=' + step + '&times=' + times + '&metrics_filter=namespace_pod_count%7C' \
                                                'namespace_deployment_count%7Cnamespace_statefulset_count%7C' \
                                                'namespace_daemonset_count%7Cnamespace_job_count%7Cnamespace_cronjob_count%7Cnamespace_pvc_count%7C' \
                                                'namespace_service_count%7Cnamespace_secret_count%7Cnamespace_configmap_count%7C' \
                                                'namespace_ingresses_extensions_count%7Cnamespace_s2ibuilder_count%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群环境查询项目的abnormalworkloads')
def step_get_project_abnormalworkloads_in_multi_project(cluster_name, project_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha2/namespaces/' + \
          project_name + '/abnormalworkloads'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群环境查询项目的workloads')
def step_get_workloads_in_multi_project(project_name):
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + '/federateddeployments?sortBy=createTime&limit=10'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群项目创建账户密码密钥')
def step_create_secret_account_in_fed_project(cluster_name, project_name, secret_name, username, password):
    url = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedsecrets'
    url1 = url + '?dryRun=All'
    clusters = []
    overrides = []
    for name in cluster_name:
        override = {}
        cluster = {'name': name}
        override['clusterName'] = name
        override['clusterOverrides'] = []
        clusters.append(cluster)
        overrides.append(override)
    data = {"apiVersion": "types.kubefed.io/v1beta1",
            "kind": "FederatedSecret",
            "metadata": {"namespace": project_name,
                         "name": secret_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"placement": {"clusters": clusters},
                     "template": {"metadata":
                                      {"namespace": project_name, "labels": {}},
                                  "type": "kubernetes.io/basic-auth",
                                  "spec": {"template": {"metadata": {"labels": {}}}},
                                  "data": {"password": password, "username": username}},
                     "overrides": overrides}}

    requests.post(url=url1, headers=get_header(), data=json.dumps(data))
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在多集群项目查询配置')
def step_get_federatedconfigmap(project_name, config_name):
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + \
          '/federatedconfigmaps?name=' + config_name + '&sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群项目创建镜像仓库类型密钥')
def step_create_secret_image_in_fed_project(cluster_name, project_name, secret_name):
    url = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedsecrets'
    url1 = url + '?dryRun=All'
    clusters = []
    overrides = []
    for name in cluster_name:
        override = {}
        cluster = {'name': name}
        override['clusterName'] = name
        override['clusterOverrides'] = []
        clusters.append(cluster)
        overrides.append(override)
    data = {"apiVersion": "types.kubefed.io/v1beta1",
            "kind": "FederatedSecret",
            "metadata": {"namespace": project_name,
                         "name": secret_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"placement": {"clusters": clusters},
                     "template": {"metadata": {"namespace": project_name, "labels": {}},
                                  "type": "kubernetes.io/dockerconfigjson",
                                  "spec": {"template": {"metadata": {"labels": {}}}},
                                  "data": {
                                      ".dockerconfigjson": "eyJhdXRocyI6eyJodHRwczovL3NzIjp7InVzZXJuYW1lIjoic2FzYSIs"
                                                           "InBhc3N3b3JkIjoic2FzYSIsImVtYWlsIjoiIiwiYXV0aCI6ImMyRnpZ"
                                                           "VHB6WVhOaCJ9fX0="}},
                     "overrides": overrides}}

    requests.post(url=url1, headers=get_header(), data=json.dumps(data))
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('获取host集群的名称')
def step_get_host_name():
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/clusters?labelSelector=cluster-role.kubesphere.io%2Fhost'
    try:
        response = requests.get(url=url, headers=get_header())
        return response.json()['items'][0]['metadata']['name']
    except IndexError as e:
        print(e)


@allure.step('在多集群环境查询项目的federatedlimitranges')
def step_get_project_fed_limit_ranges(project_name):
    url = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedlimitranges'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群环境查询落盘日志收集功能')
def step_check_disk_log_collection(project_name):
    url = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + \
          '/federatednamespaces/' + project_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('创建存储卷')
def step_create_volume(cluster_name, project_name, volume_name):
    url = env_url + '/api/clusters/' + cluster_name + '/v1/namespaces/' + project_name + '/persistentvolumeclaims'
    data = {"apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"namespace": project_name, "name": volume_name, "labels": {},
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"accessModes": ["ReadWriteOnce"], "resources": {"requests": {"storage": "10Gi"}},
                     "storageClassName": "local"}}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('删除指定的项目')
def step_delete_project(cluster_name, ws_name, project_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/namespaces/' + project_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('删除指定的多集群项目')
def step_delete_fed_project(project_name):
    url = env_url + '/api/v1/namespaces/' + project_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('在指定集群创建项目')
def step_create_project_for_cluster(cluster_name, ws_name, project_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/tenant.kubesphere.io/v1alpha2/workspaces/' + \
          ws_name + '/namespaces'
    data = {"apiVersion": "v1", "kind": "Namespace",
            "metadata": {"name": project_name, "labels": {"kubesphere.io/workspace": ws_name},
                         "annotations": {"kubesphere.io/creator": "admin"}}, "cluster": cluster_name}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('从指定集群删除项目')
def step_delete_project_from_cluster(cluster_name, ws_name, project_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/tenant.kubesphere.io/v1alpha2/workspaces/' + \
          ws_name + '/namespaces/' + project_name
    response = requests.delete(url=url, headers=get_header())
    return response
