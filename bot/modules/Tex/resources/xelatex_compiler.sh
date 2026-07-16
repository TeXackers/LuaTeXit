cd "$2/$1/" || exit 1

# chmod --quiet -R o+rwx .

# parse discord emotes as images
if grep -o '<a\?:[a-zA-Z0-9_]\{2,\}:[0-9]\+>' $1.tex >$1.emotes; then
    timeout 20 \
        wget -q -nc -t 1 -- \
            $(sed 's/^.*:\([0-9]\+\)>$/https:\/\/cdn.discordapp.com\/emojis\/\1.png/' $1.emotes)
    sed -i 's/<a\?:\([a-zA-Z0-9_]\{2,\}\):\([0-9]\+\)>/{\\texitemote{\1}{}{\2.png}}/g' $1.tex
fi

# compile_start=$(date +%s.%N)
# sudo -u $(whoami) timeout 1m pdflatex $1.tex > texput.log 2>&1
timeout 3m latexmk -xelatex -no-shell-escape -halt-on-error -interaction=nonstopmode "$1.tex" > texput_xetex.log #2>&1
# compile_end=$(date +%s.%N)
# compile_time=$(echo "$compile_end - $compile_start" | bc)
# echo "compile took $compile_time secs." >> texput.log

RET=$?
if [ $RET -eq 0 ];
then
    echo "";
elif [ $RET -eq 124 ];
then
    echo "[E167] Compilation timed out!";
    cp "$3/1x7.png" "$1.png";
    exit 1
else
    grep -A 6 -m 1 "^!" "$1.log";
fi

if [ ! -f "$1.pdf" ];
then
    # echo "\n[E162]";
    cp "$3/1x2.png" "$1.png";
    exit 1
fi

# convert_start=$(date +%s.%N)

# -density <geometry>: horizontal and vertical density of the image
# -depth <value>: image depth
# -quality <value>: JPEG/MIFF/PNG compression level
# -repage <geometry>: size and location of an image canvas
# -gamma <value>: gamma value
# -fuzz <value>%: colors within <value>% are considered equal
# -trim: trim image edges
timeout 20 gs -q -r600 -sDEVICE=pngalpha -dBATCH -dNOPAUSE -dDownScaleFactor=1 -sOutputFile="$1.png" "$1.pdf" >> /dev/null;

# convert_end=$(date +%s.%N)
# convert_time=$(echo "$convert_end - $convert_start" | bc)
# echo "convert took $convert_time secs." >> texput.log
if [ $? -eq 124 ]; then
    echo "[E168] Image processing timed out!";
    cp "$3/1x8.png" "$1.png";
    exit 1
fi
