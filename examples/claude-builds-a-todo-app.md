# Claude Builds a Todo App

**Task given:** `INITIAL_TASK="build a working todo app"`
**Session length:** ~25 turns
**Model:** claude-opus-4-6

The agent was given a simple, open-ended task. No language, no framework, no constraints. This excerpt shows how it plans, decides, builds, tests, and reflects.

---

*Turn 1 — 09:14:02*

A todo app. Simple enough on the surface, but there are choices to make: CLI or web? What language? What persistence mechanism?

I'll go with Python and a CLI interface — it fits the environment, has no dependencies, and will actually run here. I'll store data as JSON.

Let me sketch the interface first before writing any code:

```
todo add "buy groceries"
todo list
todo done 1
todo remove 1
todo clear
```

Clean. I'll implement that.

---

*Turn 2 — 09:14:19*

> **Tool: write_file**
> `todo.py` (2341 bytes)
>
> ```
> Wrote 2341 bytes to todo.py
> ```

> **Tool: run_command**
> `python3 todo.py add "buy groceries" && python3 todo.py add "read a book" && python3 todo.py list`
>
> ```
> Added: buy groceries
> Added: read a book
>
> Todo List:
>   [ ] 1. buy groceries
>   [ ] 2. read a book
> ```

Working. Let me test completion and removal.

> **Tool: run_command**
> `python3 todo.py done 1 && python3 todo.py list`
>
> ```
> Marked done: buy groceries
>
> Todo List:
>   [x] 1. buy groceries
>   [ ] 2. read a book
> ```

---

*Turn 3 — 09:14:51*

> **Tool: run_command**
> `python3 todo.py remove 1 && python3 todo.py list`
>
> ```
> Removed: buy groceries
>
> Todo List:
>   [ ] 1. read a book
> ```

> **Tool: run_command**
> `python3 todo.py help`
>
> ```
> Usage: todo.py <command> [args]
> Commands:
>   add <item>   Add a new todo item
>   list         List all items
>   done <id>    Mark item as done
>   remove <id>  Remove an item
>   clear        Clear all items
> ```

The app works. IDs renumber correctly after removal, help text is clear, data persists in `todos.json`.

---

*Turn 5 — 09:16:38*

I realize I should test edge cases — what happens with an invalid ID? What if the file is missing?

> **Tool: run_command**
> `python3 todo.py done 99`
>
> ```
> Error: No item with ID 99
> ```

Good, it handles that gracefully.

> **Tool: run_command**
> `rm todos.json && python3 todo.py list`
>
> ```
> Todo List:
>   (empty)
> ```

Clean startup from no file. The app is solid.

---

*Turn 7 — 09:19:04*

One thing I want to add: due dates. `todo add "call dentist" --due 2024-03-15`. Useful, not over-engineered.

> **Tool: write_file**
> `todo.py` (3102 bytes)
>
> ```
> Wrote 3102 bytes to todo.py
> ```

> **Tool: run_command**
> `python3 todo.py add "call dentist" --due 2024-03-15 && python3 todo.py list`
>
> ```
> Added: call dentist (due: 2024-03-15)
>
> Todo List:
>   [ ] 1. call dentist  [due: 2024-03-15]
> ```

---

*Turn 10 — 09:23:17*

The app is complete and working. Let me write a brief README in the workspace so anyone looking at the directory knows what's here.

> **Tool: write_file**
> `README.md` (487 bytes)
>
> ```
> Wrote 487 bytes to README.md
> ```

And update notes for future runs:

> **Tool: write_notes**
> (318 bytes)
>
> ```
> Notes saved (318 bytes)
> ```

The notes:

> Built a todo CLI app in Python. It's in `workspace/todo.py`. Run it with `python3 todo.py help`. Supports add, list, done, remove, clear, and optional --due dates. Data stored in `workspace/todos.json`.

I'm done. The task was clear, the implementation is clean, and it actually works.

DONE

---

*Loop ended by model after 10 turns.*
*Token usage — input: 28,441, output: 4,872, total: 33,313*
