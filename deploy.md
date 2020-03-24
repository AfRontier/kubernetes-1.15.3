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
yum -y install kubelet-1.15.3
yum -y install kubeadm-1.15.3
systemctl enable kubelet  && systemctl start kubelet
```

### 8.拉取kubernetes镜像 分发镜像

```shell
docker pull aiotceo/kube-proxy:v1.15.4
docker pull aiotceo/kube-controller-manager:v1.15.4
docker pull aiotceo/kube-scheduler:v1.15.4
docker pull aiotceo/kube-apiserver:v1.15.4	
docker pull aiotceo/kube-coredns:1.3.1
docker pull aiotceo/kube-etcd:3.3.10
docker pull aiotceo/pause:3.1
docker save  aiotceo/kube-proxy:v1.15.4 -o proxy.tar
docker save  aiotceo/kube-controller-manager:v1.15.4 -o conmanager.tar
docker save  aiotceo/kube-scheduler:v1.15.4 -o scheduler.tar
docker save  aiotceo/kube-apiserver:v1.15.4 -o apiserver.tar
docker save  aiotceo/kube-coredns:1.3.1 -o coredns.tar
docker save  aiotceo/kube-etcd:3.3.10 -o   etcd.tar
docker save aiotceo/pause:3.1 -o  pause.tar
```

### 9.安装配置Haproxy

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
    timeout server          1m
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

### 9.启动kubernetes集群

```shell
cat <<EOF > kubeadm-config.yaml
apiVersion: kubeadm.k8s.io/v1beta2
kind: ClusterConfiguration
kubernetesVersion: 1.15.4
imageRepository: aiotceo
controlPlaneEndpoint: "172.19.0.252:6443"
networking:
  podSubnet: 10.244.0.0/16
EOF
kubeadm init --config=kubeadm-config.yaml --upload-certs
########安装flannel插件
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
########主节点加入命令
kubeadm join 172.19.0.252:6443 --token 5p8dfi.beigq7g6t8bvumpc \
    --discovery-token-ca-cert-hash sha256:7d0be2ebb4e0e007a10ee6d799d40c361449252928ca79101116a7aa08131db1 \
    --control-plane --certificate-key 1c71c4622a77c9fb1046678fa268ca3119e54392488bb8303c49cbd8f8c3c66c
########从节点加入命令
kubeadm join 172.19.0.252:6443 --token 5p8dfi.beigq7g6t8bvumpc \
    --discovery-token-ca-cert-hash sha256:7d0be2ebb4e0e007a10ee6d799d40c361449252928ca79101116a7aa08131db1
```

### 10.master2 master3加入集群

```shell
kubeadm join 172.19.0.252:6443 --token 5p8dfi.beigq7g6t8bvumpc \
    --discovery-token-ca-cert-hash sha256:7d0be2ebb4e0e007a10ee6d799d40c361449252928ca79101116a7aa08131db1 \
    --control-plane --certificate-key 1c71c4622a77c9fb1046678fa268ca3119e54392488bb8303c49cbd8f8c3c66c
```

### 11.node1 node2加入集群

```shell
#######执行 1 2 3 4 5 6 7
kubeadm join 172.19.0.252:6443 --token 5p8dfi.beigq7g6t8bvumpc \
    --discovery-token-ca-cert-hash sha256:7d0be2ebb4e0e007a10ee6d799d40c361449252928ca79101116a7aa08131db1
```

### 12.node1 挂载磁盘

```shell
fdisk -l
fdisk /dev/vdc
mkfs.ext4 /dev/vdc1
blkid
vim /etc/fstab
mount /dev/vdc1 /opt
```

### 13.node1制作nfs共享盘

```shell
####### nfs共享文件
yum -y install nfs-utils rpcbind

systemctl enable rpcbind & systemctl enable nfs-server & systemctl enable nfs-lock & systemctl enable nfs-idmap

systemctl start rpcbind & systemctl start nfs-server & systemctl start nfs-lock & systemctl start nfs-idmap

#######服务端
mkdir /usr/local/MATLAB
chmod -R 777 /usr/local/MATLAB
vim /etc/exports
/usr/local/MATLAB 172.19.0.0/24(rw,sync,no_root_squash)
#######ps：如果是修改文件。则将配置文件中的目录全部重新export一次！无需重启服务。
sudo exportfs -rv
showmount -e

#######客戶端

showmount -e 72.19.0.5

```

### 13.设置master节点不可调度

```shell
kubectl  taint nodes prod19-master001 key=value:NoSchedule
kubectl  taint nodes prod19-master002 key=value:NoSchedule
kubectl  taint nodes prod19-master003 key=value:NoSchedule
```

### 14.创建拉取镜像使用的secret

```shell
kubectl create secret docker-registry dockerhub-key --docker-server=https://registry-vpc.cn-beijing.aliyuncs.com --docker-username=drzhengxin@aliyun.com --docker-password=caiyi2019
```

### 15. node3 node4 node5 制作lvm逻辑卷

```shell
yum -y install lvm2
pvcreate /dev/vdb
pvcreate /dev/vdc
vgcreate LVM /dev/vdb
vgextend LVM /dev/vdc
lvcreate -L 414G -n Data LVM
mkfs.ext4 /dev/LVM/Data
echo "/dev/LVM/Data /opt ext4 defaults 1 1 "  >> /etc/fstab
```

### 16.设置node3 node4 node5

```shell
#######执行 1 2 3 4 5 6 7
kubeadm join 172.19.0.252:6443 --token 5p8dfi.beigq7g6t8bvumpc \
    --discovery-token-ca-cert-hash sha256:7d0be2ebb4e0e007a10ee6d799d40c361449252928ca79101116a7aa08131db1
```

### 17.配置zookeeper

```shell
#######node3上创建pv
mkdir /opt/zk_data
mkdir /opt/zk_data/k8s_pv_zk{1..5}
chmod -R 777 /opt/zk_data
cat <<EOF > /etc/exports
/opt/zk_data/k8s_pv_zk1 172.19.0.0/24(rw,sync,no_root_squash)
/opt/zk_data/k8s_pv_zk2 172.19.0.0/24(rw,sync,no_root_squash)
/opt/zk_data/k8s_pv_zk3 172.19.0.0/24(rw,sync,no_root_squash)
/opt/zk_data/k8s_pv_zk4 172.19.0.0/24(rw,sync,no_root_squash)
/opt/zk_data/k8s_pv_zk5 172.19.0.0/24(rw,sync,no_root_squash)
EOF
```

### 18.配置spidermysql

```shell
#######node5上创建pv
mkdir /opt/spider_mysql
chmod -R 777 /opt/spider_mysql
cat <<EOF > /etc/exports
/opt/spider_mysql 172.19.0.0/24(rw,sync,no_root_squash)
EOF
#######连接数据库增加用户
grant all on *.* to caiex@"%" identified by "12345678";
```

### 19.安全组开放端口

6443

22

### 20.修改docker默认存储路径(应该在docker启动前修改)

```shell
docker info

```

