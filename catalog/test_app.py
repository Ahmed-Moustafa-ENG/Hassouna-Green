"""End-to-end check of the app: runs the four steps and the plant filter.

    python catalog/test_app.py
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")
from streamlit.testing.v1 import AppTest

APP = str(__import__("pathlib").Path(__file__).resolve().parent.parent / "22_updated.py")


def run(lang: str) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    if lang == "en":
        at.radio[0].set_value("en").run()
    at.button(key="step1_next").click().run()
    at.number_input(key="width_in").set_value(40.0)
    at.number_input(key="height_in").set_value(30.0)
    at.run()
    at.button(key="step2_next").click().run()
    at.button(key="step3_gen").click().run()
    return at


def main() -> None:
    failed = False
    for lang in ("en", "ar"):
        at = run(lang)
        if at.exception:
            print(f"  {lang}: EXCEPTION {[str(e.value)[:200] for e in at.exception]}")
            failed = True
        else:
            print(f"  {lang}: the four steps run without an exception")
        for key, expected in (("group:vegetable", 12), ("group:fruit", 10)):
            at.selectbox(key="plant_filter_sel").set_value(key).run()
            texts = "\n".join(t.value for t in at.markdown)
            cards = texts.count('class="plant-card"')
            errors = [str(e.value)[:200] for e in at.exception]
            status = "ok" if not errors and cards == expected else "FAILED"
            print(f"     {key}: {cards} plant cards (expected {expected}) — {status}")
            if status == "FAILED":
                failed = True
    print("\n  result:", "FAILED" if failed else "all checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
