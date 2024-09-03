#include <winfsp/winfsp.h>

#include <cstdlib>

int main()
{
	UINT32 version;
	NTSTATUS status = FspVersion(&version);

	return status >= 0
		? EXIT_SUCCESS
		: EXIT_FAILURE;
}
