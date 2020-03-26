from tomcat:8.0-jre8

maintainer "afrontier"

workdir /usr/local/tomcat/

expose 8080

env TZ=Asia/Shanghai

RUN rm -rf /usr/local/tomcat/webapps/*
 
ADD xxxxxx.war /usr/local/tomcat/webapps/ROOT.war

ADD run.sh  /usr/local/tomcat/bin/run.sh

RUN chmod +x  /usr/local/tomcat/bin/run.sh

cmd ["/usr/local/tomcat/bin/run.sh", "start"]
