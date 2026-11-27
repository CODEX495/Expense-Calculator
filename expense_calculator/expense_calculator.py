import curses
import json
import os
from datetime import datetime

# Safe storage location (prevents the Read-Only error in Mac Downloads)
DATA_DIR = os.path.expanduser("~/.expense_tracker_data")
DATA_FILE = os.path.join(DATA_DIR, "expenses.json")

CATEGORIES = ["Food & Dining", "Transport", "Bills & Utilities", "Shopping", "Entertainment", "Health", "Other"]

class ExpenseTracker:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.expenses = self.load_data()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.expenses, f, indent=4)

    def add_expense(self, amount, category, description):
        try:
            amt = float(amount)
            if amt <= 0: return False
        except ValueError:
            return False
            
        expense = {
            "id": len(self.expenses) + 1,
            "amount": amt,
            "category": category,
            "description": description,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.expenses.append(expense)
        self.save_data()
        return True

    def delete_expense(self, index):
        if 0 <= index < len(self.expenses):
            del self.expenses[index]
            # Reassign IDs
            for i, e in enumerate(self.expenses, 1):
                e["id"] = i
            self.save_data()
            return True
        return False

    def get_totals(self):
        totals = {cat: 0.0 for cat in CATEGORIES}
        total_all = 0.0
        for e in self.expenses:
            if e["category"] in totals:
                totals[e["category"]] += e["amount"]
            total_all += e["amount"]
        return totals, total_all


# --- Curses UI Functions ---

def draw_menu(stdscr, options, title, current_row):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    
    # Draw Title
    title_x = w//2 - len(title)//2
    stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
    stdscr.addstr(2, title_x, title)
    stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)

    # Draw Menu Options
    for idx, option in enumerate(options):
        x = w//2 - len(option)//2
        y = h//2 - len(options)//2 + idx
        
        if idx == current_row:
            stdscr.attron(curses.color_pair(2))
            stdscr.addstr(y, x, option)
            stdscr.attroff(curses.color_pair(2))
        else:
            stdscr.addstr(y, x, option)
    stdscr.refresh()

def menu_loop(stdscr, options, title):
    curses.curs_set(0)
    current_row = 0
    draw_menu(stdscr, options, title, current_row)

    while True:
        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(options) - 1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            return current_row
        draw_menu(stdscr, options, title, current_row)

def get_input(stdscr, prompt, y, x):
    curses.curs_set(1)
    curses.echo()
    stdscr.addstr(y, x, prompt)
    stdscr.refresh()
    input_str = stdscr.getstr(y + 1, x, 30).decode('utf-8')
    curses.noecho()
    curses.curs_set(0)
    return input_str

def main(stdscr):
    # Initialize colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)

    tracker = ExpenseTracker()
    
    while True:
        options = ["➕  Add Expense", "📊  View Expenses", "📈  Summary by Category", "❌  Delete Expense", "🚪  Exit"]
        choice = menu_loop(stdscr, options, "💰 EXPENSE TRACKER 💰")

        if choice == 0: # Add Expense
            stdscr.clear()
            stdscr.addstr(2, 5, "--- Add Expense ---", curses.color_pair(1) | curses.A_BOLD)
            amount = get_input(stdscr, "Amount ($): ", 4, 5)
            
            # Select Category
            cat_choice = menu_loop(stdscr, CATEGORIES, "Select Category")
            category = CATEGORIES[cat_choice]
            
            stdscr.clear()
            desc = get_input(stdscr, "Description: ", 4, 5)
            
            if tracker.add_expense(amount, category, desc):
                stdscr.addstr(7, 5, "✓ Expense added successfully!", curses.color_pair(3))
            else:
                stdscr.addstr(7, 5, "✗ Invalid amount. Try again.", curses.color_pair(1))
            stdscr.getch()

        elif choice == 1: # View Expenses
            stdscr.clear()
            stdscr.addstr(1, 2, "--- All Expenses ---", curses.color_pair(1) | curses.A_BOLD)
            stdscr.addstr(2, 2, f"{'ID':<4} {'Date':<18} {'Category':<20} {'Amount':<10} Description")
            stdscr.addstr(3, 2, "-" * 70)
            
            for i, e in enumerate(tracker.expenses):
                line = f"{e['id']:<4} {e['date']:<18} {e['category']:<20} ${e['amount']:<9.2f} {e['description']}"
                stdscr.addstr(4 + i, 2, line)
            
            stdscr.addstr(curses.LINES - 2, 2, "Press any key to return...")
            stdscr.getch()

        elif choice == 2: # Summary
            stdscr.clear()
            stdscr.addstr(1, 2, "--- Spending by Category ---", curses.color_pair(1) | curses.A_BOLD)
            totals, grand_total = tracker.get_totals()
            
            y = 3
            for cat, amt in totals.items():
                if amt > 0:
                    percent = (amt / grand_total) * 100 if grand_total > 0 else 0
                    bar = "█" * int(percent / 2)
                    line = f"{cat:<20} ${amt:<10.2f} {percent:>5.1f}% {bar}"
                    stdscr.addstr(y, 2, line)
                    y += 1
            
            stdscr.addstr(y + 1, 2, "-" * 50)
            stdscr.addstr(y + 2, 2, f"TOTAL: ${grand_total:.2f}", curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr(curses.LINES - 2, 2, "Press any key to return...")
            stdscr.getch()

        elif choice == 3: # Delete
            if not tracker.expenses:
                continue
                
            del_options = [f"#{e['id']} - {e['category']} (${e['amount']})" for e in tracker.expenses]
            del_options.append("Cancel")
            
            del_choice = menu_loop(stdscr, del_options, "Select Expense to Delete")
            
            if del_choice < len(tracker.expenses):
                tracker.delete_expense(del_choice)
                stdscr.clear()
                stdscr.addstr(2, 5, "✓ Expense deleted!", curses.color_pair(3))
                stdscr.getch()

        elif choice == 4: # Exit
            break

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"An error occurred: {e}")
        print("If you are on Mac, make sure to run this in the native Terminal app, not VS Code.")