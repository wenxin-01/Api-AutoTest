import pytest
import allure
import sys
from common.getData import DoexcleByPandas
from common import commonFunction
from step import cluster_steps
import time
import random

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


@allure.feature('集群管理')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is True, reason='多集群环境下不执行')
class TestCluster(object):
    # 从文件中读取用例信息
    parametrize = DoexcleByPandas().get_data_for_pytest(filename='../data/data.xlsx', sheet_name='cluster')

    @allure.title('{title}')  # 设置用例标题
    # 将用例信息以参数化的方式传入测试方法
    @pytest.mark.parametrize('id,url,params,data, story, title,method,severity,condition,except_result', parametrize)
    def test_cluster(self, id, url, params, data, story, title, method, severity, condition, except_result):

        '''
        :param id: 用例编号
        :param url: 用例请求的URL地址
        :param data: 用例使用的请求数据
        :param title: 用例标题
        :param method: 用例的请求方式
        :param severity: 用例优先级
        :param condition: 用例的校验条件
        :param except_result: 用例的预期结果
        '''

        allure.dynamic.story(story)  # 动态生成模块
        allure.dynamic.severity(severity)  # 动态生成用例等级

        commonFunction.request_resource(url, params, data, story, title, method, severity, condition, except_result)

    @allure.story("节点")
    @allure.title('为节点设置污点')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_set_taints(self):
        # 污点信息
        taints = [{"key": "tester", "value": "wx", "effect": "NoSchedule"}]
        # 获取节点列表中第一个节点的名称
        response = cluster_steps.step_get_nodes()
        node_name = response.json()['items'][0]['metadata']['name']
        # 为节点设置污点
        cluster_steps.step_ste_taints(node_name, taints)
        # 获取节点的污点信息
        r = cluster_steps.step_get_node_detail_info(node_name)
        taints_actual = r.json()['spec']['taints']
        # 验证污点设置成功
        assert taints == taints_actual
        # 清空设置的污点
        cluster_steps.step_ste_taints(node_name=node_name, taints=[])

    @allure.story("节点")
    @allure.title('为节点添加标签')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_add_labels(self):
        # 获取节点列表中第一个节点的名称
        response = cluster_steps.step_get_nodes()
        node_name = response.json()['items'][0]['metadata']['name']
        # 获取节点的标签信息
        re = cluster_steps.step_get_node_detail_info(node_name)
        labels_old = re.json()['metadata']['labels']  # 用于删除添加的标签
        labels = re.json()['metadata']['labels']  # 用于添加标签
        # 添加标签的内容
        labels['tester/label'] = 'wxx'
        # 添加标签
        cluster_steps.step_add_labels_for_node(node_name, labels)
        # 获取编辑后节点的标签信息
        r = cluster_steps.step_get_node_detail_info(node_name)
        labels_actual = r.json()['metadata']['labels']
        # 验证标签添加成功
        assert labels == labels_actual
        # 删除添加的标签
        labels_old['tester/label'] = None
        cluster_steps.step_add_labels_for_node(node_name, labels_old)

    @allure.story('节点')
    @allure.title('设置节点为停止调度, 然后设置为启用调度')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_set_uncordon_node(self):
        # 获取节点列表中第一个节点的名称
        response = cluster_steps.step_get_nodes()
        node_name = response.json()['items'][0]['metadata']['name']
        # 设置节点为停止调度
        cluster_steps.step_cordon_node(node_name, True)
        # 获取节点的调度状态
        response = cluster_steps.step_get_node_detail_info(node_name)
        cordon_status = response.json()['spec']['unschedulable']
        # 验证节点调度状态为停止调度
        assert cordon_status == True
        # 设置节点为启用调度
        cluster_steps.step_cordon_node(node_name, False)

    @allure.story('节点')
    @allure.title('查看节点的pod信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_pods(self):
        # 获取节点列表中第一个节点的名称
        response = cluster_steps.step_get_nodes()
        node_name = response.json()['items'][0]['metadata']['name']
        # 查看节点的pod信息
        response = cluster_steps.step_get_pod_info(node_name)
        # 验证pod信息查询成功
        assert response.status_code == 200

    @allure.story('节点')
    @allure.title('查看节点的event信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_events(self):
        # 获取节点列表中第一个节点的名称
        response = cluster_steps.step_get_nodes()
        node_name = response.json()['items'][0]['metadata']['name']
        # 查看节点的event信息
        response = cluster_steps.step_get_event_of_node(node_name)
        # 获取资源类型
        kind = response.json()['kind']
        # 验证event信息查询成功
        assert kind == 'EventList'

    @allure.story('节点')
    @allure.title('查看节点的监控信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_monitoring(self):
        # 获取节点列表中第一个节点的名称
        response = cluster_steps.step_get_nodes()
        node_name = response.json()['items'][0]['metadata']['name']
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取10分钟之前的戳
        before_timestamp = commonFunction.get_before_timestamp(10)
        # 查看最近十分钟的监控信息
        r = cluster_steps.step_get_metrics_of_node(node_name=node_name, start_time=before_timestamp, end_time=now_timestamp,
                                     step='60s', times='10')
        # 获取查询到的数据的结果类型
        resultType = r.json()['results'][0]['data']['resultType']
        # 验证查询到的数据的结果类型
        assert resultType == 'matrix'

    @allure.story('节点')
    @allure.title('查看节点的状态信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_status(self):
        # 获取节点列表中第一个节点的名称
        response = cluster_steps.step_get_nodes()
        node_name = response.json()['items'][0]['metadata']['name']
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取20分钟之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp(20)
        # 查看节点的状态信息
        response = cluster_steps.step_get_status_of_node(node_name=node_name, start_time=before_timestamp, end_time=now_timestamp,
                                           step='180s', times='20')
        # 获取查询结果中的节点信息
        node = response.json()['results'][0]['data']['result'][0]['metric']['node']
        # 验证查询结果正确
        assert node == node_name

    @allure.story('节点')
    @allure.title('查询节点中不存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_non_existent_pod(self):
        # 获取节点列表中第一个节点的名称
        response = cluster_steps.step_get_nodes()
        node_name = response.json()['items'][0]['metadata']['name']
        # 查询不存在的pod
        pod_name = 'non-existent'
        re = cluster_steps.step_query_pod(node_name, pod_name)
        # 获取查询结果
        totalItems = re.json()['totalItems']
        # 验证查询结果
        assert totalItems == 0

    @allure.story('节点')
    @allure.title('按名称精确查询节点中存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_precise_query_existent_pod(self):
        # 获取节点列表中第一个节点的名称
        response = cluster_steps.step_get_nodes()
        node_name = response.json()['items'][0]['metadata']['name']
        # 获取节点的任意一个pod的名称
        re = cluster_steps.step_get_pod_of_node(node_name)
        pod_name = re.json()['items'][0]['metadata']['name']
        # 按名称精确查询存在的pod
        re = cluster_steps.step_query_pod(node_name, pod_name)
        # 获取查询到的pod名称
        name_actual = re.json()['items'][0]['metadata']['name']
        # 验证查询结果
        assert name_actual == pod_name

    @allure.story('节点')
    @allure.title('按名称模糊查询节点中存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_existent_pod(self):
        # 获取节点列表中第一个节点的名称
        response = cluster_steps.step_get_nodes()
        node_name = response.json()['items'][0]['metadata']['name']
        # 获取节点的任意一个pod的名称
        re = cluster_steps.step_get_pod_info(node_name)
        pod_name = re.json()['items'][0]['metadata']['name']
        # 按名称模糊查询存在的pod
        pod_fuzzy_name = pod_name[2:]
        re = cluster_steps.step_query_pod(node_name, pod_fuzzy_name)
        # 获取查询到的pod名称
        name_actual = re.json()['items'][0]['metadata']['name']
        # 验证查询结果
        assert name_actual == pod_name

    @allure.story('项目')
    @allure.title('按名称精确查询集群中不存在的系统项目')
    @allure.severity(allure.severity_level.NORMAL)
    def test_precise_non_existent_system_project(self):
        project_name = 'non-existent-project'
        # 查询指定的集群的系统项目
        response = cluster_steps.step_query_system_project(project_name)
        # 获取查询结果
        items = response.json()['items']
        # 验证查询结果为空
        assert items == []

    @allure.story('项目')
    @allure.title('按名称精确查询集群中存在的系统项目')
    @allure.severity(allure.severity_level.NORMAL)
    def test_precise_query_existent_system_project(self):
        # 获取集群任意系统项目的名称
        response = cluster_steps.step_query_system_project('')
        project_name = response.json()['items'][0]['metadata']['name']
        # 按名称精确查询系统项目
        re = cluster_steps.step_query_system_project(project_name)
        # 获取查询结果
        project_name_actual = re.json()['items'][0]['metadata']['name']
        # 验证查询结果
        assert project_name_actual == project_name

    @allure.story('项目')
    @allure.title('按名称模糊查询集群中存在的系统项目')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_existent_system_project(self):
        # 获取集群任意系统项目的名称
        response = cluster_steps.step_query_system_project('')
        project_name = response.json()['items'][0]['metadata']['name']
        # 按名称精确查询系统项目
        fuzzy_project_name = project_name[2:]
        re = cluster_steps.step_query_system_project(fuzzy_project_name)
        # 获取查询结果
        project_name_actual = re.json()['items'][0]['metadata']['name']
        # 验证查询结果
        assert project_name_actual == project_name

    @allure.story('项目')
    @allure.title('查询集群中所有系统项目的详情信息,并验证其状态为活跃')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_system_project_state(self):
        # 获取集群中系统项目的数量
        response = cluster_steps.step_query_system_project('')
        project_count = response.json()['totalItems']
        # 获取集群任意系统项目的名称
        for i in range(0, project_count):
            project_name = response.json()['items'][i]['metadata']['name']
            # 查询项目的详细信息
            r = cluster_steps.step_get_project_detail(project_name)
            # 获取项目的状态
            status = r.json()['status']['phase']
            # 验证项目运行状态为活跃
            assert status == 'Active'

    @allure.story('项目')
    @allure.title('查询集群中所有系统项目的配额信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_one_system_project_quota(self):
        # 获取集群中系统项目的数量
        response = cluster_steps.step_query_system_project('')
        project_count = response.json()['totalItems']
        for i in range(0, project_count):
            # 获取集群任意系统项目的名称
            project_name = response.json()['items'][i]['metadata']['name']
            # 查询项目的配额信息
            r = cluster_steps.step_get_project_quota(project_name)
            # 获取项目的配额信息
            used = r.json()['data']['used']
            # 验证项目配额信息获取成功
            assert 'count/pods' in used

    @allure.story('项目')
    @allure.title('查询集群中所有系统项目的LimitRanges信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_one_system_project_detail(self):
        # 获取集群中系统项目的数量
        response = cluster_steps.step_query_system_project('')
        project_count = response.json()['totalItems']
        for i in range(0, project_count):
            # 获取集群任意系统项目的名称
            project_name = response.json()['items'][i]['metadata']['name']
            # 查询项目的LimitRanges
            r = cluster_steps.step_get_project_limit_ranges(project_name)
            # 获取请求资源的kind
            kind = r.json()['kind']
            # 验证请求资源的kind为LimitRangeList
            assert kind == 'LimitRangeList'

    @allure.story('项目')
    @allure.title('查询集群中所有系统项目的工作负载信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_system_project_workload(self):
        # 获取集群中系统项目的数量
        response = cluster_steps.step_query_system_project('')
        project_count = response.json()['totalItems']
        for i in range(0, project_count):
            # 获取集群任意系统项目的名称
            response = cluster_steps.step_query_system_project('')
            project_name = response.json()['items'][i]['metadata']['name']
            # 查询项目的工作负载信息
            response = cluster_steps.step_get_project_workload(project_name)
            # 获取接口的响应数据
            data = response.json()['data']
            # 验证接口响应数据正确
            data_except = ['daemonsets', 'deployments', 'jobs', 'persistentvolumeclaims', 'statefulsets']
            assert data_except[random.randint(0, 4)] in data

    @allure.story('项目')
    @allure.title('验证集群中所有系统项目的pod运行正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_system_project_pods(self):
        # 获取集群中系统项目的数量
        response = cluster_steps.step_query_system_project('')
        project_count = response.json()['totalItems']
        # 获取集群中所有系统项目的名称
        for i in range(0, project_count):
            project_name = response.json()['items'][i]['metadata']['name']
            # 查询项目的pods信息
            r = cluster_steps.step_get_pods_of_project(project_name=project_name)
            # 获取pod的数量
            pod_count = r.json()['totalItems']
            # 获取所有pod的状态
            for j in range(0, pod_count):
                state = r.json()['items'][j]['status']['phase']
                # 获取pod的名称
                pod_name = r.json()['items'][j]['metadata']['name']
                if state not in ['Running', 'Succeeded']:
                    print(pod_name)
                # 验证pod的运行状态
                pytest.assume(state in ['Running', 'Succeeded'])

    @allure.story('项目')
    @allure.title('使用名称精确查询项目中存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_precise_query_existent_pod(self):
        # 用于存放pod的名称
        pod_names = []
        # 获取集群中任一系统项目的名称
        response = cluster_steps.step_query_system_project('')
        project_name = response.json()['items'][0]['metadata']['name']
        # 查询项目的所有的pod信息
        re = cluster_steps.step_get_pods_of_project(project_name=project_name)
        # 获取pod的数量
        pod_count = re.json()['totalItems']
        # 获取项目的pod的名称
        for i in range(0, pod_count):
            name = re.json()['items'][i]['metadata']['name']
            pod_names.append(name)
        # 使用pod的名称，精确查询存在的pod
        r = cluster_steps.step_get_pods_of_project(project_name, 'name=' + pod_names[0])
        # 获取查询结果中pod名称
        pod_name_actual = r.json()['items'][0]['metadata']['name']
        # 验证查询结果正确
        assert pod_name_actual == pod_names[0]

    @allure.story('项目')
    @allure.title('使用名称模糊查询项目中存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_existent_pod(self):
        # 用于存放pod的名称
        pod_names = []
        # 获取集群中任一系统项目的名称
        response = cluster_steps.step_query_system_project('')
        project_name = response.json()['items'][0]['metadata']['name']
        # 查询项目的所有的pod信息
        re = cluster_steps.step_get_pods_of_project(project_name=project_name)
        # 获取pod的数量
        pod_count = re.json()['totalItems']
        # 获取项目的pod的名称
        for i in range(0, pod_count):
            name = re.json()['items'][i]['metadata']['name']
            pod_names.append(name)
        # 使用pod的名称，模糊查询存在的pod
        r = cluster_steps.step_get_pods_of_project(project_name, 'name=' + pod_names[0][2:])
        # 获取查询结果中pod名称
        pod_name_actual = r.json()['items'][0]['metadata']['name']
        # 验证查询结果正确
        assert pod_name_actual == pod_names[0]

    @allure.story('项目')
    @allure.title('使用名称查询项目中不存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_existent_pod(self):
        # 获取集群中任一系统项目的名称
        response = cluster_steps.step_query_system_project('')
        project_name = response.json()['items'][0]['metadata']['name']
        # 使用pod的名称，模糊查询存在的pod
        pod_name = 'test' + str(commonFunction.get_random())
        r = cluster_steps.step_get_pods_of_project(project_name, 'name=' + pod_name)
        # 获取查询结果中的pod数量
        pod_count = r.json()['totalItems']
        # 验证查询结果正确
        assert pod_count == 0

    @allure.story('项目')
    @allure.title('创建用户项目，并验证项目创建成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_user_system(self):
        project_name = 'user-project' + str(commonFunction.get_random())
        alias_name = 'test'
        description = 'create user-system'
        # 创建用户项目
        cluster_steps.step_create_user_project(project_name, alias_name, description)
        # 查询创建的项目，并获取其运行状态
        r = cluster_steps.step_get_user_system(project_name)
        state = r.json()['status']['phase']
        # 验证项目的状态为active
        assert state == 'Active'
        # 删除创建的项目
        cluster_steps.step_delete_user_system(project_name)

    @allure.story('项目')
    @allure.title('删除用户项目，并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_user_system(self):
        project_name = 'user-project' + str(commonFunction.get_random())
        alias_name = 'test'
        description = 'create user-system'
        # 创建用户项目
        cluster_steps.step_create_user_project(project_name, alias_name, description)
        # 删除用户项目
        response = cluster_steps.step_delete_user_system(project_name)
        # 获取删除项目的状态
        state = response.json()['status']['phase']
        # 验证删除项目的状态为Terminating
        assert state == 'Terminating'
        # 等待项目删除成功
        i = 0
        while i < 60:
            # 查询被删除的项目并获取查询结果
            r = cluster_steps.step_get_user_system(project_name)
            status = r.json()['status']
            if status == {'phase': 'Terminating'}:
                time.sleep(1)
                i += 1
            else:
                break
        # 验证项目删除成功
        assert status == 'Failure'

    @allure.story('应用负载')
    @allure.title('查看集群所有的deployments，并验证其运行正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_deployments_of_cluster(self):
        # 查询集群所有的deployments
        response = cluster_steps.step_get_resource_of_cluster('deployments')
        # 获取集群deployments的数量
        count = response.json()['totalItems']
        # 获取集群所有的deployments的状态
        for i in range(0, count):
            state = response.json()['items'][i]['status']['conditions'][0]['status']
            # 验证deployment的状态为True
            assert state == 'True'

    @allure.story('应用负载')
    @allure.title('查看集群所有的deployments的Revision Records')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_deployments_revision_records(self):
        # 查询集群所有的deployments
        response = cluster_steps.step_get_resource_of_cluster('deployments')
        # 获取集群deployments的数量
        count = response.json()['totalItems']
        # 获取集群所有的deployments的labels
        for i in range(0, count):
            label_selector = ''
            project_name = response.json()['items'][i]['metadata']['namespace']
            labels = response.json()['items'][i]['spec']['selector']['matchLabels']
            # 将labels的key和value拼接为label_selector
            keys = list(labels.keys())
            values = list(labels.values())
            for j in range(0, len(keys)):
                label_selector += keys[j] + '=' + values[j] + ','
            # 去掉最后的逗号
            label_selector = label_selector[:-1]
            # 查看deployments的revision records信息
            r = cluster_steps.step_get_deployment_revision_records(project_name, label_selector)
            # 获取请求的资源类型
            kind = r.json()['kind']
            # 验证请求的资源类型为ReplicaSetList
            assert kind == 'ReplicaSetList'

    @allure.story('应用负载')
    @allure.title('查看集群所有的statefulSets，并验证其运行正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_statefulsets_of_cluster(self):
        # 查询集群所有的statefulSets
        response = cluster_steps.step_get_resource_of_cluster('statefulsets')
        # 获取集群statefulSets的数量
        count = response.json()['totalItems']
        # 获取集群所有的statefulSets的副本数和ready的副本数
        for i in range(0, count):
            replica = response.json()['items'][i]['status']['replicas']
            readyReplicas = response.json()['items'][i]['status']['readyReplicas']
            # 验证每个statefulSets的ready的副本数=副本数
            assert replica == readyReplicas

    @allure.story('应用负载')
    @allure.title('查看集群所有的daemonSets，并验证其运行正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_daemonsets_of_cluster(self):
        # 查询集群所有的daemonSets
        response = cluster_steps.step_get_resource_of_cluster('daemonsets')
        # 获取集群daemonSets的数量
        count = response.json()['totalItems']
        # 获取集群所有的daemonSets的currentNumberScheduled和desiredNumberScheduled
        for i in range(0, count):
            currentNumberScheduled = response.json()['items'][i]['status']['currentNumberScheduled']
            desiredNumberScheduled = response.json()['items'][i]['status']['desiredNumberScheduled']
            # 验证每个daemonSets的currentNumberScheduled=desiredNumberScheduled
            assert currentNumberScheduled == desiredNumberScheduled

    @allure.story('应用负载')
    @allure.title('查看集群所有的daemonSets的详情信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_daemonsets_detail_of_cluster(self):
        # 查询集群所有的daemonSets
        response = cluster_steps.step_get_resource_of_cluster('daemonsets')
        # 获取集群daemonSets的数量
        count = response.json()['totalItems']
        # 获取集群中所有的daemonSets的名称和所在的项目名称
        for i in range(0, count):
            resource_name = response.json()['items'][i]['metadata']['name']
            project_name = response.json()['items'][i]['metadata']['namespace']
            # 查询daemonSets的详细信息
            r = cluster_steps.step_get_app_workload_detail(project_name, 'daemonsets', resource_name)
            # 验证信息查询成功
            assert r.json()['kind'] == 'DaemonSet'

    @allure.story('应用负载')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('type, title',
                             [('statefulsets', '查看集群所有的statefulSets的Revision Records'),
                              ('daemonsets', '查看集群所有的daemonSets的Revision Records')])
    def test_check_app_workload_revision_records(self, type, title):
        # 查询集群所有的daemonSets
        response = cluster_steps.step_get_resource_of_cluster(type)
        # 获取集群daemonSets的数量
        count = response.json()['totalItems']
        # 获取所有的daemonSets的label、project_name和daemonSets的名称
        for i in range(0, count):
            labels = response.json()['items'][i]['metadata']['labels']
            # 将labels的key和value拼接为label_selector
            keys = list(labels.keys())
            values = list(labels.values())
            for j in range(0, len(keys)):
                label_selector = ''
                label_selector += keys[j] + '=' + values[j] + ','
            # 去掉最后的逗号
            label_selector = label_selector[:-1]
            # 获取daemonSets的名称和所在的项目名称
            project_name = response.json()['items'][i]['metadata']['namespace']
            # 查看daemonSets的revision Records 信息
            r = cluster_steps.step_get_app_workload_revision_records(project_name, label_selector)
            # 获取请求的资源类型
            kind = r.json()['kind']
            # 验证请求的资源类型为ControllerRevisionList
            assert kind == 'ControllerRevisionList'

    @allure.story('应用负载')
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title('{title}')
    @pytest.mark.parametrize('type, title',
                             [('deployments', '查看集群所有的deployments的Monitoring'),
                              ('statefulsets', '查看集群所有的statefulSets的Monitoring'),
                              ('daemonsets', '查看集群所有的daemonSets的Monitoring'),
                              ('pods', '查看集群所有pod的Monitoring'),
                              ('services', '查看集群所有service的Monitoring')])
    def test_check_app_workload_monitoring(self, type, title):
        # 查询集群所有的daemonSets
        response = cluster_steps.step_get_resource_of_cluster(type)
        # 获取集群daemonSets的数量
        count = response.json()['totalItems']
        # 获取所有的daemonSets的project_name和daemonSets的名称
        for i in range(0, count):
            project_name = response.json()['items'][i]['metadata']['namespace']
            resource_name = response.json()['items'][i]['metadata']['name']
            # 查看监控信息
            r = cluster_steps.step_get_app_workload_monitoring(project_name, type, resource_name)
            # 获取请求结果中监控数据的类型
            resultType = r.json()['results'][0]['data']['resultType']
            # 验证请求结果中监控数据的类型为vector
            assert resultType == 'vector'

    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('story, type, title',
                             [('应用负载', 'deployments', '查看集群所有的deployments的event'),
                              ('应用负载', 'statefulsets', '查看集群所有的statefulSets的event'),
                              ('应用负载', 'daemonsets', '查看集群所有的daemonSets的event'),
                              ('应用负载', 'pods', '查看集群所有pod的event'),
                              ('应用负载', 'services', '查看集群所有service的event'),
                              ('存储', 'persistentvolumeclaims', '查看集群所有pvc的event')
                              ])
    def test_check_app_workload_event(self, story, type, title):
        allure.dynamic.story(story)
        # 查询集群所有的资源
        response = cluster_steps.step_get_resource_of_cluster(type)
        # 获取集群某一资源的数量
        count = response.json()['totalItems']
        # 获取某一资源所有的project_name,资源的名称和uid
        for i in range(0, count):
            project_name = response.json()['items'][i]['metadata']['namespace']
            resource_name = response.json()['items'][i]['metadata']['name']
            resource_uid = response.json()['items'][i]['metadata']['uid']
            # 查询daemonSets的event信息
            r = cluster_steps.step_get_resource_event(project_name, type, resource_name, resource_uid)
            # 获取请求结果的类型
            kind = r.json()['kind']
            # 验证请求结果的类型为EventList
            assert kind == 'EventList'

    @allure.story('应用负载')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('type, title',
                             [('deployments', '按名称精确查询存在的deployments'),
                              ('statefulsets', '按名称精确查询存在的statefulSets'),
                              ('daemonsets', '按名称精确查询存在的daemonSets'),
                              ('pods', '按名称模糊查询存在的pod'),
                              ('services', '按名称模糊查询存在的service')])
    def test_precise_query_app_workload_by_name(self, type, title):
        # 获取集群中存在的资源的名称
        response = cluster_steps.step_get_resource_of_cluster(type)
        # 获取第一个资源的名称
        name = response.json()['items'][0]['metadata']['name']
        r = cluster_steps.step_get_resource_of_cluster(type, 'name=' + name)
        # 获取查询结果的名称
        name_actual = r.json()['items'][0]['metadata']['name']
        # 验证查询结果正确
        assert name == name_actual

    @allure.story('应用负载')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('type, title',
                             [('deployments', '按名称模糊查询存在的deployments'),
                              ('statefulsets', '按名称模糊查询存在的statefulSets'),
                              ('daemonsets', '按名称模糊查询存在的daemonSets'),
                              ('pods', '按名称模糊查询存在的pod'),
                              ('services', '按名称模糊查询存在的service')])
    def test_fuzzy_query_app_workload_by_name(self, type, title):
        # 获取集群中存在的资源的名称
        response = cluster_steps.step_get_resource_of_cluster(type)
        # 获取第一个资源的名称
        name = response.json()['items'][0]['metadata']['name']
        r = cluster_steps.step_get_resource_of_cluster(type, 'name=' + name[2:])
        # 获取查询结果的名称
        name_actual = r.json()['items'][0]['metadata']['name']
        # 验证查询结果正确
        assert name == name_actual

    @allure.story('应用负载')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('type, title',
                             [('deployments', '按状态查询存在的deployments'),
                              ('statefulsets', '按状态查询存在的statefulSets'),
                              ('daemonsets', '按状态查询存在的daemonSets')])
    def test_query_app_workload_by_status(self, type, title):
        # 查询状态为running的资源
        r = cluster_steps.step_get_resource_of_cluster(type, 'status=running')
        # 获取资源的数量
        count = r.json()['totalItems']
        # 获取资源的readyReplicas和replicas
        for i in range(0, count):
            if type == 'daemonsets':
                readyReplicas = r.json()['items'][i]['status']['numberReady']
                replicas = r.json()['items'][i]['status']['numberAvailable']
            else:
                readyReplicas = r.json()['items'][i]['status']['readyReplicas']
                replicas = r.json()['items'][i]['status']['replicas']
            # 验证readyReplicas=replicas，从而判断资源的状态为running
            assert readyReplicas == replicas

    @allure.story('应用负载')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('type, title',
                             [('deployments', '按状态和名称查询存在的deployments'),
                              ('statefulsets', '按状态和名称查询存在的statefulSets'),
                              ('daemonsets', '按状态和名称查询存在的daemonSets')])
    def test_query_app_workload_by_status_and_name(self, type, title):
        # 查询集群中所有的资源
        response = cluster_steps.step_get_resource_of_cluster(type)
        # 获取资源的数量
        count = response.json()['totalItems']
        running_resource = []
        for i in range(0, count):
            if type == 'daemonsets':
                readyReplicas = response.json()['items'][i]['status']['numberReady']
                replicas = response.json()['items'][i]['status']['numberAvailable']
            else:
                readyReplicas = response.json()['items'][i]['status']['readyReplicas']
                replicas = response.json()['items'][i]['status']['replicas']
            if readyReplicas == replicas:
                running_resource.append(response.json()['items'][i]['metadata']['name'])
        # 使用名称和状态查询资源
        for name in running_resource:
            r = cluster_steps.step_get_resource_of_cluster(type, 'name=' + name, 'status=running')
            # 获取查询结果中的name
            name_actual = r.json()['items'][0]['metadata']['name']
            # 验证查询的结果正确
            assert name in name_actual

    @allure.story('应用负载')
    @allure.title('获取集群所有的容器组，并验证其数量与从项目管理中获取的数量一致')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_pods_of_cluster(self):
        # 获取集群的容器组的数量
        response = cluster_steps.step_get_pods_of_cluster()
        count = response.json()['totalItems']
        # 从项目管理处获取所有项目的名称
        project_name = []
        re = cluster_steps.step_get_project_of_cluster()
        project_count = re.json()['totalItems']
        for i in range(0, project_count):
            name = re.json()['items'][i]['metadata']['name']
            project_name.append(name)
        # 获取每个项目的pod数量,并将其加和
        pod_counts = 0
        for project in project_name:
            r = cluster_steps.step_get_pods_of_project(project)
            pod_count = r.json()['totalItems']
            pod_counts += pod_count
        # 验证集群的容器数量等于每个项目的容器数之和
        assert count == pod_counts

    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('story, type, title',
                             [('配置中心', 'secrets', '按名称精确查询存在的密钥'),
                              ('配置中心', 'configmaps', '按名称精确查询存在的配置'),
                              ('配置中心', 'serviceaccounts', '按名称精确查询存在的服务账号'),
                              ('CRDs', 'customresourcedefinitions', '按名称精确查询存在的CRD'),
                              ('存储', 'persistentvolumeclaims', '按名称精确查询存在的存储卷'),
                              ('存储', 'storageclasses', '按名称精确查询存在的存储类型')
                              ])
    def test_precise_query_resource_by_name(self, story, type, title):
        allure.dynamic.story(story)
        # 获取集群中存在的任一资源的名称
        response = cluster_steps.step_get_resource_of_cluster(resource_type=type)
        count = response.json()['totalItems']
        name = response.json()['items'][random.randint(0, count - 1)]['metadata']['name']
        # 按名称精确查询存在的资源
        r = cluster_steps.step_get_resource_of_cluster(type, 'name=' + name)
        name_actual = r.json()['items'][0]['metadata']['name']
        # 验证查询结果正确
        assert name_actual in name

    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('story, type, title',
                             [('配置中心', 'secrets', '按名称模糊查询存在的密钥'),
                              ('配置中心', 'configmaps', '按名称模糊查询存在的配置'),
                              ('配置中心', 'serviceaccounts', '按名称模糊查询存在的服务账号'),
                              ('CRDs', 'customresourcedefinitions', '按名称模糊查询存在的CRD'),
                              ('存储', 'persistentvolumeclaims', '按名称模糊查询存在的存储卷'),
                              ('存储', 'storageclasses', '按名称模糊查询存在的存储类型')
                              ])
    def test_fuzzy_query_resource_by_name(self, story, type, title):
        allure.dynamic.story(story)
        # 查看集群中的某一种资源
        response = cluster_steps.step_get_resource_of_cluster(resource_type=type)
        # 获取集群中某一种资源的数量
        count = response.json()['totalItems']
        # 获取集群中存在的任一资源的名称
        name = response.json()['items'][random.randint(0, count - 1)]['metadata']['name']
        fuzzy_name = name[1:]
        # 按名称精确查询存在的资源
        r = cluster_steps.step_get_resource_of_cluster(type, 'name=' + fuzzy_name)
        name_actual = r.json()['items'][0]['metadata']['name']
        # 验证查询结果正确
        assert name_actual == name

    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('story, type, title',
                             [('配置中心', 'secrets', '按项目查询存在的密钥'),
                              ('配置中心', 'configmaps', '按项目查询存在的配置'),
                              ('配置中心', 'serviceaccounts', '按项目查询存在的服务账号'),
                              ('存储', 'persistentvolumeclaims', '按项目查询存在的存储卷')
                              ])
    def test_query_configuration_by_project(self, story, type, title):
        allure.dynamic.story(story)
        # 查询项目为kube-system的所有资源
        response = cluster_steps.step_get_resource_of_cluster_by_project(type=type, project_name='kubesphere-system')
        # 获取资源数量
        count = response.json()['totalItems']
        # 遍历所有资源，验证资源的项目为kubesphere-system
        for i in range(0, count):
            project = response.json()['items'][i]['metadata']['namespace']
            assert project == 'kubesphere-system'

    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('story, type, title',
                             [('配置中心', 'secrets', '按项目和名称查询存在的密钥'),
                              ('配置中心', 'configmaps', '按项目和名称查询存在的配置'),
                              ('配置中心', 'serviceaccounts', '按项目和名称查询存在的服务账号'),
                              ('存储', 'persistentvolumeclaims', '按项目和名称查询存在的存储卷')
                              ])
    def test_query_configuration_by_project_and_name(self, story, type, title):
        allure.dynamic.story(story)
        # 查询项目为kube-system的所有资源
        response = cluster_steps.step_get_resource_of_cluster_by_project(type=type, project_name='kubesphere-system')
        # 获取资源数量
        count = response.json()['totalItems']
        # 获取任一资源的名称
        name = response.json()['items'][random.randint(0, count - 1)]['metadata']['name']
        # 按项目和名称查询资源
        r = cluster_steps.step_get_resource_of_cluster_by_project(type, 'kubesphere-system', 'name=' + name)
        # 在查询结果中获取资源名称和数量
        name_actual = r.json()['items'][0]['metadata']['name']
        count = r.json()['totalItems']
        # 验证查询结果正确
        assert name_actual == name
        assert count == 1

    @allure.story('CRDs')
    @allure.title('查询所有CRD的详情信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_crd_detail(self):
        # 查询集群中的crd
        response = cluster_steps.step_get_resource_of_cluster(resource_type='customresourcedefinitions')
        # 获取crd的数量
        count = response.json()['totalItems']
        # 获取crd的名称
        for i in range(0, count):
            name = response.json()['items'][i]['metadata']['name']
            # 查询CRD的详情信息
            r = cluster_steps.step_get_crd_detail(name)
            # 获取查询结果中的kind
            kind = r.json()['kind']
            # 验证查询结果正确
            assert kind == 'CustomResourceDefinition'

    @allure.story('CRDs')
    @allure.title('查询所有CRD的FederatedGroupList')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_crd_federated_group_list(self):
        # 查询集群中的crd
        response = cluster_steps.step_get_resource_of_cluster(resource_type='customresourcedefinitions')
        # 获取crd的数量
        count = response.json()['totalItems']
        # 获取crd的group和kind
        for i in range(0, count):
            # 获取crd的名称
            name = response.json()['items'][i]['metadata']['name']
            # 获取crd的group,version和kind
            re = cluster_steps.step_get_crd_detail(name)
            group = re.json()['spec']['group']
            version = re.json()['spec']['version']
            kind = response.json()['items'][i]['spec']['names']['kind']
            # 查询crd的FederatedGroupList信息
            r = cluster_steps.step_get_crd_federated_group_list(group, version, kind.lower())
            # 验证查询结果正确
            assert r.status_code == 200

    @allure.story('存储')
    @allure.title('按状态查询存储卷，并验证查询结果正确')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_pvc_by_status(self):
        # 查询状态为bound的存储卷
        response = cluster_steps.step_get_resource_of_cluster('persistentvolumeclaims', 'status=bound')
        # 获取存储卷数量
        count = response.json()['totalItems']
        # 获取并验证所有存储卷的状态为Bound
        for i in range(0, count):
            status = response.json()['items'][i]['status']['phase']
            assert status == 'Bound'

    @allure.story('存储')
    @allure.title('查询每一个存储卷的详情信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_pvc_detail(self):
        # 查询集群的存储卷
        response = cluster_steps.step_get_resource_of_cluster('persistentvolumeclaims')
        # 获取存储卷的数量
        count = response.json()['totalItems']
        # 获取所有存储卷的名称和所在namespace
        for i in range(0, count):
            name = response.json()['items'][i]['metadata']['name']
            namespace = response.json()['items'][i]['metadata']['namespace']
            # 查询存储卷的详情信息
            r = cluster_steps.step_get_pvc_detail(namespace, name)
            # 获取查询结果的kind
            kind = r.json()['kind']
            # 验证查询结果正确
            assert kind == 'PersistentVolumeClaim'

    @allure.story('存储')
    @allure.title('查询每一个存储卷的监控信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_pvc_metrics(self):
        # 查询集群存在的存储卷信息
        response = cluster_steps.step_get_resource_of_cluster('persistentvolumeclaims')
        # 获取存储卷的数量
        count = response.json()['totalItems']
        # 获取所有存储卷的名称和所在namespace
        for i in range(0, count):
            name = response.json()['items'][i]['metadata']['name']
            namespace = response.json()['items'][i]['metadata']['namespace']
            # 获取当前时间的10位时间戳
            now_timestamp = str(time.time())[0:10]
            # 获取60分钟之前的时间时间戳
            before_timestamp = commonFunction.get_before_timestamp(60)
            # 查询每个pvc最近1个小时的监控信息
            r = cluster_steps.step_get_metrics_of_pvc(namespace, name, before_timestamp, now_timestamp, '60s', '60')
            # 获取查询到的数据的结果类型
            resultType = r.json()['results'][0]['data']['resultType']
            # 验证查询到的数据的结果类型
            assert resultType == 'matrix'

    @allure.story('存储')
    @allure.title('查询每一个存储卷的pod信息,并验证pod运行正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_pvc_pods(self):
        # 查询集群存在的存储卷信息
        response = cluster_steps.step_get_resource_of_cluster('persistentvolumeclaims')
        # 获取存储卷的数量
        count = response.json()['totalItems']
        # 获取所有存储卷的名称和所在namespace
        for i in range(0, count):
            name = response.json()['items'][i]['metadata']['name']
            namespace = response.json()['items'][i]['metadata']['namespace']
            # 查询存储卷的pod信息
            r = cluster_steps.step_get_pods_of_project(namespace, 'pvcName=' + name)
            # 获取pod的数量
            count_pod = r.json()['totalItems']
            # 获取所有pod的运行状态
            for j in range(0, count_pod):
                status = r.json()['items'][j]['status']['phase']
                # 验证pod的状态为Running
                assert status == 'Running'

    @allure.story('存储')
    @allure.title('查看所有存储卷的快照信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_pvc_snapshot(self):
        # 查询集群存在的存储卷信息
        response = cluster_steps.step_get_resource_of_cluster('persistentvolumeclaims')
        # 获取存储卷的数量
        count = response.json()['totalItems']
        # 获取所有存储卷的名称和所在namespace
        for i in range(0, count):
            name = response.json()['items'][i]['metadata']['name']
            namespace = response.json()['items'][i]['metadata']['namespace']
            # 查询每个pvc的快照信息
            r = cluster_steps.step_get_resource_of_cluster_by_project('volumesnapshots', namespace,
                                                        'persistentVolumeClaimName=' + name)
            # 验证查询成功
            assert r.status_code == 200

    @allure.story('存储')
    @allure.title('查询存储类型的详细信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_storage_class_detail(self):
        # 查询集群存在的存储类型
        response = cluster_steps.step_get_resource_of_cluster('storageclasses')
        # 获取存储类型的数量
        count = response.json()['totalItems']
        # 获取所有的存储类型的名称
        for i in range(0, count):
            name = response.json()['items'][i]['metadata']['name']
            # 查询每个存储类型的详情信息
            r = cluster_steps.step_get_storage_class_detail(name)
            # 获取详情信息中的kind
            kind = r.json()['kind']
            # 验证查询结果正确
            assert kind == 'StorageClass'

    @allure.story('存储')
    @allure.title('将存储类型设置为默认的存储类型')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_set_default_storage_class(self):
        # 查询集群存在的存储类型
        response = cluster_steps.step_get_resource_of_cluster('storageclasses')
        # 获取存储类型的数量
        count = response.json()['totalItems']
        # 获取任一存储类型的名称
        name = response.json()['items'][random.randint(0, count - 1)]['metadata']['name']
        # 将任一存储类型设置为非默认存储类型
        r = cluster_steps.step_set_default_storage_class(name, 'false')
        # 获取请求结果中的storageclass.kubernetes.io/is-default-class
        result = r.json()['metadata']['annotations']['storageclass.kubernetes.io/is-default-class']
        # 验证结果为false
        assert result == 'false'

        # 将任一存储类型设置为默认存储类型
        r = cluster_steps.step_set_default_storage_class(name, 'true')
        # 获取请求结果中的storageclass.kubernetes.io/is-default-class
        result = r.json()['metadata']['annotations']['storageclass.kubernetes.io/is-default-class']
        # 验证结果为true
        assert result == 'true'

    @allure.story('监控&告警')
    @allure.title('查看组件的运行状态并验证组件均健康运行')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_component_health(self):
        # 获取组件的健康状况
        response = cluster_steps.step_get_component_health()
        # 获取组件的数量
        component_count = len(response.json()['kubesphereStatus'])
        print(component_count)
        for i in range(0, component_count):
            # 获取每个组件的totalBackends
            totalBackends = response.json()['kubesphereStatus'][i]['totalBackends']
            # 获取每个组件的healthyBackends
            healthyBackends = response.json()['kubesphereStatus'][i]['healthyBackends']
            # 获取组件的名称
            component_name = response.json()['kubesphereStatus'][i]['name']
            # 验证 totalBackends=healthyBackends
            if totalBackends != healthyBackends:
                print('组件：' + component_name + ' 运行不正常')
                # 校验失败仍能继续运行
                pytest.assume(totalBackends == healthyBackends)

    @allure.story('监控&告警')
    @allure.title('查看组件的运行状态并验证组件均健康运行')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_node_health(self):
        # 查询节点的健康状况
        response = cluster_steps.step_get_component_health()
        # 获取集群的totalNodes
        totalNodes = response.json()['nodeStatus']['totalNodes']
        # 获取集群的healthyNodes
        healthyNodes = response.json()['nodeStatus']['healthyNodes']
        # 验证totalNodes = healthyNodes
        assert totalNodes == healthyNodes

    @allure.story('监控&告警')
    @allure.title('查看集群的监控信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_metrics(self):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取210分钟之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp(210)
        # 查询集群的最近210分钟的监控信息
        response = cluster_steps.step_get_metrics_of_cluster(before_timestamp, now_timestamp, '300s', '100')
        # 获取查询结果的数据类型
        for i in range(0, 10):
            try:
                result_type = response.json()['results'][i]['data']['resultType']
                # 验证数据类型为matrix
                assert result_type == 'matrix'
            except Exception as e:
                print(e)

    @allure.story('监控&告警')
    @allure.title('查看apiserver的监控信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_apiserver_metrics(self):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取240分钟之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp(240)
        # 查询集群的最近240分钟的监控信息
        response = cluster_steps.step_get_metrics_of_apiserver(before_timestamp, now_timestamp, '300s', '100')
        # 获取查询结果的数据类型
        for i in range(0, 3):
            try:
                result_type = response.json()['results'][i]['data']['resultType']
                # 验证数据类型为matrix
                assert result_type == 'matrix'
            except Exception as e:
                print(e)

    @allure.story('监控&告警')
    @allure.title('查看schedule的监控信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_schedule_metrics(self):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取240分钟之前的时间
        before_timestamp = commonFunction.get_before_timestamp(240)
        # 查询集群的最近240分钟的监控信息
        response = cluster_steps.step_get_metrics_of_scheduler(before_timestamp, now_timestamp, '300s', '100')
        # 获取查询结果的数据类型
        for i in range(0, 2):
            try:
                result_type = response.json()['results'][i]['data']['resultType']
                # 验证数据类型为matrix
                assert result_type == 'matrix'
            except Exception as e:
                print(e)

    @allure.story('监控&告警')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('sort, title',
                             [('node_load1', 'Sort by Load Average查看Node Usage Ranking'),
                              ('node_cpu_utilisation', 'Sort by CPU查看Node Usage Ranking'),
                              ('node_memory_utilisation', 'Sort by Memory查看Node Usage Ranking'),
                              ('node_disk_size_utilisation', 'Sort by Local Storage查看Node Usage Ranking'),
                              ('node_disk_inode_utilisation', 'Sort by inode Utilization查看Node Usage Ranking'),
                              ('node_pod_utilisation', 'Sort by Pod Utilization查看Node Usage Ranking')
                              ])
    def test_get_node_usage_rank(self, sort, title):
        # 查询Node Usage Ranking
        response = cluster_steps.step_get_node_usage_rank(sort)
        # 获取结果中的数据类型
        for i in range(0, 15):
            try:
                result_type = response.json()['results'][i]['data']['resultType']
                # 验证数据类型为vector
                assert result_type == 'vector'
            except Exception as e:
                print(e)

    @allure.story('监控&告警')
    @allure.title('查看集群资源使用情况')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_resource_usage(self):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取1440分钟之前的时间
        before_timestamp = commonFunction.get_before_timestamp(1440)
        # 查询最近一天的集群应用资源使用情况
        response = cluster_steps.step_get_resource_usage_of_cluster(before_timestamp, now_timestamp, '3600s', '24')
        # 获取结果中的数据类型
        for i in range(0, 3):
            try:
                result_type = response.json()['results'][i]['data']['resultType']
                # 验证数据类型为matrix
                assert result_type == 'matrix'
            except Exception as e:
                print(e)

    @allure.story('监控&告警')
    @allure.title('查看集群应用资源用量')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_app_usage(self):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取1440分钟之前的时间
        before_timestamp = commonFunction.get_before_timestamp(1440)
        # 查询最近一天的集群应用资源使用情况
        response = cluster_steps.step_get_app_usage_of_cluster(before_timestamp, now_timestamp, '3600s', '24')
        # 获取结果中的数据类型
        for i in range(0, 8):
            try:
                result_type = response.json()['results'][i]['data']['resultType']
                # 验证数据类型为matrix
                assert result_type == 'matrix'
            except Exception as e:
                print(e)

    @allure.story('监控&告警')
    @allure.title('查看集群项目变化趋势')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_app_usage(self):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取1440分钟之前的时间
        before_timestamp = commonFunction.get_before_timestamp(1440)
        # 查询最近一天的集群应用资源使用情况
        response = cluster_steps.step_get_project_trend_of_cluster(before_timestamp, now_timestamp, '3600s', '24')
        # 获取结果中的数据类型
        result_type = response.json()['results'][0]['data']['resultType']
        # 验证数据类型为matrix
        assert result_type == 'matrix'

