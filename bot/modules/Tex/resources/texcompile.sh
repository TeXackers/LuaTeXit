cd tex/staging/$1/

chmod --quiet -R o+rwx .

# find . ! -name "$1.tex" -type f -exec rm -f {} +

sudo -u $(whoami) timeout 1m pdflatex -no-shell-escape $1.tex > texout.log 2>&1

RET=$?
if [ $RET -eq 0 ];
then
 echo "";
elif [ $RET -eq 124 ];
then
 echo "Compilation timed out!";
else
    grep -A 10 -m 1 "^!" $1.log;
fi

if [ ! -f $1.pdf ];
then
  cp ../../failed.png $1.png
  exit 1
fi

# -density <geometry>: horizontal and vertical density of the image
# -depth <value>: image depth
# -quality <value>: JPEG/MIFF/PNG compression level
# -repage <geometry>: size and location of an image canvas
# -trim: trim image edges
timeout 10 convert -density 600 -quality 90 -depth 8 -trim +repage $1.pdf -colorspace sRGB PNG64:$1.png;

if [ $? -eq 124 ];
then
 echo "Image processing timed out!";
 cp ../../failed.png $1.png
 exit 1
fi
