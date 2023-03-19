# /usr/bin/env bash

tmp_dir=tests/assets/tmp/
add_dir=$assets_dir/added/
mkdir -p $tmp_dir
rm -rf $tmp_dir/*
rm -rf $add_dir/*

# write pid to a file
echo $$ > tests/assets/tmp/watchfiles_test.sh.pid

# modifiy tests/assets/tmp/watchfiles_call_test
# add tests/assets/tmp/$RANDOM with random content
# touch tests/assets/tmp/$sec and rm afterwards
# timout: 30s
for sec in {0..15..1}
do
    touch $tmp_dir/$sec
    echo $RANDOM > $tmp_dir/watchfiles_call_test;
    touch $tmp_dir/$RANDOM
    sleep 1
    rm $tmp_dir/$sec
done
