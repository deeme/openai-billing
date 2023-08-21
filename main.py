from flask import Flask, render_template, request, jsonify
import requests

import json
import datetime
import time


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_sess_key', methods=['POST'])
def get_sess_key():

    try:

        data = request.get_json()
        print(data)
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
                print(f"Account info: {username}----{password}")
                api_prefix = 'https://ai.fakeopen.com'

                data = {
                    'username': username,
                    'password': password,
                    'prompt': 'login',
                }
                time.sleep(0.5)
                resp = requests.post(
                    'https://ai.fakeopen.com/auth/platform/login', data=data)
                result = {}  # Initialize the result dictionary

                if resp.status_code == 200:
                    # print('==================== 以下为账号SESS信息 ====================')
                    data = resp.json()
                    sess_key = data['login_info']['user']['session']['sensitive_id']
                    org_id = data['login_info']['user']['orgs']['data'][0]['id']
                    print(sess_key)
                    headers = {
                        "Authorization": "Bearer " + sess_key,
                        "Content-Type": "application/json"
                    }

                    # print('==================== 判断账号plus信息 ====================')
                    url = '{}/api/models'.format(api_prefix)
                    resp = requests.get(url, headers=headers)
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
                    if resp.status_code == 200:
                        data = resp.json()
                        total = data['hard_limit_usd']
                        account_type = data['plan']['id']
                        account_data = datetime.datetime.utcfromtimestamp(
                            data.get('access_until'))
                        expiry_time = account_data.strftime("%Y-%m-%d")
                        timestamp = int(time.time())
                        keys_access_unitl = data.get('access_until')
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
                        # print(data)
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
                        'is_alive': True,
                        'sess_key': sess_key,
                        'org_id': org_id,
                        'account_type': account_type,
                        'is_plus': is_plus,
                        'is_gpt4': is_gpt4,
                        'total_granted': f"{total:.2f}",
                        'total_used': f"{total_usage:.2f}",
                        'total_available': f"{(total - total_usage):.2f}",
                        'account_expires_at': expiry_time
                    }

                else:
                    err_str = resp.text.replace(
                        '\n', '').replace('\r', '').strip()
                    print('share token failed: {}'.format(err_str))
                    result = {
                        'username': username,
                        'password': password,
                        'is_alive': False,
                        'err_str': err_str,
                        'org_id': None,
                        'account_type': None,
                        'is_plus': None,
                        'is_gpt4': None,
                        'total_granted': None,
                        'total_used': None,
                        'total_available': None,
                        'account_expires_at': None
                    }
                batch_results.append(result)

            results.extend(batch_results)
    except Exception as e:
        print(jsonify({'error': str(e)}))
        # return jsonify({'error': str(e)})

    json_data = json.dumps(results, indent=4)
    print(json_data)
    return json_data


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
