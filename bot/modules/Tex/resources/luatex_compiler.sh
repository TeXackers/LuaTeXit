cd "tex/staging/$1/" || exit 1

# chmod --quiet -R o+rwx .

# find . ! -name "$1.tex" -type f -exec rm -f {} +

timeout 1m luatex --file-line-error "$1.tex" > plaintex.log #2>&1

RET=$?
if [ $RET -eq 0 ];
then
    echo "";
elif [ $RET -eq 124 ];
then
    echo "[E107] Compilation timed out!";
else
    grep -A 10 -m 1 "^\./" "plaintex.log" | sed "s+\./$1\.tex.*:++"
fi

if [ ! -f "$1.pdf" ];
then
  # echo "[E102]";
  cp "../../failed/1x2.png" "$1.png"
  exit 1
# check if .dvi might be present
elif [ -f "$1.dvi" ];
then
  dvipdfmx "$1.dvi" > /dev/null
fi


timeout 10 gs -q -r1800 -sDEVICE=png16m -dBATCH -dNOPAUSE -dDownScaleFactor=3 -sOutputFile="$1.png" "$1.pdf" >> /dev/null;

if [ $? -eq 124 ];
then
 echo "[E108] Image processing timed out!";
 cp "../../failed/1x8.png" "$1.png"
 exit 1
fi
