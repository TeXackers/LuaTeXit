cd tex/staging/$1/

chmod --quiet -R o+rwx .

# compile_start=$(date +%s.%N)
# sudo -u $(whoami) timeout 1m pdflatex $1.tex > texput.log 2>&1
sudo -u latex timeout 1m lualatex -no-shell-escape $1.tex > texput.log 2>&1
# compile_end=$(date +%s.%N)
# compile_time=$(echo "$compile_end - $compile_start" | bc)
# echo "compile took $compile_time secs." >> texput.log

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

# convert_start=$(date +%s.%N)
timeout 20 convert -density 700 -quality 75 -depth 8 -trim +repage $1.pdf PNG32:$1.png;
# convert_end=$(date +%s.%N)
# convert_time=$(echo "$convert_end - $convert_start" | bc)
# echo "convert took $convert_time secs." >> texput.log
if [ $? -eq 124 ]; then
    echo "Image processing timed out!";
    cp ../../failed.png $1.png
    exit 1
fi
