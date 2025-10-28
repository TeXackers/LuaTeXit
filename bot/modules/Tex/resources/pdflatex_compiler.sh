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
elif [ $RET -eq 124 ];
then
 echo "[E127] Compilation timed out!";
 # 127
 # cp "../../failed.png" "$1.png"
else
    grep -A 6 -m 1 "^!" "$1.log";
fi

if [ ! -f "$1.pdf" ];
then
  # 122
  # echo "\n[E122]";
  cp "../../failed/1x2.png" "$1.png"
  exit 1
fi

# -density <geometry>: horizontal and vertical density of the image
# -depth <value>: image depth
# -quality <value>: JPEG/MIFF/PNG compression level
# -repage <geometry>: size and location of an image canvas
# -trim: trim image edges
timeout 10 magick convert -density 600 -quality 90 -depth 8 -gamma 2 -fuzz 1% -trim +repage "$1.pdf" -colorspace RGB +profile "icc" PNG64:"$1.png" >> /dev/null;

if [ $? -eq 124 ];
then
  # 128
  echo "[E128] Image processing timed out!";
  cp "../../failed/1x8.png" "$1.png"
  exit 1
fi
