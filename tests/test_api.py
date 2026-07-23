# -*- coding: utf-8 -*-

from shsk_ai_harness_docs import api


def test():
    _ = api


if __name__ == "__main__":
    from shsk_ai_harness_docs.tests import run_cov_test

    run_cov_test(
        __file__,
        "shsk_ai_harness_docs.api",
        preview=False,
    )
