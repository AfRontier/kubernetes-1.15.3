# 1. just try for current bash
```
export PS1='\[\e]0;\a\]\n\[\e[1;32m\]\[\e[1;34m\]\H\[\e[1;36m\]<$(date +"%Y-%m-%d %T")> \[\e[32m\]\w\[\e[0m\]\n\u>\$ '
```

# 2. for yourself
```
echo "PS1='\[\e]0;\a\]\n\[\e[1;32m\]\[\e[1;34m\]\H\[\e[1;36m\]<$(date +"%Y-%m-%d %T")> \[\e[32m\]\w\[\e[0m\]\n\u>\$ '" >> ~/.bashrc
```

# 3. for whole bash
```
echo "PS1='\[\e]0;\a\]\n\[\e[1;32m\]\[\e[1;34m\]\H\[\e[1;36m\]<$(date +"%Y-%m-%d %T")> \[\e[32m\]\w\[\e[0m\]\n\u>\$ '" >> /etc/bashrc
```
