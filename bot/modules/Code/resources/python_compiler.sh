cd "$2/$1/" || exit 1

timeout --kill-after=10s 5s python3 "$1.py" > output.log 2>&1
RET=$?

if [ $RET -eq 124 ]; then
    echo "[Execution timed out.]" >> output.log
fi

tail -c 3800 output.log
printf '__CODE_EXIT_%s__' "$RET"
