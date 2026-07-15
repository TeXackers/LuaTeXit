cd "tex/staging/$1/" || exit 1

# chmod --quiet -R o+rwx .

# find . ! -name "$1.tex" -type f -exec rm -f {} +

# parse discord emotes as images
if grep -o '<a\?:[a-zA-Z0-9_]\{2,\}:[0-9]\+>' $1.tex >$1.emotes; then
    timeout 20 \
        wget -q -nc -t 1 -- \
            $(sed 's/^.*:\([0-9]\+\)>$/https:\/\/cdn.discordapp.com\/emojis\/\1.png/' $1.emotes)
    sed -i 's/<a\?:\([a-zA-Z0-9_]\{2,\}\):\([0-9]\+\)>/{\\texitemote{\1}{}{\2.png}}/g' $1.tex
fi

timeout --kill-after=1m 15 pdflatex \
    -interaction=nonstopmode -halt-on-error \
    -cnf-line 'opening_any=p' -cnf-line 'openout_any=p' \
    -no-shell-escape "$1.tex" > "$1.log" #2>&1

RET=$?
if [ $RET -eq 0 ];
then
 echo "";
elif [ $RET -eq 124 ] || [ $RET -eq 137 ];
then
    head -n 2 $1.tex > failed.tex
    printf '%s\n' '\usepackage{fontspec}\setmainfont{DIN Condensed}' '\begin{document}' '\MakeUppercase{Недостаточно часов}' '\end{document}' >> failed.tex
    timeout 10 \
        lualatex -no-shell-escape \
            -cnf-line 'opening_any=p' -cnf-line 'openout_any=p' \
            failed.tex >> /dev/null
    cp failed.pdf "$1.pdf"
    if [ ! -f "$1.pdf" ];
    then
        cp ../../failed/1x7.png "$1.png"
        exit 1
    fi
else
    grep -A 6 -m 1 "^!" "$1.log";
fi

if [ ! -f "$1.pdf" ];
then
    head -n 2 $1.tex > failed.tex
    printf '%s\n' '\usepackage{fontspec}\setmainfont{DIN Condensed}' '\begin{document}' '\MakeUppercase{Compilation Failed}' '\end{document}' >> failed.tex
    timeout 5 \
        lualatex -no-shell-escape \
            -cnf-line 'opening_any=p' -cnf-line 'openout_any=p' \
            failed.tex >> /dev/null
    timeout 5 \
        gs -q -dSAFER -dBATCH -dNOPAUSE -sDEVICE=pngalpha -r600 -dDownScaleFactor=1 \
            -sOutputFile=$1.png failed.pdf >> /dev/null
    if [ ! -f $1.png ]; then
        cp "../../failed/1x2.png" $1.png
        exit 1
    fi
  exit 1
fi

timeout 10 gs -q -r600 -sDEVICE=pngalpha -dBATCH -dNOPAUSE -dDownScaleFactor=1 -sOutputFile="$1.png" "$1.pdf" >> /dev/null;

if [ $? -eq 124 ];
then
  # 128
  echo "[E128] Image processing timed out!";
  cp "../../failed/1x8.png" "$1.png"
  exit 1
fi
