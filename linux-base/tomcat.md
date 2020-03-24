# tomcat不输出catalina.out日志的方法
* tomcat镜像没有 catalina.out的原因是因为启动方式是使用catalina.sh的run命令导致的，直接使用startup.sh就会有新的catalina.out日志(相当于执行catalina.sh start)，但是这样会导致镜像运行时没有守护进程，脚本执行完后直接关掉了容器，所以需要手动写一个脚本

```shell
#!/bin/bash
bash /usr/local/tomcat/bin/startup.sh
tail -f /usr/local/tomcat/logs/catalina.out
```

* 在针对我们的服务，重新写一个Dockerfile，生成catalina.out文件

Dockfile如下
```Dockerfile
from tomcat:8

maintainer "Caiex"

workdir /usr/local/tomcat/
expose 8080

env TZ=Asia/Shanghai

RUN rm -rf /usr/local/tomcat/webapps/*

RUN sed -i 's/0027/0000/g' /usr/local/tomcat/bin/catalina.sh

ADD run.sh  /usr/local/tomcat/bin/run.sh

RUN chmod +x  /usr/local/tomcat/bin/run.sh

ADD target/repo-app-client-1.0.0-SNAPSHOT-dev.war /usr/local/tomcat/webapps/ROOT.war

cmd ["/usr/local/tomcat/bin/run.sh", "start"]

```
