cd "$2/$1/" || exit 1

# Colour expressions for typst and ImageMagick, derived from the requested colourscheme.
if [ "$3" = "trans" ]; then
    TYPST_BG='rgb(0, 0, 0, 0)'
    MAGICK_BG="none"
else
    TYPST_BG="rgb(\"#$3\")"
    MAGICK_BG="#$3"
fi
TYPST_TEXT="rgb(\"#$4\")"

timeout --kill-after=5s 3s typst compile --root "$2/$1" --font-path "$5" -f png --ppi 300 "$1.typ" "$1.png" 2> "$1.log"

RET=$?

# if it's downloading from typst universe
if [ $RET -eq 124 ] && grep -q "^downloading " "$1.log"; then
    timeout --kill-after=5s 10s typst compile --root "$2/$1" --font-path "$5" -f png --ppi 300 "$1.typ" "$1.png" 2> "$1.log"
    RET=$?
fi

# multi PNG?
if [ $RET -ne 0 ] && grep -q "cannot export multiple images without a page number template" "$1.log"; then
    timeout --kill-after=5s 3s typst compile --root "$2/$1" --font-path "$5" -f png --ppi 300 "$1.typ" "$1-{0p}.png" 2> "$1.log"
    RET=$?
fi

if [ $RET -ne 0 ]; then
    if [ $RET -eq 124 ]; then
        MESSAGE="Compilation took too long!"
    else
        cat "$1.log"
        MESSAGE="Compilation Failed"
    fi

    printf '%s\n' \
        "#set page(width: 345pt, height: auto, margin: 10pt, fill: $TYPST_BG)" \
        "#set text(font: \"DIN\", weight: 700, size: 32pt, fill: $TYPST_TEXT)" \
        "#upper[$MESSAGE]" > failed.typ
    timeout 5s typst compile failed.typ "$1.png" --ppi 300 > /dev/null 2>&1

    if [ ! -f "$1.png" ]; then
        exit 1
    fi
fi

# Trim/border every page that was produced
for page in "$1.png" "$1"-*.png; do
    [ -f "$page" ] || continue
    magick "$page" -bordercolor "$MAGICK_BG" -trim +repage -border 30 -background "$MAGICK_BG" -flatten -colorspace sRGB "$page"
done

if [ $RET -ne 0 ]; then
    exit 1
fi