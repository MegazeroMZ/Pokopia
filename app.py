import tkinter as tk
from tkinter import ttk, messagebox
from pokedata import load_data, search_by_name, filter_by_specialty, filter_by_favorite, sort_records, related_by_habitat, group_by_favorite
from pathlib import Path
import sys


# Locate the CSV whether running from source or from a PyInstaller bundle.
# When bundled with PyInstaller --onefile the files are extracted to
# sys._MEIPASS at runtime. Fall back to the script directory otherwise.
_base_dir = Path(getattr(sys, '_MEIPASS', Path(__file__).parent))
CSV_PATH = _base_dir / 'Pokopia.csv'


class PokopiaApp(tk.Tk):
    def __init__(self, data):
        super().__init__()
        self.title('Pokopia Explorer')
        self.geometry('1000x600')
        self.data = data
        self.filtered = list(data)
        self.create_widgets()

    def create_widgets(self):
        # overall layout: left=filters, right=results
        container = ttk.Frame(self)
        container.pack(fill='both', expand=True, padx=8, pady=6)

        left = ttk.Frame(container)
        left.pack(side='left', fill='y', padx=(0, 8))

        right = ttk.Frame(container)
        right.pack(side='right', fill='both', expand=True)

        # status/count label
        self.count_var = tk.StringVar(value='')

        # Name search
        ttk.Label(left, text='Search Pokemon name:').pack(anchor='w')
        self.search_var = tk.StringVar()
        ttk.Entry(left, textvariable=self.search_var, width=30).pack(anchor='w', pady=2)

        # Specialty (checkbox + combobox editable)
        self.spec_check = tk.BooleanVar(value=False)
        ttk.Checkbutton(left, text='Enable specialty filter', variable=self.spec_check).pack(anchor='w', pady=(8,0))
        self.spec_var = tk.StringVar()
        self.spec_combo = ttk.Combobox(left, textvariable=self.spec_var, values=[], width=30)
        self.spec_combo.pack(anchor='w', pady=2)
        self.spec_combo.configure(state='normal')

        # Favorite (checkbox + combobox editable)
        self.fav_check = tk.BooleanVar(value=False)
        ttk.Checkbutton(left, text='Enable favorite filter', variable=self.fav_check).pack(anchor='w', pady=(8,0))
        self.fav_var = tk.StringVar()
        self.fav_combo = ttk.Combobox(left, textvariable=self.fav_var, values=[], width=30)
        self.fav_combo.pack(anchor='w', pady=2)

        # Ideal habitat (checkbox + combobox editable)
        self.ideal_check = tk.BooleanVar(value=False)
        ttk.Checkbutton(left, text='Enable ideal habitat filter', variable=self.ideal_check).pack(anchor='w', pady=(8,0))
        self.ideal_var = tk.StringVar()
        self.ideal_combo = ttk.Combobox(left, textvariable=self.ideal_var, values=[], width=30)
        self.ideal_combo.pack(anchor='w', pady=2)

        # Sort controls
        ttk.Label(left, text='Sort by:').pack(anchor='w', pady=(12,0))
        self.sort_var = tk.StringVar()
        sort_columns = ['Number', 'Name', 'Primary Location', 'Ideal Habitat', 'specialties', 'favorites', 'Litter drop item', 'habitats']
        ttk.Combobox(left, textvariable=self.sort_var, values=sort_columns, width=30).pack(anchor='w', pady=2)
        self.sort_rev = tk.BooleanVar()
        ttk.Checkbutton(left, text='Descending', variable=self.sort_rev).pack(anchor='w')

        # Action buttons
        ttk.Button(left, text='Search', command=self.on_search_all).pack(anchor='w', pady=(12,4))
        ttk.Button(left, text='Reset', command=self.on_reset).pack(anchor='w')

        # Treeview in right pane
        cols = ['Number', 'Name', 'Primary Location', 'Ideal Habitat', 'specialties', 'favorites', 'Litter drop item', 'habitats']
        self.tree = ttk.Treeview(right, columns=cols, show='headings')
        for c in cols:
            # make the heading clickable to sort by this column
            self.tree.heading(c, text=c, command=lambda _c=c: self._on_heading_click(_c))
            self.tree.column(c, width=140, anchor='w')
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<Double-1>', self.on_open_details)

        # bottom details / actions
        bottom = ttk.Frame(self)
        bottom.pack(fill='x', padx=8, pady=6)

        # Instruction text above the action buttons
        ttk.Label(
            bottom,
            text="Please select a Pokémon before clicking one of these buttons.",
            foreground='gray'
        ).pack(side='top', fill='x', pady=(0, 4))

        # Put the action buttons in their own sub-frame so the label sits above them
        btn_frame = ttk.Frame(bottom)
        btn_frame.pack(side='left')

        ttk.Button(btn_frame, text='Show selected details', command=self.on_open_details).pack(side='left')
        ttk.Button(btn_frame, text='Related by habitat', command=self.on_related).pack(side='left', padx=6)
        ttk.Button(btn_frame, text='Group related by favorite', command=self.on_group_fav).pack(side='left')
        ttk.Label(bottom, textvariable=self.count_var).pack(side='right')

        # populate combobox choices from data
        self._populate_filter_choices()

        self.populate_tree(self.filtered)

    def _on_heading_click(self, column: str):
        # Toggle sort order when the same column is clicked repeatedly
        prev = getattr(self, '_last_sort_col', None)
        rev = getattr(self, '_last_sort_rev', False)
        if prev == column:
            rev = not rev
        else:
            rev = False
        self._last_sort_col = column
        self._last_sort_rev = rev

        # Apply sort to the currently displayed rows
        try:
            rows = list(self.filtered)
        except Exception:
            rows = list(self.data)
        rows = sort_records(rows, column, reverse=rev)
        # update sort controls to reflect this
        try:
            self.sort_var.set(column)
            self.sort_rev.set(rev)
        except Exception:
            pass
        self.filtered = rows
        self.populate_tree(self.filtered)

    def populate_tree(self, rows):
        # Remember which rows are currently displayed so other actions (like
        # sorting via header click) operate only on this subset instead of the
        # full dataset.
        try:
            self.filtered = rows
        except Exception:
            pass

        for i in self.tree.get_children():
            self.tree.delete(i)
        for r in rows:
            vals = [
                r.get('Number', ''),
                r.get('Name', ''),
                r.get('Primary Location', ''),
                # Prefer the original CSV 'Ideal Habitat' value if present, otherwise use normalized field
                r.get('Ideal Habitat', '') or r.get('ideal_habitat', ''),
                ','.join(r.get('specialties', [])),
                ','.join(r.get('favorites', [])),
                r.get('Litter drop item', ''),
                ','.join(r.get('habitats', [])),
            ]
            self.tree.insert('', 'end', values=vals)
        # update count: number of displayed rows and total dataset size
        try:
            total = len(self.data)
        except Exception:
            total = 0
        self.count_var.set(f'Showing {len(rows)} of {total}')

    def _populate_filter_choices(self):
        # collect unique specialties, favorites, and ideal habitats from dataset
        specs = set()
        favs = set()
        ideals = set()
        for r in self.data:
            for s in r.get('specialties', []):
                specs.add(s)
            for f in r.get('favorites', []):
                favs.add(f)
            ih = (r.get('ideal_habitat') or '').strip()
            if ih:
                ideals.add(ih)
        spec_list = sorted(x for x in specs if x)
        fav_list = sorted(x for x in favs if x)
        ideal_list = sorted(x for x in ideals if x)
        self.spec_combo['values'] = spec_list
        self.fav_combo['values'] = fav_list
        self.ideal_combo['values'] = ideal_list

    def on_search_all(self):
        rows = list(self.data)
        # name filter (always applied if present)
        name_q = (self.search_var.get() or '').strip()
        if name_q:
            rows = [r for r in rows if name_q.lower() in r.get('name_lower', '')]

        # specialty
        if getattr(self, 'spec_check', None) and self.spec_check.get():
            rows = filter_by_specialty(rows, self.spec_var.get().strip())

        # favorite
        if getattr(self, 'fav_check', None) and self.fav_check.get():
            rows = filter_by_favorite(rows, self.fav_var.get().strip())

        # ideal habitat
        if getattr(self, 'ideal_check', None) and self.ideal_check.get():
            from pokedata import filter_by_ideal_habitat
            rows = filter_by_ideal_habitat(rows, self.ideal_var.get().strip())

        # sorting is always applied after filtering
        sortc = (self.sort_var.get() or '').strip()
        if sortc:
            rows = sort_records(rows, sortc, reverse=self.sort_rev.get())

        self.filtered = rows
        self.populate_tree(self.filtered)

    def on_reset(self):
        # clear filters and show all
        self.search_var.set('')
        if getattr(self, 'spec_check', None):
            self.spec_check.set(False)
        if getattr(self, 'fav_check', None):
            self.fav_check.set(False)
        if getattr(self, 'ideal_check', None):
            self.ideal_check.set(False)
        self.spec_var.set('')
        self.fav_var.set('')
        self.ideal_var.set('')
        self.filtered = list(self.data)
        # apply sort if any
        sortc = (self.sort_var.get() or '').strip()
        if sortc:
            self.filtered = sort_records(self.filtered, sortc, reverse=self.sort_rev.get())
        self.populate_tree(self.filtered)

    def on_search(self):
        q = self.search_var.get()
        if not q:
            messagebox.showinfo('Info', 'Enter a name to search (partial ok).')
            return
        found = search_by_name(self.data, q)
        self.filtered = found
        self.populate_tree(self.filtered)

    def on_search_specialty(self):
        q = self.spec_var.get().strip()
        if not q:
            messagebox.showinfo('Info', 'Enter a specialty to search.')
            return
        found = filter_by_specialty(self.data, q)
        self.filtered = found
        self.populate_tree(self.filtered)

    def on_search_favorite(self):
        q = self.fav_var.get().strip()
        if not q:
            messagebox.showinfo('Info', 'Enter a favorite to search.')
            return
        found = filter_by_favorite(self.data, q)
        self.filtered = found
        self.populate_tree(self.filtered)

    def on_search_ideal(self):
        q = self.ideal_var.get().strip()
        if not q:
            messagebox.showinfo('Info', 'Enter an ideal habitat to search.')
            return
        # import local function to avoid circular references
        from pokedata import filter_by_ideal_habitat
        found = filter_by_ideal_habitat(self.data, q)
        self.filtered = found
        self.populate_tree(self.filtered)

    def apply_filters(self):
        rows = list(self.data)
        spec = self.spec_var.get().strip()
        fav = self.fav_var.get().strip()
        if spec:
            rows = filter_by_specialty(rows, spec)
        if fav:
            rows = filter_by_favorite(rows, fav)
        sortc = self.sort_var.get().strip()
        if sortc:
            rows = sort_records(rows, sortc, reverse=self.sort_rev.get())
        self.filtered = rows
        self.populate_tree(self.filtered)

    def get_selected_record(self):
        sel = self.tree.selection()
        if not sel:
            return None
        vals = self.tree.item(sel[0], 'values')
        name = vals[1]
        for r in self.data:
            if r.get('Name') == name:
                return r
        return None

    def on_open_details(self, event=None):
        rec = self.get_selected_record()
        if not rec:
            messagebox.showinfo('Info', 'Select a row first')
            return
        txt = ''
        for k, v in rec.items():
            if k in ('specialties','favorites','habitats','name_lower'):
                continue
            txt += f"{k}: {v}\n"
        DetailsWindow(self, title=rec.get('Name','Details'), text=txt)

    def on_related(self):
        rec = self.get_selected_record()
        if not rec:
            messagebox.showinfo('Info', 'Select a row first')
            return
        related = related_by_habitat(self.data, rec)
        self.populate_tree(related)

    def on_group_fav(self):
        rec = self.get_selected_record()
        if not rec:
            messagebox.showinfo('Info', 'Select a row first')
            return
        related = related_by_habitat(self.data, rec)
        groups = group_by_favorite(related)
        # show a simple popup with groups
        out = ''
        for fav, items in sorted(groups.items(), key=lambda x: -len(x[1])):
            out += f"{fav} ({len(items)}): {', '.join(i.get('Name','') for i in items)}\n\n"
        DetailsWindow(self, title=f"Grouped by favorite (related to {rec.get('Name')})", text=out)


class DetailsWindow(tk.Toplevel):
    def __init__(self, parent, title='Details', text=''):
        super().__init__(parent)
        self.title(title)
        self.geometry('640x480')
        txt = tk.Text(self, wrap='word')
        txt.insert('1.0', text)
        txt.config(state='disabled')
        txt.pack(fill='both', expand=True)


def main():
    data = load_data(str(CSV_PATH))
    app = PokopiaApp(data)
    app.mainloop()


if __name__ == '__main__':
    main()
