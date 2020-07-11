#include "ctst/ctst.h"
#include <stdio.h>

SETUP({
	printf("setup\n");
})

TEARDOWN({
	printf("teardown\n");
})

TEST(math_works, {
	ASSERT(1 != 5, "Math works");
})

TEST(lets_fail, {
	ASSERT(1 == 5, "Lets fail");
})
