cd "tex/staging/$1/" || exit 1

# chmod --quiet -R o+rwx .

# find . ! -name "$1.tex" -type f -exec rm -f {} +

timeout 1m luatex -file-line-error -halt-on-error "$1.tex" > plaintex.log #2>&1

RET=$?
if [ $RET -eq 0 ];
then
    echo "";
elif [ $RET -eq 124 ];
then
    echo "[E107] Compilation timed out!";
else
    grep -A 10 -m 1 "^!" "plaintex.log";
fi

if [ ! -f "$1.pdf" ];
then
  echo "[E102]";
  cp "../../failed/1x2.png" "$1.png"
  exit 1
# check if .dvi might be present
elif [ -f "$1.dvi"];
then
  dvipdfmx "$1.dvi" > /dev/null
fi

# -density <geometry>: horizontal and vertical density of the image
# -depth <value>: image depth
# -quality <value>: JPEG/MIFF/PNG compression level
# -repage <geometry>: size and location of an image canvas
# -trim: trim image edges
timeout 10 magick convert -density 600 -quality 90 -depth 8 -gamma 2 -fuzz 1% -trim +repage "$1.pdf" -colorspace RGB +profile "icc" PNG64:"$1.png" >> /dev/null;

if [ $? -eq 124 ];
then
 echo "[E108] Image processing timed out!";
 cp "../../failed/1x8.png" "$1.png"
 exit 1
fi
