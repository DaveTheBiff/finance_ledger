import json
from typing import List, Dict, Any, Literal, TypedDict
from datetime import datetime

# Import Rich components for nice console output
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, FloatPrompt, IntPrompt

# Initialize the console object
console = Console()

# --- 1. Type Definitions (Strict Type Hinting) ---
# Using TypedDict to enforce the structure of a transaction dictionary.
# This makes the code much safer and easier to read!

TransactionType = Literal["income", "expense"]


class Transaction(TypedDict):
    """
    Defines the strict structure for a single transaction record.
    We use dictionaries (TypedDict) for storing structured data.
    """

    id: int
    date: str
    type: TransactionType
    category: str
    amount: float
    description: str


# --- 2. Core Ledger Class ---


class PersonalFinanceLedger:
    """
    Manages all transactions and ledger operations.
    The main data structure is a list of Transaction dictionaries.
    """

    def __init__(self, data_file: str = "ledger_data.json"):
        self.data_file = data_file
        self.transactions: List[Transaction] = []
        self._load_transactions()
        self._next_id = max((t["id"] for t in self.transactions), default=0) + 1

    def _load_transactions(self) -> None:
        """Loads transaction data from the JSON file."""
        try:
            with open(self.data_file, "r") as f:
                # Load the data and ensure it matches the Transaction list type
                self.transactions = json.load(f)
            console.print(
                f"[green]Data loaded successfully from {self.data_file}.[/green]"
            )
        except FileNotFoundError:
            # If file doesn't exist, start with an empty list
            self.transactions = []
            console.print("[yellow]Starting with a fresh, empty ledger.[/yellow]")
        except json.JSONDecodeError:
            # Handle corrupted or empty JSON file
            console.print(
                "[bold red]Error loading data: JSON file is corrupted or empty. Starting new ledger.[/bold red]"
            )
            self.transactions = []

    def _save_transactions(self) -> None:
        """Saves current transactions to the JSON file."""
        try:
            with open(self.data_file, "w") as f:
                # Use indent=4 to make the exported file human-readable
                json.dump(self.transactions, f, indent=4)
        except IOError:
            console.print("[bold red]Error: Could not save data to file![/bold red]")

    def add_transaction(
        self, tx_type: TransactionType, category: str, amount: float, description: str
    ) -> None:
        """Adds a new transaction dictionary to the list."""
        new_transaction: Transaction = {
            "id": self._next_id,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": tx_type,
            "category": category,
            "amount": round(amount, 2),
            "description": description,
        }
        self.transactions.append(new_transaction)
        self._next_id += 1
        self._save_transactions()
        console.print(
            f"\n[bold green]✅ {tx_type.capitalize()} transaction added! ID: {new_transaction['id']}[/bold green]\n"
        )

    def delete_transaction(self, tx_id: int) -> bool:
        """Deletes a transaction by its ID."""
        initial_count = len(self.transactions)
        # Filter out the transaction with the given ID
        self.transactions = [t for t in self.transactions if t["id"] != tx_id]

        if len(self.transactions) < initial_count:
            self._save_transactions()
            console.print(
                f"\n[bold yellow]🗑️ Transaction ID {tx_id} deleted.[/bold yellow]\n"
            )
            return True
        else:
            console.print(
                f"\n[bold red]❌ Error: Transaction ID {tx_id} not found.[/bold red]\n"
            )
            return False

    def calculate_balance(self) -> float:
        """Calculates the current net balance."""
        balance = 0.0
        for tx in self.transactions:
            if tx["type"] == "income":
                balance += tx["amount"]
            elif tx["type"] == "expense":
                balance -= tx["amount"]
        return round(balance, 2)

    def generate_summary(self) -> Dict[str, float]:
        """Calculates total income and total expense."""
        summary: Dict[str, float] = {"income": 0.0, "expense": 0.0}
        for tx in self.transactions:
            if tx["type"] == "income":
                summary["income"] += tx["amount"]
            elif tx["type"] == "expense":
                summary["expense"] += tx["amount"]

        summary["income"] = round(summary["income"], 2)
        summary["expense"] = round(summary["expense"], 2)
        return summary

    def export_data(self, filename: str) -> None:
        """Exports all data to a specified JSON file."""
        try:
            with open(filename, "w") as f:
                json.dump(self.transactions, f, indent=4)
            console.print(
                f"[bold cyan]📤 Data successfully exported to {filename}[/bold cyan]"
            )
        except IOError:
            console.print(
                "[bold red]Error: Could not write to the specified file.[/bold red]"
            )

    def import_data(self, filename: str) -> None:
        """Imports data from a JSON file, replacing the current ledger."""
        try:
            with open(filename, "r") as f:
                imported_data: List[Transaction] = json.load(f)
            # Simple validation to check if the imported data looks like transactions
            if not isinstance(imported_data, list) or not all(
                isinstance(d, dict) for d in imported_data
            ):
                raise ValueError("Imported file format is incorrect.")

            self.transactions = imported_data
            self._next_id = max((t["id"] for t in self.transactions), default=0) + 1
            self._save_transactions()
            console.print(
                f"[bold green]📥 Data successfully imported from {filename}.[/bold green]"
            )
        except FileNotFoundError:
            console.print(f"[bold red]Error: File not found at {filename}.[/bold red]")
        except (json.JSONDecodeError, ValueError) as e:
            console.print(
                f"[bold red]Error importing data: {e}. File format may be invalid.[/bold red]"
            )


