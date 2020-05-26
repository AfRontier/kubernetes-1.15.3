#!/usr/bin/python3
import subprocess
import re
import requests
def send_msg(project, msg):
    url = '*'
    reminders = '*'
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    content = "%s %s 使用过高!" % (project,msg)
    data = {
        "msgtype": "text",  # 发送消息类型为文本
        "at": {
            "atMobiles": reminders,
            "isAtAll": False,   # 不@所有人
        },
        "text": {
            "content": content,   # 消息正文
        }
    }
    r = requests.post(url, data=json.dumps(data), headers=headers)
    return r.json()   # 服务器的返回信息，用于调试
def chu(x,y):
    if y in ['1','2','3','4','5']:
        y = y + '000'
    use = round(int(x)/int(y),2)
    return use
def dingding(project,content):
    token = '*'
    phone = '*'
    subprocess.run('curl -H \"Content-Type: application/json\" -X POST --data \'{\"msgtype\": \"text\", \"text\": {\"content\": \"%s %s!\"}, \"at\": {\"atMobiles\": [%s], \"isAtAll\": false}}\' %s' % (project,content,phone,token), shell=True, stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE)
def memory():
    get_project  = subprocess.run('kubectl top pods | awk \'NR!=1{print $1}\'',shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    project      = get_project.stdout.decode(encoding='UTF-8')
    project_list = re.split('\n',project)
    for i in project_list:
        if not i:
            continue
        get_mem_use = subprocess.run('kubectl top pods %s | awk \'NR==2{print $3}\'' % i,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        mem_use = get_mem_use.stdout.decode(encoding='UTF-8').strip()
        mem_use = re.sub('Mi','',mem_use)
        get_mem_claim = subprocess.run('kubectl describe pods %s  | grep Limits -C 2 | grep memory ' % i,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if get_mem_claim.returncode == 1 :
            continue
        mem_result = get_mem_claim.stdout.decode(encoding='UTF-8').strip()
        mem_result = re.search('\d+',mem_result)
        mem_claim  = mem_result.group()
        #print(i,mem_use,mem_claim)
        mem_per = chu(mem_use,mem_claim)
        if mem_per > 0.85 :
            dingding(i,"内存使用率大于85%")
def cpu():
    get_project  = subprocess.run('kubectl top pods | awk \'NR!=1{print $1}\'',shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    project      = get_project.stdout.decode(encoding='UTF-8')
    project_list = re.split('\n',project)
    for i in project_list:
        if not i:
            break
        get_cpu_use = subprocess.run('kubectl top pods %s | awk \'NR==2{print $2}\'' % i,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        cpu_use = get_cpu_use.stdout.decode(encoding='UTF-8').strip()
        cpu_use = re.sub('m','',cpu_use)
        get_cpu_claim = subprocess.run('kubectl describe pods %s  | grep Limits -C 2 | grep cpu ' % i,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if get_cpu_claim.returncode == 1:
            continue
        cpu_result = get_cpu_claim.stdout.decode(encoding='UTF-8').strip()
        cpu_result = re.search('\d+',cpu_result)
        cpu_claim  = cpu_result.group()
        #print(i,cpu_use,cpu_claim)
        cpu_per = chu(cpu_use,cpu_claim)
        if cpu_per > 0.85:
            dingding(i,"cpu使用率大于85%")
        
if __name__ == '__main__':
    cpu()
    memory()
