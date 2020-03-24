#### 1.下载基础repo文件

```shell
#docker-ce
wget -O /etc/yum.repos.d/docker2.repo  http://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
#centos-7
wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo
#epel
wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/epel-7.repo
#kubernetes
cat <<EOF > /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://mirrors.aliyun.com/kubernetes/yum/repos/kubernetes-el7-x86_64
enabled=1
gpgcheck=0
EOF
#缓存repo
yum makecache
```

#### 2.检查selinux firewalld

```shell
getenforce
#sed -i 's/\=enforcing/\=disabled/' /etc/selinux/config
#reboot
systemctl status firewalld
#systemctl stop firewalld && systemctl disable firewalld
```

#### 3.检查NTP时间同步

```shell
systemctl status chronyd
#yum -y install chrony
#替换ntp时间同步器为阿里云服务器 ntp1.aliyun.com
#systemctl restart chronyd
chronyc sources -v 
```

### 4.配置/etc/hosts解析

```shell
cat << EOF > /etc/hosts
::1	localhost	localhost.localdomain	localhost6	localhost6.localdomain6
127.0.0.1	localhost	localhost.localdomain	localhost4	localhost4.localdomain4

172.19.0.1     master1      master1
172.19.0.2     master2      master2
172.19.0.3     master3      master3
EOF
```

### 5.禁用swap

```shell
swapoff -a
#cat /etc/fstab
#注释swap项 避免重启打开swap
```

### 6.设置路由

```shell
modprobe br_netfilter
cat <<EOF > /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF
sysctl -p /etc/sysctl.d/k8s.conf
```

### 7.安装docker 修改daemon.json 启动docker

```shell
#此处是安装k8s支持的最新版本的docker-ce 无需求可以直接安装docker-ce而不指定版本号
yum -y install docker-ce-cli-18.09.3-3.el7.x86_64
yum -y install docker-ce-18.09.3
#优化docker配置项 避免产生过大的json-file文件
cat > /etc/docker/daemon.json <<EOF
{
  "exec-opts": ["native.cgroupdriver=systemd"],
  "registry-mirrors": [ "https://docker.mirrors.ustc.edu.cn"],
  "log-driver": "json-file",
    "log-opts": {
        "max-size": "50k",
        "max-file": "3"
}
EOF
systemctl enable docker  && systemctl start docker
```

### 8.安装kubeadm和kubelet

```shell
# 分开安装是为了指定版本号
yum -y install kubelet-1.15.4
yum -y install kubeadm-1.15.4
systemctl enable kubelet  && systemctl start kubelet
```

### 9.拉取kubernetes镜像 分发镜像

```shell
#使用阿里云公开镜像仓库 
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/kube-proxy:v1.15.4
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/kube-controller-manager:v1.15.4
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/kube-scheduler:v1.15.4
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/kube-apiserver:v1.15.4	
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/kube-coredns:1.3.1
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/kube-etcd:3.3.10
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/pause:3.1
docker save  registry.cn-hangzhou.aliyuncs.com/google_containers/kube-proxy:v1.15.4 -o proxy.tar
docker save  registry.cn-hangzhou.aliyuncs.com/google_containers/kube-controller-manager:v1.15.4 -o conmanager.tar
docker save  registry.cn-hangzhou.aliyuncs.com/google_containers/kube-scheduler:v1.15.4 -o scheduler.tar
docker save  registry.cn-hangzhou.aliyuncs.com/google_containers/kube-apiserver:v1.15.4 -o apiserver.tar
docker save  registry.cn-hangzhou.aliyuncs.com/google_containers/kube-coredns:1.3.1 -o coredns.tar
docker save  registry.cn-hangzhou.aliyuncs.com/google_containers/kube-etcd:3.3.10 -o   etcd.tar
docker save  registry.cn-hangzhou.aliyuncs.com/google_containers/pause:3.1 -o  pause.tar
```

### 10.使用Haproxy来负载均衡3个master

```shell
yum -y install haproxy
cat  <<EOF > /etc/haproxy/haproxy.cfg
#---------------------------------------------------------------------
# common defaults that all the 'listen' and 'backend' sections will
# use if not designated in their block
#---------------------------------------------------------------------
defaults
    mode                    http
    log                     global
    option                  httplog
    option                  dontlognull
    option http-server-close
    option forwardfor       except 127.0.0.0/8
    option                  redispatch
    retries                 3
    timeout http-request    10s
    timeout queue           1m
    timeout connect         10s
    timeout client          1m  
    timeout server          1m #此项会影响使用kubectl log exec时1分钟退出 适当修改
    timeout http-keep-alive 10s
    timeout check           10s
    maxconn                 3000

#---------------------------------------------------------------------
# main frontend which proxys to the backends
#---------------------------------------------------------------------
frontend   k8s
    bind *:6443
    mode tcp
    default_backend app

backend app
    mode tcp
    balance     roundrobin
    server  master1 172.19.0.1:6443 check
    server  master2 172.19.0.2:6443 check
    server  master3 172.19.0.3:6443 check
EOF
systemctl enable haproxy
systemctl start haproxy
```

### 11.启动kubernetes集群

```shell
cat <<EOF > kubeadm-config.yaml
apiVersion: kubeadm.k8s.io/v1beta2
kind: ClusterConfiguration
kubernetesVersion: 1.15.4
imageRepository: registry.cn-hangzhou.aliyuncs.com/google_containers
controlPlaneEndpoint: "172.19.0.252:6443"
networking:
  podSubnet: 10.244.0.0/16
EOF
kubeadm init --config=kubeadm-config.yaml --upload-certs
########安装flannel插件
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
########主节点加入命令
kubeadm join 172.19.0.252:6443 --token 5p8dfi.beigq7g6t8bvumpc \
    --discovery-token-ca-cert-hash sha256:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx \
    --control-plane --certificate-key xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
########从节点加入命令
kubeadm join 172.19.0.252:6443 --token 5p8dfi.beigq7g6t8bvumpc \
    --discovery-token-ca-cert-hash sha256:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
