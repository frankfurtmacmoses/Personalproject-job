#!/usr/bin/env bash
#######################################################################
# Example of ~/.bashrc for Mac OS X - usage: `source bashrc.sh`
#######################################################################
shopt -s promptvars
echo ""

########################################
# file_name="${file##*.}"
# file_extension="${file%.*}"
script_file="$( readlink "${BASH_SOURCE[0]}" 2>/dev/null || echo ${BASH_SOURCE[0]} )"
script_name="${script_file##*/}"
script_base="$( cd "$( echo "${script_file%/*}/.." )" && pwd )"
script_path="$( cd "$( echo "${script_file%/*}" )" && pwd )"
########################################

# see:
#   - http://omar.io/ps1gen/
#   - https://www.kirsle.net/wizards/ps1.html
#   - https://www.askapache.com/linux/bash-power-prompt/
PS1='\n\[\033[0;36m\]\h\[\033[0m\]:\[\033[0;35m\]\u\[\033[0m\] \W [\#]:\n\$ '
PS1='$(printf "%$((COLUMNS-1))s\r")'$PS1

export JAVA_HOME="${JAVA_HOME:-$(/usr/libexec/java_home)}"
export JAVA_HOME="${JAVA_HOME:-$(type -p javac|xargs readlink -n 2>/dev/null|xargs dirname|xargs dirname)}"
export JAVA_HOME="${JAVA_HOME:-$(type -p javac|xargs dirname|xargs dirname)}"
export GOROOT="${GOROOT:-$(type -p go|xargs readlink -n 2>/dev/null|xargs dirname|xargs dirname)}"
export GOPATH="${HOME}/go"
export MAVEN_HOME="${MAVEN_HOME:-$(mvn -v 2>/dev/null|grep -i 'maven home:'|awk '{print substr($0, index($0,$3))}')}"
export MAVEN_HOME="${MAVEN_HOME:-/opt/apache-maven-3.3.3}"

export HISTCONTROL=ignoredups
export PROMPT_COMMAND='echo -ne "\033]0;${PWD/#$HOME/~}\007"'
# export PATH="$MYSQL_HOME/bin:$MAVEN_HOME/bin"
# export PATH="/Library/PostgreSQL/10/bin:$PATH"
# export PATH="/usr/local/bin:$PATH"
export PATH="$(brew --prefix coreutils)/libexec/gnubin:$PATH"
export PATH="${JAVA_HOME}/bin:$PATH" # Add java
export PATH="${GOPATH}/bin:$PATH" # Add golang


echo "Loading bash aliases ..."
alias a="alias|cut -d' ' -f 2- "
alias bashrc='source ~/.bash_profile; title ${PWD##*/};'
alias brewery='brew update && brew upgrade && brew cleanup'
alias bu='brew upgrade; brew update --debug --verbose'
alias cdp='cd -P .'
alias clean='find . -name \*.pyc -o -name .DS_Store -delete'
alias cls='clear && printf "\e[3J"'
alias dir='ls -al '
alias dsclean='sudo find . -name *.DS_Store -type f -delete'
alias envi='env | grep -i '
alias fixmod='for f in *; do if [[ -d "$f" ]] || [[ "${f##*.}" == "sh" ]]; then chmod 755 "$f"; else chmod 644 "$f"; fi; done'
alias hs='history | grep'
alias ip='echo $(ipconfig getifaddr en0) $(dig +short myip.opendns.com @resolver1.opendns.com)'
alias ll='ls -al'
alias lll='ls -al -T | sort -f -k9,9'  # --time-style=full-iso
alias lln='ls -al | sort -f -k9,9'
alias llt='ls -al -rt'
alias lg='dscl . list /groups | grep -v "_"'
alias lgv='dscacheutil -q group' # -a name staff
alias lsofi='lsof -i -n -P'
alias lports='netstat -vanp tcp|grep -e pid '
alias lu='dscl . list /users | grep -v "_"'
alias luv='dscacheutil -q user' # -a name $USER
alias ml="make -qp|awk -F':' '/^[a-zA-Z0-9][^\$#\/\t=]*:([^=]|\$)/ {split(\$1,A,/ /);for(i in A)print A[i]}'|sort"
alias path='echo $PATH|tr ":" "\n"'
alias setp='(set -o posix; set|grep -v _xspec)'
alias showhidden='defaults write com.apple.finder AppleShowAllFiles YES; killall Finder /System/Library/CoreServices/Finder.app'
alias si='echo -e $(for k in ~/.ssh/*.pub;do echo -e "\\\n$(ssh-keygen -E md5 -lf $k) - $k";done)|sort -k 3; echo;echo "--- Added identities ---"; ssh-add -E md5 -l|sort -k 3'
alias ver='echo -e "$(uname -a)"; echo ""; echo -e "$(bash --version)"'
alias t='title ${PWD##*/}'

