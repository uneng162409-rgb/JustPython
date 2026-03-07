import os

def push_to_github():

    print("📤 Pushing to GitHub...")

    os.system("git add .")
    os.system('git commit -m "auto update bio farm"')
    os.system("git push")

    print("✅ Push Complete")

if __name__ == "__main__":
    push_to_github()