# --- 3. CLI Interaction Functions ---


def display_transactions(
    transactions: List[Transaction], title: str = "Transaction History"
) -> None:
    """Displays transactions using a professional Rich Table."""
    if not transactions:
        console.print(Panel(f"[yellow]No transactions found for {title}.[/yellow]"))
        return

    table = Table(title=title, show_header=True, header_style="bold blue")
    # Define columns
    table.add_column("ID", style="dim", width=5)
    table.add_column("Date", min_width=20)
    table.add_column("Type", style="bold")
    table.add_column("Category", min_width=10)
    table.add_column("Amount", justify="right")
    table.add_column("Description", overflow="fold")

    # Add rows
    for tx in transactions:
        amount_style = "green" if tx["type"] == "income" else "red"
        type_icon = "⬆️" if tx["type"] == "income" else "⬇️"

        table.add_row(
            str(tx["id"]),
            tx["date"],
            f"[{amount_style}]{type_icon} {tx['type'].capitalize()}",
            tx["category"].capitalize(),
            f"[{amount_style}]${tx['amount']:.2f}",
            tx["description"],
        )
    console.print(table)


def handle_add(ledger: PersonalFinanceLedger) -> None:
    """Prompts user for input to add a new transaction."""
    tx_type: str = Prompt.ask(
        "Is this [bold blue]Income[/bold blue] or [bold blue]Expense[/bold blue]?",
        choices=["income", "expense"],
        default="expense",
    )
    category = Prompt.ask(
        "Enter Category (e.g., [green]Salary[/green], [red]Groceries[/red])"
    )
    # Use FloatPrompt to ensure the input is a valid number
    amount = FloatPrompt.ask("Enter Amount", default=0.0)
    description = Prompt.ask("Enter a brief description")

    if amount <= 0:
        console.print(
            "[bold red]Amount must be greater than zero. Transaction cancelled.[/bold red]"
        )
        return

    # Call the core ledger logic
    ledger.add_transaction(tx_type, category, amount, description)


def handle_view(ledger: PersonalFinanceLedger) -> None:
    """Allows filtering transactions before displaying."""
    filter_choice = Prompt.ask(
        "Filter by [bold]type[/bold] (income/expense) or [bold]category[/bold]? (type 'all' for everything)",
        default="all",
    )

    if filter_choice.lower() == "all":
        display_transactions(ledger.transactions, "Full Transaction History")
    elif filter_choice.lower() in ("income", "expense"):
        filtered = [
            t for t in ledger.transactions if t["type"] == filter_choice.lower()
        ]
        display_transactions(filtered, f"{filter_choice.capitalize()} Transactions")
    elif filter_choice.lower() == "category":
        cat = Prompt.ask("Enter Category to filter by").lower()
        filtered = [t for t in ledger.transactions if t["category"].lower() == cat]
        display_transactions(filtered, f"Transactions in Category: {cat.capitalize()}")
    else:
        console.print("[bold red]Invalid filter choice.[/bold red]")


