#!/bin/sh

static_object="$1"

header=$(cat) <<'EOF'
#include <stdlib.h>
#include <stdio.h>
#include "ctst/ctst.h"
EOF
main_header=$(cat) <<'EOF'
int main(int argc, char **argv){
    char *msj;
    unsigned tests_ok=0;
    unsigned tests_failed=0;
    unsigned tests_skipped=0;
EOF


symbols=$(objdump -t --section=.text "$static_object" | grep ' F ' | awk '{print $6}')

call_setup=$(echo $symbols | grep __ctst_setup)
call_teardown=$(echo $symbols | grep __ctst_teardown)

if [ -n "$call_setup" ]; then
    call_setup='__ctst_setup();'
fi

if [ -n "$call_teardown" ]; then
    call_teardown='__ctst_teardown();'
fi

echo "$header"
for symbol in $symbols; do
    if [ -n "$(echo $symbol | grep -E '^test_')" ]; then
        echo "char *${symbol}();"
    fi
done

echo "$main_header"
for symbol in $symbols; do
    if [ -n "$(echo $symbol | grep -E '^test_')" ]; then
        cat <<EOF
        ${ctst_tests}
        ${call_setup}
        if ((msj = ${symbol}()) == NULL){
            tests_ok++;
        }
        else{
            printf("FAIL: ${symbol}: %s\n", msj);
            free(msj);
            tests_failed++;
        }
        ${call_teardown}
EOF
    fi
done

cat <<'EOF'
    printf("OK: %u, FAIL: %u, SKIP: %u\n", tests_ok, tests_failed, tests_skipped);
    return (tests_failed == 0)?EXIT_SUCCESS:EXIT_FAILURE;
}
EOF
