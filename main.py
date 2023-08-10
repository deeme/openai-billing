from flask import Flask, render_template, request
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
    data = request.get_json()
    user_data = data.get('userData')
    results = []
    for entry in user_data:
        username, password = entry.split('----')
        print(f"Processed user: {username}----{password}")

        data = {
            'username': username,
            'password': password,
            'prompt': 'login',
        }
        resp = requests.post(
            'https://ai.fakeopen.com/auth/platform/login', data=data)
        if resp.status_code == 200:
            print('==================== 以下为账号SESS信息 ====================')
            data = resp.json()
            sess_key = data['login_info']['user']['session']['sensitive_id']
            org_id = data['login_info']['user']['orgs']['data'][0]['id']
            print(sess_key)

            print('==================== 以下为账号订阅信息 ====================')
            api_prefix = 'https://ai.fakeopen.com'
            headers = {
                "Authorization": "Bearer " + sess_key,
                "Content-Type": "application/json"
            }
            url = '{}/dashboard/billing/subscription'.format(api_prefix)
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                total = data['hard_limit_usd']
                account_type = data['plan']['id']
                print('账号类型:', data['plan']['id'])
                print('是否主账号:', data['primary'])
                print('是否绑卡:', data['has_payment_method'])
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
                billing_response = requests.get(billing_url, headers=headers)
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

            print('==================== 以下为账号GPT信息 ====================')
            url = '{}/dashboard/rate_limits'.format(api_prefix)
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                # text = json.dumps(data, sort_keys=True, indent=4)
                if 'gpt-4' in data:
                    is_gpt4 = True
                else:
                    is_gpt4 = False
            else:
                print('账号频控信息获取失败！\n')

            result = {
                'username': username,
                'password': password,
                'is_alive': True,
                'sess_key': sess_key,
                'org_id': org_id,
                'account_type': account_type,
                'is_gpt4': is_gpt4,
                'total_granted': f"{total:.2f}",
                'total_used': f"{total_usage:.2f}",
                'total_available': f"{(total - total_usage):.2f}",
                'account_expires_at': expiry_time
            }
            results.append(result)

        else:
            err_str = resp.text.replace('\n', '').replace('\r', '').strip()
            print('share token failed: {}'.format(err_str))
            result = {
                'username': username,
                'password': password,
                'is_alive': False,
                'sess_key': None,
                'org_id': None,
                'account_type': None,
                'is_gpt4': None,
                'total_granted': None,
                'total_used': None,
                'total_available': None,
                'account_expires_at': None
            }
            results.append(result)

    json_data = json.dumps(results, indent=4)

    return json_data


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
