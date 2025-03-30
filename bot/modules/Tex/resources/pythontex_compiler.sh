cd "tex/staging/$1/" || exit 1

timeout 1m latexmk -lualatex -shell-escape -halt-on-error "$1.tex" > texput_pytex.log && \
timeout 10s /usr/bin/pythontex "$1.tex" > texput_pytex.log && \
timeout 1m latexmk -lualatex -shell-escape -halt-on-error "$1.tex" >> texput_pytex.log

RET=$?
if [ $RET -eq 0 ];
then
    echo "";
elif [ $RET -eq 124 ];
then
    echo "[E177] Compilation timed out!";
    cp "../../failed/1x7.png" "$1.png";
    exit 1
else
    grep -A 6 -m 1 "^!" "$1.log";
fi

if [ ! -f "$1.pdf" ];
then
    # 172
    # echo "\n[E172]";
    cp "../../failed/1x2.png" "$1.png"
    exit 1
fi

# convert_start=$(date +%s.%N)

# -density <geometry>: horizontal and vertical density of the image
# -depth <value>: image depth
# -quality <value>: JPEG/MIFF/PNG compression level
# -repage <geometry>: size and location of an image canvas
# -trim: trim image edges
timeout 10 magick convert -density 600 -quality 100 -depth 16 -gamma 2 -fuzz 1% -trim +repage "$1.pdf" -colorspace RGB +profile "icc" PNG64:"$1.png" >> /dev/null;

# convert_end=$(date +%s.%N)
# convert_time=$(echo "$convert_end - $convert_start" | bc)
# echo "convert took $convert_time secs." >> texput.log
if [ $? -eq 124 ]; then
    echo "[E178] Image processing timed out!";
    # 178
    cp "../../failed/1x8.png" "$1.png"
    exit 1
fi
