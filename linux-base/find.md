## 利用stat命令可以看到文件的atime ctime mtime分别是多少

```shell
root># stat a.out 
  File: ‘a.out’
  Size: 133584    	Blocks: 264        IO Block: 4096   regular file
Device: fd11h/64785d	Inode: 1838185     Links: 1
Access: (0644/-rw-r--r--)  Uid: (    0/    root)   Gid: (    0/    root)
Access: 2019-07-24 11:41:25.858787983 +0800    #atime 文件或目录上一次的访问时间
Modify: 2019-07-17 18:21:56.568582066 +0800    #mtime 文件或目录上一次的修改时间，ll命令，输出的即是mtime
Change: 2019-07-17 18:21:56.568582066 +0800    #ctime 文件或目录上一次状态改变的时间，例如属主，属组修改，软连接等
 Birth: -
```

## 利用find命令查找日志

```shell
find / -atime +7   
#查找上一次访问在7天之前的文件
find / -mtime -7
#查看上一次修改在7天之内的文件
find / -atime 7
#查找上一次访问是七天之前当天的
```