# docker-machine
export DOCKER_EMAIL=''
export DOCKER_USERNAME=''
export DOCKER_PASSWORD=''
export GITHUB_USERNAME=''
export GITHUB_PASSWORD=''
export GITHUB_EMAIL=""
export GITHUB_USER=""

echo "Loading bash aliases for docker cli ..."
alias dm="docker-machine "
alias dme="docker-machine env default"
alias dme_disable='eval $(docker-machine env -u)'
alias dme_enable='eval $(docker-machine env)'
alias dmip="docker-machine ip default"
alias dclean='docker kill $(docker ps -aq); docker rm -f -v $(docker ps -aq); docker rmi -f $(docker images -aq)'
alias denv='env|sort|grep DOCKER'
alias di="docker images|sort|grep -v none"
alias dia="docker images -a"
alias didangling="docker images -a --filter dangling=true"
alias diq="docker images -q"
alias dlogs="docker logs -ft "
alias dps="docker ps -a"
alias dpsq="docker ps -q"
alias drm="docker rm -f -v"
alias drma='docker rm -f -v $(docker ps -aq)'
alias drme='docker rm -f -v $(docker ps -aq --filter "status=exited")'
alias drmi='docker rmi -f '
alias dvrm='docker volume rm -f $(docker volume ls -q -f dangling=true)'
alias kc="kubectl"
alias mkenv='eval $(minikube docker-env)'
alias mkenv_disable='eval $(minikube docker-env -u)'
alias mkdb='echo "# run inside debug: apk add curl --no-cache" && kubectl run -i --tty --rm debug --image=alpine --restart=Never -- sh'
alias mk="minikube"

echo "Loading bash aliases for git ..."
alias gbc='git symbolic-ref --short -q HEAD'
alias gbd='git branch -d '  # delete branch locally
alias gbdo='git push origin --delete '  # delete branch on origin
alias gbv="git branch -v "
alias gco="git checkout "
alias gcdev='git checkout master && git pull upstream master && git push && git checkout dev && git rebase master && git push --force && git fetch --v --all --prune ; git branch -v'
alias gfv="git fetch -v --all --prune ; git branch -v"
alias glg="git log --graph --pretty=format:'%C(magenta)%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit --date=relative"
alias gpum='git checkout master && git pull upstream master'
alias gpumgp='git checkout master && git pull upstream master && git push'
alias grm='git rebase master'
alias grmgp='git rebase master && git push'
alias grmgpf='git rebase master && git push --force'
alias grv='git remote -v'
alias gst='git status'

echo "Loading bash aliases for dev ..."
alias apache='httpd -v; sudo apachectl '
alias exif='exiftool -sort -s'
alias ipy='ipython -i --ext=autoreload -c "%autoreload 2"'
alias ipy3='ipython3 -i --ext=autoreload -c "%autoreload 2"'
alias goback='cd ${GOPATH}/$(cut -d/ -f2,3,4 <<< "${PWD/$GOPATH/}")'
alias gopath='cd -P ${GOPATH} && pwd'
alias pipf='pip freeze'
alias pipi='pip install'
alias pipiu='pip install --upgrade'
alias pipl='pip list'
alias pylib='pip show pip | grep Location | awk '\''{print substr($0, index($0,$2))}'\'''
alias pyserver='python -m SimpleHTTPServer'
alias dvenv='deactivate'
alias venv='source .venv/bin/activate'
alias nr="npm run "


