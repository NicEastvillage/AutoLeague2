import tkinter as tk

from match import MatchResult

def confirm_match_result(match_result: MatchResult):
    window = tk.Tk()
    window.wm_title("Confirm match results")
    window.geometry("512x448")

    small_font = ("Comic Sans MS", 24)
    font = ("Comic Sans MS", 32)

    blue_goals_label = tk.Label(text="blue goals", font=small_font)
    blue_goals_label.place(x=32, y=64, width=192, height=64)
    blue_goals_entry = tk.Entry(font=font)
    blue_goals_entry.insert(0, str(match_result.blue_goals))
    blue_goals_entry.place(x=64, y=128, width=128, height=64)

    orange_goals_label = tk.Label(text="orange goals", font=small_font)
    orange_goals_label.place(x=288, y=64, width=192, height=64)
    orange_goals_entry = tk.Entry(font=font)
    orange_goals_entry.insert(0, str(match_result.orange_goals))
    orange_goals_entry.place(x=320, y=128, width=128, height=64)

    def confirm_scores(event):
        try:
            match_result.blue_goals = int(blue_goals_entry.get())
        except ValueError:
            print("Cannot convert blue goals to int")
        else:
            try:
                match_result.orange_goals = int(orange_goals_entry.get())
            except ValueError:
                print("Cannot convert orange goals to int")
            else:
                # No exceptions, we can close
                window.quit()

    confirm_button = tk.Button(text="Confirm", font=font)
    confirm_button.bind("<Button-1>", func=confirm_scores)
    confirm_button.place(x=64, y=256, width=384, height=96)

    window.mainloop()

    return match_result


if __name__ == "__main__":
    # Test popup
    match_result = confirm_match_result(MatchResult())
    print(match_result)
