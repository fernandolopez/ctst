
test_something: test_something.o __ctst_main_test_something.o ctst/ctst.o
	gcc -Wall -g -o test_something test_something.o ctst/ctst.o __ctst_main_test_something.o


__ctst_main_test_something.c: test_something.o
	ctst/generate.sh test_something.o > __ctst_main_test_something.c

__ctst_main_test_something.o: __ctst_main_test_something.c

test_something.o: test_something.c ctst/ctst.h
	gcc -Wall --std=c99 -c test_something.c

ctst/ctst.o: ctst/ctst.c ctst/ctst.h

clean:
	rm -f __ctst_main_test_something.o __ctst_main_test_something.c test_something.bin test_something.o ctst/ctst.o