############################################################
# function: Main
############################################################
function main() {

  # echo `date +"%Y-%m-%d %H:%M:%S"` "Login to docker with ${DOCKER_USERNAME}..."
  # docker login -u ${DOCKER_USERNAME} -p ${DOCKER_PASSWORD}
  # eval $(minikube docker-env)
  # eval $(docker-machine env)

  find . -name '.DS_Store' -type f -delete 2>/dev/null &

  ipy_autoreload
  fixpath
}

############################################################
# function: Output a relative path to absolute path
############################################################
function abspath() {
  set +u
  local thePath
  if [[ ! "$1" =~ ^/ ]]; then thePath="$PWD/$1"; else thePath="$1"; fi
  echo "$thePath"|(
  IFS=/
  read -a parr
  declare -a outp
  for i in "${parr[@]}";do
    case "$i" in
    ''|.) continue ;;
    ..)
      len=${#outp[@]}
      if ((len!=0));then unset outp[$((len-1))]; else continue; fi
      ;;
    *)
      len=${#outp[@]}
      outp[$len]="$i"
      ;;
    esac
  done
  echo /"${outp[*]}"
  )
  set -u
}

############################################################
# function: Add $1 (a dir path) to $PATH, if not added yet
############################################################
function addtopath() {
    if [ -d "$1" ] && [[ ! "$PATH" =~ (^|:)"${1}"(:|$) ]]; then
      export PATH+=:$1
    fi
}

############################################################
# function: Configure AWS profile
############################################################
function aws_config() {
  local profile=${1:-default}
  echo "Loading/Setting AWS CLI profile: ${profile}"
  local aws_access_key_id="$(aws configure get aws_access_key_id --profile ${profile} 2>/dev/null)"
  local aws_secret_access_key="$(aws configure get aws_secret_access_key --profile ${profile} 2>/dev/null)"
  local aws_default_region="$(aws configure get profile.${profile}.region)"
  local s3_bucket="$(aws configure get profile.${profile}.s3_bucket)"

  if [[ "${aws_access_key_id}" == "" ]]; then
    if [[ "${AWS_ACCESS_KEY_ID}" == "" ]]; then
      echo "ERROR: Environment variable AWS_ACCESS_KEY_ID is not set."
    else
      echo "  - setting aws_access_key_id to default and profile ${profile}"
      aws configure set aws_access_key_id ${AWS_ACCESS_KEY_ID}
      aws configure set aws_access_key_id ${AWS_ACCESS_KEY_ID} --profile ${profile}
    fi
  else
    echo "  - setting environment variable AWS_ACCESS_KEY_ID"
    export AWS_ACCESS_KEY_ID="${aws_access_key_id}"
  fi
  if [[ "${aws_secret_access_key}" == "" ]]; then
    if [[ "${AWS_SECRET_ACCESS_KEY}" == "" ]]; then
      echo "ERROR: Environment variable AWS_SECRET_ACCESS_KEY is not set."
    else
      echo "  - setting aws_secret_access_key to default and profile ${profile}"
      aws configure set aws_secret_access_key ${AWS_SECRET_ACCESS_KEY}
      aws configure set aws_secret_access_key ${AWS_SECRET_ACCESS_KEY} --profile ${profile}
    fi
  else
    echo "  - setting environment variable AWS_SECRET_ACCESS_KEY"
    export AWS_SECRET_ACCESS_KEY="${aws_secret_access_key}"
  fi
  if [[ "${aws_default_region}" == "" ]]; then
    if [[ "${AWS_DEFAULT_REGION}" == "" ]]; then
      echo "ERROR: Environment variable AWS_DEFAULT_REGION is not set."
    else
      echo "  - setting default.region and profile.${profile}.region"
      aws configure set default.region ${AWS_DEFAULT_REGION}
      aws configure set profile.${profile}.region ${AWS_DEFAULT_REGION}
    fi
  else
    echo "  - setting environment variable AWS_DEFAULT_REGION"
    export AWS_DEFAULT_REGION="${aws_default_region}"
  fi
  if [[ "${s3_bucket}" == "" ]]; then
    if [[ "${S3_BUCKET}" == "" ]]; then
      echo "ERROR: Environment variable S3_BUCKET is not set."
    else
      aws configure set default.s3_bucket ${S3_BUCKET}
      aws configure set profile.${profile}.s3_bucket ${S3_BUCKET}
    fi
  else
    export S3_BUCKET="${s3_bucket}"
  fi
}