def handle_summary(ledger: PersonalFinanceLedger) -> None:
    """Displays the financial summary."""
    summary = ledger.generate_summary()
    balance = ledger.calculate_balance()

    table = Table(title="Financial Summary", show_header=False)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row(
        "[green]Total Income[/green]", f"[green]${summary['income']:.2f}[/green]"
    )
    table.add_row("[red]Total Expense[/red]", f"[red]${summary['expense']:.2f}[/red]")

    balance_style = "bold green" if balance >= 0 else "bold red"
    table.add_row(
        f"[{balance_style}]Current Balance",
        f"[{balance_style}]${balance:.2f}[/{balance_style}]",
    )

    console.print("\n", table, "\n")


def handle_balance(ledger: PersonalFinanceLedger) -> None:
    """Displays only the current balance."""
    balance = ledger.calculate_balance()
    balance_style = "bold green" if balance >= 0 else "bold red"
    console.print(
        Panel(
            f"Your current balance is: [b {balance_style}]${balance:.2f}[/]",
            title="Current Balance",
            border_style="cyan",
        )
    )


def handle_delete(ledger: PersonalFinanceLedger) -> None:
    """Prompts for an ID to delete a transaction."""
    tx_id = IntPrompt.ask(
        "Enter the [bold red]ID[/bold red] of the transaction to delete"
    )
    ledger.delete_transaction(tx_id)


def handle_export(ledger: PersonalFinanceLedger) -> None:
    """Handles the export command."""
    filename = Prompt.ask("Enter the filename to export to", default="export.json")
    ledger.export_data(filename)


def handle_import(ledger: PersonalFinanceLedger) -> None:
    """Handles the import command."""
    filename = Prompt.ask("Enter the filename to import from")
    ledger.import_data(filename)


# --- 4. Main Application Loop ---


def run_cli() -> None:
    """The main entry point for the Command Line Interface."""
    console.print(
        Panel(
            "[bold cyan]💰 Personal Finance Ledger[/bold cyan]\n"
            "Welcome! Type 'help' to see commands.",
            title="Welcome",
            border_style="yellow",
        )
    )

    # Initialize the ledger, which loads existing data
    ledger = PersonalFinanceLedger()

    # Dictionary mapping command names to the functions that handle them
    commands: Dict[str, Any] = {
        "add": handle_add,
        "view": handle_view,
        "summary": handle_summary,
        "balance": handle_balance,
        "export": handle_export,
        "import": handle_import,
        "delete": handle_delete,
    }

    def display_help() -> None:
        """Displays all available commands."""
        console.print("\n[bold magenta]Available Commands:[/bold magenta]")
        for cmd in commands:
            console.print(f"  [cyan]{cmd:<7}[/cyan]: {commands[cmd].__doc__.strip()}")
        console.print("  [cyan]help[/cyan]   : Show this help message")
        console.print("  [cyan]exit/quit[/cyan]: Exit the program\n")

    display_help()  # Show help at startup

    while True:
        # Simple, non-niche way to get user input for the command
        user_input: str = (
            Prompt.ask("[bold green]Ledger[/bold green] >").lower().strip()
        )

        if user_input in ("exit", "quit"):
            console.print(Panel("[bold yellow]👋 Goodbye! Data saved.[/bold yellow]"))
            break
        elif user_input == "help":
            display_help()
        elif user_input in commands:
            try:
                # Call the corresponding function from the dictionary
                commands[user_input](ledger)
            except Exception as e:
                console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")
        else:
            console.print(
                f"[bold red]Unknown command: '{user_input}'. Type 'help' for a list of commands.[/bold red]"
            )


if __name__ == "__main__":
    # This structure is simple and easy to run directly.
    # To follow the provided README command, this file would typically be renamed
    # to 'cli.py' and placed inside a 'finance_ledger' directory.
    run_cli()
