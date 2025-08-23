#include <stdlib.h>

#define EXPORT __attribute__((visibility("default")))
void __ctst_setup();
void __ctst_teardown();
void __ctst_assert(int assertion, const char *msg, char **result);
extern int __ctst_success;
extern int __ctst_failed;
extern int __ctst_skipped;

#define SETUP(__CTST_SETUP_CODE) EXPORT \
void __ctst_setup(){\
	__CTST_SETUP_CODE\
}

#define TEARDOWN(__CTST_TEARDOWN_CODE) EXPORT \
void __ctst_teardown(){\
	__CTST_TEARDOWN_CODE\
}

#define TEST(__CTST_TEST_NAME, __CTST_TEST_CODE) EXPORT \
char *test_##__CTST_TEST_NAME(){\
	char *__ctst_result = NULL;\
	{\
		__CTST_TEST_CODE\
	}\
	return __ctst_result;\
}

#define SKIP(__CTST_TEST_NAME, __CTST_TEST_CODE) EXPORT \
char *skip_##__CTST_TEST_NAME(){\
	__ctst_skipped++;\
	return NULL;\
}

#define ASSERT(__CTST_ASSERTION, __CTST_ASSERTION_MSG)\
__ctst_assert(__CTST_ASSERTION, __CTST_ASSERTION_MSG, &__ctst_result)
