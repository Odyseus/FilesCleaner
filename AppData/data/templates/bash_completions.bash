#!/bin/bash

# It would have been impossible to create this without the following post on Stack Exchange!!!
# https://unix.stackexchange.com/a/55622

type "{executable_name}" &> /dev/null &&
_decide_nospace_{current_date}(){
    if [[ ${1} == "--"*"=" ]] ; then
        type "compopt" &> /dev/null && type "compopt" &> /dev/null && compopt -o nospace
    fi
} &&
__files_cleaner_cli_{current_date}(){
    local cur prev cmd
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Handle --xxxxxx=
    if [[ ${prev} == "--"* && ${cur} == "=" ]] ; then
        compopt -o filenames
        COMPREPLY=(*)
        return 0
    fi

    # Handle --xxxxx=path
    if [[ ${prev} == "=" ]] ; then
        # Unescape space
        cur=${cur//\\ / }
        # Expand tilder to $HOME
        [[ ${cur} == "~/"* ]] && cur=${cur/\~/$HOME}

        # Show completion if path exist (and escape spaces)
        compopt -o filenames
        local files=("${cur}"*)
        [[ -e ${files[0]} ]] && COMPREPLY=( "${files[@]// /\ }" )
        return 0
    fi

    # Completion of commands and "first level options.
    if [[ $COMP_CWORD == 1 ]]; then
        COMPREPLY=( $(compgen -W "del edit generate -h --help --manual --version" -- "${cur}") )
        return 0
    fi

    # Completion of options and sub-commands.
    cmd="${COMP_WORDS[1]}"

    case $cmd in
    "del")
        COMPREPLY=( $(compgen -W "-p --path= -n --negated -g --glob" -- "${cur}") )
        _decide_nospace_{current_date} ${COMPREPLY[0]}
        ;;
    "edit")
        COMPREPLY=( $(compgen -W "-l --line-endings" -- "${cur}") )
        ;;
    "generate")
        COMPREPLY=( $(compgen -W "system_executable" -- "${cur}") )
        ;;
    esac
} &&
complete -F __files_cleaner_cli_{current_date} {executable_name}
