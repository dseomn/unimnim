# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

all: m17n-test

m17n-test: m17n-test.c
	$(CC) -Wall $(CFLAGS) -o $@ m17n-test.c -lm17n -lm17n-core
