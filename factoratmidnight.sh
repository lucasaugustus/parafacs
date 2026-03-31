while true; do
    sleep $(( $(date -d "tomorrow 00:00:00" +%s) - $(date +%s) ));
    clear;
    time ./factorcomposites.py depth=45 time=4;
done