############################################################
# function: docker inspect extract config in docker image
############################################################
function dex() {
  docker history --no-trunc "$1" | \
  sed -n -e 's,.*/bin/sh -c #(nop) \(MAINTAINER .[^ ]\) 0 B,\1,p' | \
  head -1
  docker inspect --format='{{range $e := .Config.Env}}
  ENV {{$e}}
  {{end}}{{range $e,$v := .Config.ExposedPorts}}
  EXPOSE {{$e}}
  {{end}}{{range $e,$v := .Config.Volumes}}
  VOLUME {{$e}}
  {{end}}{{with .Config.User}}USER {{.}}{{end}}
  {{with .Config.WorkingDir}}WORKDIR {{.}}{{end}}
  {{with .Config.Entrypoint}}ENTRYPOINT {{json .}}{{end}}
  {{with .Config.Cmd}}CMD {{json .}}{{end}}
  {{with .Config.OnBuild}}ONBUILD {{json .}}{{end}}' "$1"
}

############################################################
# function: Extract for common file formats
# -- https://github.com/xvoland/Extract/blob/master/extract.sh
############################################################
function extract() {
  IFS_SAVED=$IFS
  IFS=$(echo -en "\n\b")

  if [ -z "$1" ]; then
    # display usage if no parameters given
    echo "Usage: extract <path/file_name>.<zip|rar|bz2|gz|tar|tbz2|tgz|Z|7z|xz|ex|tar.bz2|tar.gz|tar.xz>"
    echo "       extract <path/file_name_1.ext> [path/file_name_2.ext] [path/file_name_3.ext]"
    return 1
  else
    for n in $@
    do
      if [ -f "$n" ] ; then
          case "${n%,}" in
            *.tar.bz2|*.tar.gz|*.tar.xz|*.tbz2|*.tgz|*.txz|*.tar)
                         tar xvf "$n"       ;;
            *.lzma)      unlzma ./"$n"      ;;
            *.bz2)       bunzip2 ./"$n"     ;;
            *.rar)       unrar x -ad ./"$n" ;;
            *.gz)        gunzip ./"$n"      ;;
            *.zip)       unzip ./"$n"       ;;
            *.z)         uncompress ./"$n"  ;;
            *.7z|*.arj|*.cab|*.chm|*.deb|*.dmg|*.iso|*.lzh|*.msi|*.rpm|*.udf|*.wim|*.xar)
                         7z x ./"$n"        ;;
            *.xz)        unxz ./"$n"        ;;
            *.exe)       cabextract ./"$n"  ;;
            *)
                         echo "extract: '$n' - unknown archive method"
                         return 1
                         ;;
          esac
      else
          echo "'$n' - file does not exist"
          return 1
      fi
    done
  fi

  IFS=$IFS_SAVED
}

