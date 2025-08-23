#include <stdlib.h>
#include <string.h>
#include "ctst.h"

int __ctst_succeeded;
int __ctst_failed;
int __ctst_skipped;

void __ctst_assert(int assertion, const char *msg, char **result){
	if (assertion){
		__ctst_succeeded++;
		return;
	}
	if (*result == NULL){
		*result = malloc(strlen(msg) + 1);
		*result[0] = 0;
	}
	else{
		*result = realloc(*result, strlen(*result) + strlen(msg) + 2);
		strcat(*result, "\n");
	}
	strcat(*result, msg);
	__ctst_failed++;
}
