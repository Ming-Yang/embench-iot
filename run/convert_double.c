#include <stdio.h>
#include <stdlib.h>
unsigned char nop[4] = {0x00, 0x00, 0x40, 0x03};
unsigned char *seg_addr[] = {"@38000", "@80000"};

int main(int argc, char **argv)
{
	FILE *in[2];
	FILE *out;

	unsigned char mem[64];
	out = fopen("axi_ram.dat", "w");
	for (int i = 1; i < argc; ++i)
	{
		int file_no = i - 1;
		in[file_no] = fopen(argv[i], "rb");
		fprintf((out), "%s\n", seg_addr[file_no]);
		while (!feof(in[file_no]))
		{
			int read_bytes = fread(mem, 1, 8, in[file_no]);
			if (read_bytes == 4)
				for (int k = 3; k >= 0; --k)
					mem[4 + k] = nop[k];
			if (read_bytes >= 4)
				fprintf(out, "%02x%02x%02x%02x%02x%02x%02x%02x\n", mem[7], mem[6], mem[5], mem[4], mem[3], mem[2], mem[1], mem[0]);
		}
		fclose(in[file_no]);
	}

	fclose(out);

	return 0;
}