############################################################
# function: Print file info
############################################################
function fileinfo() {
  for file in "$@"; do
    path=$(abspath "$file")

    # strip longest match of */ from start
    name="${file##*/}"

    # substring from 0 thru pos of filename
    dir_="${file:0:${#file} - ${#name}}"

    # strip shortest match of . plus at least one non-dot char from end
    base="${name%.[^.]*}"

    # substring from len of base thru end
    ext_="${name:${#base} + 1}"

    size=$((
      du --apparent-size --block-size=1 "$file" 2>/dev/null ||
      gdu --apparent-size --block-size=1 "$file" 2>/dev/null ||
      find "$file" -printf "%s" 2>/dev/null ||
      gfind "$file" -printf "%s" 2>/dev/null ||
      stat --printf="%s" "$file" 2>/dev/null ||
      stat -f%z "$file" 2>/dev/null ||
      wc -c <"$file" 2>/dev/null
    ) | awk '{print $1}')

    # in case of an extension without base, it's really the base
    if [[ -z "$base" && -n "$ext_" ]]; then
      base=".$ext_"
      ext=""
    fi
    if [[ "${dir_}" == "" ]]; then
      dir_=${path%/*}
    fi
    echo -e "------------------------------------------------------------"
    echo -e "\t file : $file"
    echo -e "\t path : $path"
    echo -e "\t  dir : $dir_"
    echo -e "\t base : $base"
    echo -e "\t  ext : $ext_"
    echo -e "\t size : $size"
  done
}

############################################################
# function: Remove duplicates in $PATH variable
############################################################
function fixpath() {
  # remove duplicates in $PATH
  export PATH=$(perl -e 'print join ":", grep {!$h{$_}++} split ":", $ENV{PATH}')
  export PATH=$(printf %s "$PATH" | awk -v RS=: -v ORS=: '!arr[$0]++')
  export PATH=$(printf %s "$PATH" | awk -v RS=: -v ORS=: '{ if (!arr[$0]++) { print $0 } }')
  export PATH=$(printf %s "$PATH" | awk -v RS=: '{ if (!arr[$0]++) {printf("%s%s",!ln++?"":":",$0)}}')
  echo "........................................................................"
  echo $PATH|tr ":" "\n"
  echo "........................................................................"
}

############################################################
# function: Rename git branch name locally and on origin
############################################################
function gb-rename() {
  echo "Fetching git branches ..."
  git fetch -v --all --prune
  echo ""

  local old_name=$1
  local new_name=$2
  # get current branch, optionally using:
  #   - `git branch --no-color | grep -E '^\*' | awk '{print $2}'`
  #   - `git symbolic-ref --short -q HEAD`)
  local current_branch="$(git rev-parse --symbolic-full-name --abbrev-ref HEAD)"
  echo "Current branch: ${current_branch}"
  echo ""

  if [[ "$2" == "" ]]; then
    echo "Missing argument(s) on renaming git branch: "
    echo ""
    echo "${FUNCNAME} old_name new_name"
    echo ""
    return -2
  fi

  if [[ "$1" == "master" ]] || [[ "$2" == "master" ]]; then
    echo "Cannot rename 'master' branch."
    echo ""
    return -1
  fi

  if [[ "$1" == "${current_branch}" ]] || [[ "$2" == "${current_branch}" ]]; then
    echo "Currently on branch [${current_branch}] to be renamed: "
    echo ""
    echo "${FUNCNAME} $1 $2"
    echo ""
    return 9
  fi

  local chk_name=""
  for b in $(git branch --no-color | grep -E '^ '); do
    if [[ "${b}" == "${new_name}" ]]; then
      echo "Branch name [${new_name}] already exists."
      echo ""
      return 2
    fi
    if [[ "${b}" == "${old_name}" ]]; then
      chk_name="${old_name}"
    fi
  done

  if [[ "${chk_name}" == "" ]]; then
    echo "Cannot find branch [${old_name}]. Please fetch and sync to origin."
    echo ""
    return 1
  fi

  git branch -m ${old_name} ${new_name}
  git push origin :${old_name} ${new_name}
  git push origin -u ${new_name}

  echo ""
  echo "Done."
  echo ""
}

############################################################
# function: Delete git branch locally and on origin/remote
############################################################
function gbd-all() {
  if [[ "$1" != "" ]] && [[ "$1" != "master" ]]; then
    git push origin --delete $1
    git branch -d $1
  else
    echo "Missing valid branch name in argument."
    echo ""
  fi
  git fetch --all --prune
  git branch -v
}

############################################################
# function: Find a directory in $GOPATH/src and change to it
############################################################
function goto() {
  cd $(find $GOPATH/src -type d -name "$1" 2>/dev/null | head -n 1); pwd
}

############################################################
# function: Add config for ipython with autoreload extension
############################################################
function ipy_autoreload() {
  echo ""
  local ipy_script="
c.InteractiveShellApp.extensions = ['autoreload']
c.InteractiveShellApp.exec_lines = ['%autoreload 2', 'print("")']
c.InteractiveShellApp.exec_lines.append('print(\"**ATTENTION**: %autoreload 2 enabled.\\n\")')
"
  local ipy_config=".ipython/profile_default/ipython_config.py"
  if [[ ! -e "$HOME/${ipy_config}" ]]; then
    echo "Saving to '~/${ipy_config}' ..."
    echo "${ipy_script}" > "$HOME/${ipy_config}"
  else
    echo "Please configure '~/${ipy_config}' for autoreload in ipython."
  fi
  echo "........................................................................"
  echo "${ipy_script}"
  echo "........................................................................"
  echo ""
}

############################################################
# function: List members for a spcific group
############################################################
function members () {
  dscl . -list /Users | while read user; do printf "$user "; dsmemberutil checkmembership -U "$user" -G "$*"; done | grep "is a member" | cut -d " " -f 1;
}

############################################################
# function: Print info
############################################################
function myinfo () {
  printf "\n"
  printf "CPU   : "
  [[ -e /proc/cpuinfo ]] && cat /proc/cpuinfo 2>/dev/null | grep "model name" | head -1 | awk '{ for (i = 4; i <= NF; i++) printf "%s ", $i }'
  [[ -x "$(which sysctl)" ]] && printf "$(sysctl -n machdep.cpu.brand_string)"
  printf "\n"

  printf "Kernel: $(uname -r) $(uname -p) $(uname -m)"
  kded4 --version 2>/dev/null | grep "KDE Development Platform" | awk '{ printf " | KDE: %s", $4 }'
  printf "\n"
  printf "OS    : $(uname -s)\n"
  # cat /etc/issue 2>/dev/null | awk '{ printf "OS    : %s %s %s %s | " , $1 , $2 , $3 , $4 }'
  printf "Host  : $(uname -n)\n"
  uptime | awk '{ printf "Uptime: %s %s %s", $3, $4, $5 }' | sed 's/,//g'
  printf "\n"
  cputemp 2>/dev/null | head -1 | awk '{ printf "%s %s %s\n", $1, $2, $3 }'
  cputemp 2>/dev/null | tail -1 | awk '{ printf "%s %s %s\n", $1, $2, $3 }'
  cputemp 2>/dev/null | awk '{ printf "%s %s", $1 $2 }'
}

############################################################
# function: Add title to current terminal
############################################################
function title() {
  if [ $# -eq 0 ]; then
    # export PROMPT_COMMAND='echo -ne "\033]0;${PWD/#$HOME/~}\007"'
    export PROMPT_COMMAND='echo -ne "\033]0;${PWD##*/~}\007"'
  else
    TITLE=$*;
    export PROMPT_COMMAND='echo -ne "\033]0;$TITLE\007"'
    # echo -ne "\033]0;"$*"\007"
  fi
}

############################################################
# function: Executes command with a timeout
# Params:
#   $1 timeout in seconds
#   $2 command
# Returns 1 if timed out 0 otherwise
############################################################
function timeout() {
    time=$1
    # start the command in a subshell to avoid problem with pipes
    # (spawn accepts one command)
    command="/bin/sh -c \"$2\""
    expect -c "set echo \"-noecho\"; set timeout $time; spawn -noecho $command; expect timeout { exit 1 } eof { exit 0 }"
    if [ $? = 1 ] ; then
        echo "Timeout after ${time} seconds"
    fi
}



if [[ "$0" == "${BASH_SOURCE}" ]]; then
  echo ""
  echo '.........................................................................'
  echo '!! Please `source` this script in order to export envirnment variables !!'
  exit 9
else
  main $@
fi
