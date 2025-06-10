/*
 * SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
 *
 * SPDX-License-Identifier: LGPL-2.1-or-later OR Apache-2.0
 */

/*
 * Simple program to feed input to an m17n input method, and test that it
 * behaves as expected.
 *
 * TODO: m17n >= 1.8.6 - Switch to upstream m17n-input-test.
 */

#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include <m17n.h>

static bool assert_mtext_equal(const char *field_name, MText *actual,
                               const char *expected) {
  const int bufsize = 4096;
  unsigned char buf[bufsize];
  int buf_written = mconv_encode_buffer(Mcoding_utf_8, actual, buf, bufsize);
  if (buf_written < 0) {
    fprintf(stderr, "mconv_encode_buffer failed.\n");
    return false;
  }
  if (buf_written >= bufsize) {
    fprintf(stderr, "bufsize is too small.\n");
    return false;
  }
  buf[buf_written] = '\x00';

  if (strcmp((char *)buf, expected) == 0) {
    return true;
  } else {
    fprintf(stderr, "%s does not match. Expected '%s', got '%s'.\n", field_name,
            expected, buf);
    return false;
  }
}

int main(int argc, char *argv[]) {
  // Which input method to test.
  const char *language = NULL;
  const char *name = NULL;

  // Input keysyms.
  const char *input[argc];
  size_t input_count = 0;

  // Expected results.
  const char *expected_committed = "";
  bool expected_candidates_shown = false;
  const char *expected_candidates[argc];
  size_t expected_candidates_count = 0;
  const char *expected_preedit = "";

  int option;
  while ((option = getopt(argc, argv, "l:n:i:t:Cc:p:")) != -1) {
    switch (option) {
    case 'l':
      language = optarg;
      break;
    case 'n':
      name = optarg;
      break;
    case 'i':
      input[input_count++] = optarg;
      break;
    case 't':
      expected_committed = optarg;
      break;
    case 'C':
      expected_candidates_shown = true;
      break;
    case 'c':
      expected_candidates[expected_candidates_count++] = optarg;
      break;
    case 'p':
      expected_preedit = optarg;
      break;
    default:
      fprintf(stderr, "Error parsing options.\n");
      return 1;
    }
  }
  if (!language) {
    fprintf(stderr, "Missing argument: -l language\n");
    return 1;
  }
  if (!name) {
    fprintf(stderr, "Missing argument: -n name\n");
    return 1;
  }

  int retval = 0;
  MInputMethod *im = NULL;
  MInputContext *ic = NULL;

  M17N_INIT();

  MText *committed = mtext();

  im = minput_open_im(msymbol(language), msymbol(name), NULL);
  if (!im) {
    fprintf(stderr, "minput_open_im failed.\n");
    retval = 1;
    goto done;
  }

  ic = minput_create_ic(im, NULL);
  if (!ic) {
    fprintf(stderr, "minput_create_ic failed.\n");
    retval = 1;
    goto done;
  }

  for (size_t i = 0; i < input_count; i++) {
    MSymbol key = msymbol(input[i]);
    if (minput_filter(ic, key, NULL) != 0) {
      continue;
    }
    if (minput_lookup(ic, key, NULL, committed) != 0) {
      // Key wasn't handled, so it would be commited or forwarded.
      for (size_t j = 0; input[i][j]; j++) {
        mtext_cat_char(committed, input[i][j]);
      }
    }
  }

  if (!assert_mtext_equal("committed", committed, expected_committed)) {
    retval = 1;
  }

  if ((bool)ic->candidate_show != expected_candidates_shown) {
    fprintf(stderr, "Error: candidates %s shown.\n",
            ic->candidate_show ? "were" : "were not");
    retval = 1;
  }

  if (expected_candidates_count == 0) {
    if (ic->candidate_list) {
      fprintf(stderr, "Expected no candidates, but there were some.\n");
      retval = 1;
    }
  } else if (!ic->candidate_list) {
    fprintf(stderr, "Expected candidates, but there were none.\n");
    retval = 1;
  } else if (mplist_key(ic->candidate_list) != Mplist ||
             mplist_length(ic->candidate_list) != 1) {
    fprintf(stderr, "Unsupported structure of candidate_list.\n");
    retval = 1;
  } else if (mplist_length(mplist_value(ic->candidate_list)) !=
             expected_candidates_count) {
    fprintf(stderr, "Expected %zu candidates, got %i\n",
            expected_candidates_count,
            mplist_length(mplist_value(ic->candidate_list)));
    retval = 1;
  } else {
    // Some candidates are expected, candidate_list has a single plist group.
    size_t i;
    MPlist *candidates_head;
    for (i = 0, candidates_head = mplist_value(ic->candidate_list);
         i < expected_candidates_count && candidates_head;
         i++, candidates_head = mplist_next(candidates_head)) {
      if (mplist_key(candidates_head) != Mtext) {
        fprintf(stderr, "Unsupported structure of candidate_list.\n");
        retval = 1;
      } else if (!assert_mtext_equal("candidate", mplist_value(candidates_head),
                                     expected_candidates[i])) {
        fprintf(stderr, "Candidate mismatch was at index %zu\n", i);
        retval = 1;
      }
    }
  }

  if (!assert_mtext_equal("preedit", ic->preedit, expected_preedit)) {
    retval = 1;
  }

done:
  if (ic) {
    minput_destroy_ic(ic);
  }
  if (im) {
    minput_close_im(im);
  }
  m17n_object_unref(committed);
  M17N_FINI();
  return retval;
}
