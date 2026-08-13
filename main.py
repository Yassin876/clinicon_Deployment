"""
main.py
نقطة التشغيل — بيفتح محادثة في الـ terminal بينك وبين الـ agent.
اكتب كلامك واضغط Enter، والـ agent يرد. اكتب "خروج" أو "exit" عشان تقفل.
"""
from app.orchestrator import create_agent, chat


def main():
    print("=" * 50)
    print("  مساعد العيادة الذكي — SPHG")
    print("  اكتب 'خروج' أو 'exit' للإنهاء")
    print("=" * 50)
    print()

    agent = create_agent()

    while True:
        try:
            user_input = input("أنت: ").strip()
        except (EOFError, KeyboardInterrupt):
            # المستخدم ضغط Ctrl+C أو Ctrl+D
            print("\nمع السلامة!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("خروج", "exit", "quit"):
            print("مع السلامة!")
            break

        print("المساعد: يفكّر...", end="\r")  # رسالة مؤقتة تتشال لما الرد يوصل
        reply = chat(agent, user_input)
        print(f"المساعد: {reply}")
        print()


if __name__ == "__main__":
    main()
