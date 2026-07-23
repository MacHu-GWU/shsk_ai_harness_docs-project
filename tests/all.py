# -*- coding: utf-8 -*-

if __name__ == "__main__":
    from shsk_ai_harness_docs.tests import run_cov_test

    run_cov_test(
        __file__,
        "shsk_ai_harness_docs",
        is_folder=True,
        preview=False,
    )
