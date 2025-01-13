cd "tex/staging/$1/" || exit 1

# chmod --quiet -R o+rwx .

# compile_start=$(date +%s.%N)
# sudo -u $(whoami) timeout 1m pdflatex $1.tex > texput.log 2>&1
timeout 3m latexmk -xelatex -shell-escape -halt-on-error -interaction=nonstopmode "$1.tex" > texput_xetex.log #2>&1
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
    cp "../../failed/1x7.png" "$1.png";
    exit 1
else
    grep -A 6 -m 1 "^!" "$1.log";
fi

if [ ! -f "$1.pdf" ];
then
    # echo "\n[E162]";
    cp "../../failed/1x2.png" "$1.png";
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
timeout 10 magick convert -density 600 -quality 90 -depth 8 -gamma 2 -fuzz 1% -trim +repage "$1.pdf" -colorspace RGB +profile "icc" PNG64:"$1.png" >> /dev/null;

# convert_end=$(date +%s.%N)
# convert_time=$(echo "$convert_end - $convert_start" | bc)
# echo "convert took $convert_time secs." >> texput.log
if [ $? -eq 124 ]; then
    echo "[E168] Image processing timed out!";
    cp "../../failed/1x8.png" "$1.png";
    exit 1
fi
