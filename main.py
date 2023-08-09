from flask import Flask, render_template, request
import requests

import json
from datetime import datetime, timedelta


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
        print(f"Processed user: {username}, password: {password}")

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
                text = json.dumps(data, sort_keys=True, indent=4)
                print(text)
                account_type = data['plan']['id']
                # account_primary = data['primary']
                # account_method = data['has_payment_method']
                print('账号类型:', data['plan']['id'])
                print('是否主账号:', data['primary'])
                print('是否绑卡:', data['has_payment_method'])
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

            print('==================== 以下为账号额度信息 ====================')
            url = '{}/dashboard/billing/credit_grants'.format(api_prefix)
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                print(data)
                text = json.dumps(data, sort_keys=True, indent=4)
                total_granted = data['total_granted']
                total_used = data['total_used']
                total_available = data['total_available']

                print('账号额度:', data['total_granted'])
                print('已用额度:', data['total_used'])
                print('账号余额:', data['total_available'])
                if data['grants']['data']:
                    for grant in data['grants']['data']:
                        expires_at = datetime.fromtimestamp(
                            grant['expires_at']) + timedelta(hours=8)  # UTC+8

                        expires_at = expires_at.strftime("%Y-%m-%d")

                        print(
                            '  额度: {}/{}，过期：{}'.format(grant['used_amount'], grant['grant_amount'], expires_at))
                        account_expires_at = expires_at
                        print(account_expires_at, expires_at)
                else:
                    account_expires_at = None
                # verbose and print('账号额度信息:', text)
            else:
                print('账号额度信息获取失败！\n')

            result = {
                'username': username,
                'password': password,
                'is_alive': True,
                'sess_key': sess_key,
                'org_id': org_id,
                'account_type': account_type,
                'is_gpt4': is_gpt4,
                'total_granted': total_granted,
                'total_used': total_used,
                'total_available': total_available,
                'account_expires_at': account_expires_at
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
