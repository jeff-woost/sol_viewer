try:
    import pandas as pd
    from datetime import datetime, timedelta
    import tkinter as tk
    from tkinter import ttk, simpledialog, messagebox
    import customtkinter
    import matplotlib
    matplotlib.use("TkAgg")  # Ensure Tkinter backend for matplotlib
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.pyplot as plt
    from solusd_pull import get_binance_data  # Import the function to fetch data
    import tkinter.filedialog as filedialog
    import functools  # <-- Add this import
except ImportError as e:
    print(f"Missing dependency: {e}. Please install the required package and try again.")
    raise

#
customtkinter.set_default_color_theme("dark-blue")  # Set the customtkinter theme
customtkinter.set_appearance_mode("dark")

class DataFrameGUI:
    def __init__(self, df):
        self.original_df = df  # Store a reference to the original DataFrame
        self.df = df
        self.unique_values_cache = {}  # Cache for unique values
        self.root = customtkinter.CTk()  # Use CTk window for colorful UI
        self.root.title("Crypto Data")
        if isinstance(df, pd.DataFrame) and not df.empty:
            self.columns = list(df.columns)
        else:
            messagebox.showerror("Error", "Invalid or empty DataFrame provided.")
            self.root.destroy()
            return
        self.dragged_col = None
        self.create_widgets()
        self.update_filter_values()  # Ensure filter values are initialized
        self.populate_tree()
        self.root.mainloop()


    def create_widgets(self):
        # Frame for column controls
        col_frame = customtkinter.CTkFrame(self.root, fg_color="#1111A9")
        col_frame.pack(fill="x", padx=5, pady=5)
        
        #Export to Excel button

        # --- Add Export to Excel button here ---
        export_excel_btn = customtkinter.CTkButton(
            col_frame,
            text="Export to Excel",
            fg_color="#1976D2",
            hover_color="#0D47A1",
            command=self.export_current_view_to_excel
        )
        export_excel_btn.pack(side="left", padx=2)

        # --- Filter controls ---
        customtkinter.CTkLabel(
            col_frame,
            text="Filter Column:",
            text_color="#00FF00"
        ).pack(side="left", padx=(10, 2))
        self.filter_col_var = tk.StringVar()
        self.filter_col_menu = customtkinter.CTkComboBox(
            col_frame,
            variable=self.filter_col_var,
            values=self.columns,
            width=100,
            fg_color="#050552",
            command=self.update_filter_values
        )
        self.filter_col_menu.pack(side="left", padx=2)

        # Filter mode dropdown
        self.filter_mode_var = tk.StringVar(value="Include")
        self.filter_mode_menu = customtkinter.CTkComboBox(
            col_frame,
            variable=self.filter_mode_var,
            values=["Include", "Exclude", "Is Like"],
            width=80,
            fg_color="#333366",
            command=self.update_filter_mode
        )
        self.filter_mode_menu.pack(side="left", padx=2)

        # Multi-select Listbox for include/exclude
        self.filter_val_listbox = tk.Listbox(
            col_frame,
            selectmode="multiple",
            exportselection=0,
            height=5,
            width=15
        )
        self.filter_val_listbox.pack(side="left", padx=2)

        # Entry for "Is Like"
        self.islike_entry = customtkinter.CTkEntry(
            col_frame,
            width=100,
            fg_color="#333366"
        )
        self.islike_entry.pack(side="left", padx=2)
        self.islike_entry.pack_forget()  # Hide initially

        filter_btn = customtkinter.CTkButton(
            col_frame, text="Apply Filter", fg_color="#225533", hover_color="#113322", command=self.apply_filter
        )
        filter_btn.pack(side="left", padx=10)
        clear_filter_btn = customtkinter.CTkButton(
            col_frame,
            text="Clear Filter",
            fg_color="#444444",
            hover_color="#222222",
            command=self.clear_filter
        )
        clear_filter_btn.pack(side="left", padx=2)
        # --- End filter controls ---

        customtkinter.CTkLabel(col_frame, text="Move Column:", text_color="#FFCC00").pack(side="left")
        self.col_var = tk.StringVar()
        self.col_menu = customtkinter.CTkComboBox(
            col_frame,
            variable=self.col_var,
            values=self.columns,
            width=120,
            fg_color="#333366"
        )
        self.col_menu.pack(side="left", padx=2)

        customtkinter.CTkLabel(col_frame, text="To Position:", text_color="#FFCC00").pack(side="left")
        self.pos_var = tk.IntVar()
        self.pos_spin = customtkinter.CTkEntry(col_frame, textvariable=self.pos_var, width=50, fg_color="#333366")
        self.pos_spin.pack(side="left", padx=2)

        move_btn = customtkinter.CTkButton(
            col_frame, text="Move", fg_color="#225533", hover_color="#113322", command=self.move_column
        )
        move_btn.pack(side="left", padx=2)

        pivot_btn = customtkinter.CTkButton(
            col_frame, text="Pivot/Sum", fg_color="#225533", hover_color="#113322", command=self.open_pivot_window
        )
        pivot_btn.pack(side="left", padx=10)

        unpivot_btn = customtkinter.CTkButton(
            col_frame, text="Return to Original Table", fg_color="#665544", hover_color="#332211", command=self.unpivot
        )
        unpivot_btn.pack(side="left", padx=10)

        # --- Add graph controls ---
        customtkinter.CTkLabel(col_frame, text="X Axis (select one or more):", text_color="#FFCC00").pack(side="left", padx=(20, 2))
        self.x_listbox = tk.Listbox(col_frame, selectmode="multiple", exportselection=0, height=min(6, len(self.columns)), width=12)
        for col in self.columns:
            self.x_listbox.insert(tk.END, col)
        self.x_listbox.pack(side="left", padx=2)

        customtkinter.CTkLabel(col_frame, text="Y Axis (select one or more):", text_color="#FFCC00").pack(side="left")
        self.y_listbox = tk.Listbox(col_frame, selectmode="multiple", exportselection=0, height=min(6, len(self.columns)), width=12)
        for col in self.columns:
            self.y_listbox.insert(tk.END, col)
        self.y_listbox.pack(side="left", padx=2)

        graph_btn = customtkinter.CTkButton(
            col_frame, text="Line Graph", fg_color="#225533", hover_color="#113322", command=lambda: self.plot_graph("line")
        )
        graph_btn.pack(side="left", padx=2)
        bar_btn = customtkinter.CTkButton(
            col_frame, text="Bar Chart", fg_color="#225533", hover_color="#113322", command=lambda: self.plot_graph("bar")
        )
        bar_btn.pack(side="left", padx=2)
        # --- End graph controls ---

        # Data table (still ttk for best compatibility)
        self.frame = ttk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(
            self.frame,
            columns=self.columns,
            show='headings'
        )
        for col in self.columns:
            self.tree.heading(
                col,
                text=col,
                command=functools.partial(self.sort_by_column, col)
            )
            self.tree.column(col, width=100)
        self.tree.pack(fill=tk.BOTH, expand=True)
        # Add right-click menu for export
        self.tree_menu = tk.Menu(self.tree, tearoff=0)
        self.tree_menu.add_command(label="Export as CSV", command=self.export_current_view_to_csv)
        self.tree_menu.add_command(label="Export as Excel", command=self.export_current_view_to_excel)
        self.tree.bind("<Button-3>", self.show_tree_menu)  # Right-click

        # Track sort order for each column
        self._sort_orders = {col: False for col in self.columns}

        # --- Add cell selection binding ---
        self.tree.bind("<Button-1>", self.on_tree_cell_click)

    # (Intentionally left blank to remove the duplicate method)

    def sort_by_column(self, col):
        # Toggle sort order for the column
        self._sort_orders[col] = not self._sort_orders[col]
        ascending = self._sort_orders[col]
        try:
            # Try numeric sort first
            sorted_df = self.df.copy()
            sorted_df[col] = pd.to_numeric(sorted_df[col], errors='ignore')
            sorted_df = sorted_df.sort_values(by=col, ascending=ascending, kind='mergesort')
        except Exception:
            # Fallback to string sort
            sorted_df = self.df.astype({col: str}).sort_values(by=col, ascending=ascending, kind='mergesort')
        self.populate_tree(sorted_df)

    def populate_tree(self, df=None):
        if df is None:
            df = self.df
        for row in self.tree.get_children():
            self.tree.delete(row)
        for _, row in df.iterrows():
            self.tree.insert('', tk.END, values=[row[col] for col in self.columns])

    def move_column(self):
        col = self.col_var.get()
        try:
            pos = int(self.pos_var.get()) - 1
        except Exception:
            messagebox.showerror("Error", "Invalid input for position. Please enter a numeric value representing the column's new position.")
            return
        if col in self.columns and 0 <= pos < len(self.columns):
            self.columns.remove(col)
            self.columns.insert(pos, col)
            # Reconfigure treeview columns
            self.tree['columns'] = self.columns
            for colname in self.columns:
                self.tree.heading(colname, text=colname)
                self.tree.column(colname, width=100)
            self.populate_tree()
        else:
            messagebox.showerror("Error", "Invalid column or position.")

    def open_pivot_window(self):
        PivotWindow(self.df, self.columns, self.on_pivot_done)

    def on_pivot_done(self, pivot_df):
        self.df = pivot_df
        self.columns = list(pivot_df.columns)
        self.tree['columns'] = self.columns
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.populate_tree()

    def unpivot(self):
        self.df = self.original_df
        self.columns = list(self.df.columns)
        self.tree['columns'] = self.columns
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.populate_tree()

    def plot_graph(self, chart_type="line"):
        # Get selected x and y columns
        x_indices = self.x_listbox.curselection()
        y_indices = self.y_listbox.curselection()
        x_cols = [self.columns[i] for i in x_indices]
        y_cols = [self.columns[i] for i in y_indices]

        # Use filtered data if available, else self.df
        plot_df = self.df.copy()
        if len(self.tree.get_children()) != len(self.df):
            rows = []
            for item in self.tree.get_children():
                values = self.tree.item(item)["values"]
                rows.append(values)
            plot_df = pd.DataFrame(rows, columns=self.columns)
            for col in plot_df.columns:
                if not pd.api.types.is_numeric_dtype(plot_df[col]):
                    try:
                        plot_df[col] = pd.to_numeric(plot_df[col], errors="coerce")
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to convert column '{col}' to numeric: {e}")
                        return

        if x_cols and y_cols and not plot_df.empty:
            # Convert X and Y columns to numeric if possible
            for col in x_cols + y_cols:
                plot_df[col] = pd.to_numeric(plot_df[col], errors="ignore")

            fig, ax = plt.subplots(figsize=(10, 5))
            for y_col in y_cols:
                for x_col in x_cols:
                    if x_col in plot_df.columns and y_col in plot_df.columns:
                        # Only plot if y_col is numeric
                        if pd.api.types.is_numeric_dtype(plot_df[y_col]) and pd.api.types.is_numeric_dtype(plot_df[x_col]):
                            if chart_type == "line":
                                ax.plot(plot_df[x_col], plot_df[y_col], marker='o', label=f"{y_col} vs {x_col}")
                            elif chart_type == "bar":
                                ax.bar(plot_df[x_col], plot_df[y_col], label=f"{y_col} vs {x_col}")
                        else:
                            messagebox.showerror("Error", f"Column '{y_col}' or '{x_col}' is not numeric and cannot be plotted.")
                            return
            ax.set_xlabel(", ".join(x_cols))
            ax.set_ylabel(", ".join(y_cols))
            ax.set_title(f"{' & '.join(y_cols)} vs {' & '.join(x_cols)}")
            ax.legend(loc='best')
            ax.grid(True)
            fig.tight_layout()

            # --- Show in new Tkinter window ---
            graph_win = customtkinter.CTkToplevel(self.root)
            graph_win.title("Chart")
            canvas = FigureCanvasTkAgg(fig, master=graph_win)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            close_btn = customtkinter.CTkButton(graph_win, text="Close", command=graph_win.destroy)
            close_btn.pack(pady=5)
        else:
            messagebox.showerror("Error", "Please select at least one X and one Y column for the graph, and ensure there is data to plot.")

    def update_filter_values(self, event=None):
        col = self.filter_col_var.get()
        if col in self.df.columns:
            if col not in self.unique_values_cache:
                self.unique_values_cache[col] = self.df[col].dropna().astype(str).unique()
            unique_vals = self.unique_values_cache[col]
            self.filter_val_listbox.delete(0, tk.END)
            for val in unique_vals:
                self.filter_val_listbox.insert(tk.END, val)

    def update_filter_mode(self, event=None):
        mode = self.filter_mode_var.get()
        if mode == "Is Like":
            self.filter_val_listbox.pack_forget()
            self.islike_entry.pack(side="left", padx=2)
        else:
            self.islike_entry.pack_forget()
            self.filter_val_listbox.pack(side="left", padx=2)

    def apply_filter(self):
        col = self.filter_col_var.get()
        mode = self.filter_mode_var.get()
        if not col:
            messagebox.showerror("Error", "Please select a column to filter.")
            return

        if mode == "Include":
            selected_indices = self.filter_val_listbox.curselection()
            if not selected_indices:
                messagebox.showerror("Error", "Select at least one value to include.")
                return
            selected_vals = [self.filter_val_listbox.get(i) for i in selected_indices]
            filtered_df = self.df[self.df[col].astype(str).isin(selected_vals)]
            self.populate_tree(filtered_df)
        elif mode == "Exclude":
            selected_indices = self.filter_val_listbox.curselection()
            if not selected_indices:
                messagebox.showerror("Error", "Select at least one value to exclude.")
                return
            selected_vals = [self.filter_val_listbox.get(i) for i in selected_indices]
            filtered_df = self.df[~self.df[col].astype(str).isin(selected_vals)]
            self.populate_tree(filtered_df)
        elif mode == "Is Like":
            keyword = self.islike_entry.get()
            if not keyword:
                messagebox.showerror("Error", "Enter a keyword for 'Is Like' filter.")
                return
            filtered_df = self.df[self.df[col].astype(str).str.contains(keyword, case=False, na=False)]
            self.populate_tree(filtered_df)
        else:
            messagebox.showerror("Error", "Unknown filter mode.")

    def clear_filter(self):
        self.df = self.original_df.copy()
        self.update_filter_values()
        self.populate_tree(self.df)

    def on_tree_cell_click(self, event):
        # Identify the region and column
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            row_id = self.tree.identify_row(event.y)
            col_id = self.tree.identify_column(event.x)
            col_index = int(col_id.replace("#", "")) - 1
            if row_id and 0 <= col_index < len(self.columns):
                col_name = self.columns[col_index]
                item = self.tree.item(row_id)
                cell_value = item["values"][col_index]
                # You can now do something with (row_id, col_name, cell_value)
                print(f"Clicked cell: Row={row_id}, Column={col_name}, Value={cell_value}")
                # Optional: visually highlight the cell (requires custom drawing)
        # Prevent row selection highlight
        return "break"

    def show_tree_menu(self, event):
        try:
            self.tree_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.tree_menu.grab_release()

    def export_current_view_to_csv(self):
        # Gather data from current table view
        rows = []
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            rows.append(values)
        export_df = pd.DataFrame(rows, columns=self.columns)
        # Ask user for file path
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save table as CSV"
        )
        if file_path:
            try:
                export_df.to_csv(file_path, index=False)
                messagebox.showinfo("Export Successful", f"Table exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Could not export CSV:\n{e}")
        # (Export to Excel button moved to right-click menu)

    def export_current_view_to_excel(self):
        # Gather data from current table view
        rows = []
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            rows.append(values)
        export_df = pd.DataFrame(rows, columns=self.columns)
        # Ask user for file path
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Save table as Excel"
        )
        if file_path:
            try:
                export_df.to_excel(file_path, index=False)
                messagebox.showinfo("Export Successful", f"Table exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Could not export Excel file:\n{e}")

class PivotWindow:
    
    def __init__(self, df, columns, on_pivot_done):
        self.df = df
        self.columns = columns
        self.on_pivot_done = on_pivot_done
        self.win = customtkinter.CTkToplevel()
        self.win.title("Custom Pivot and Sum")

        # Multi-select for groupby columns
        customtkinter.CTkLabel(self.win, text="Group by (Index):", text_color="#FFCC00").grid(row=0, column=0, padx=5, pady=5)
        self.index_listbox = tk.Listbox(
            self.win,
            selectmode="multiple",
            exportselection=0,
            height=min(8, len(columns)),
            width=18
        )
        for col in columns:
            self.index_listbox.insert(tk.END, col)
        self.index_listbox.grid(row=0, column=1, padx=5, pady=5)

        # Multi-select for sum value columns
        customtkinter.CTkLabel(
            self.win,
            text="Sum Values:",
            text_color="#FFCC00"
        ).grid(row=1, column=0, padx=5, pady=5)
        self.value_listbox = tk.Listbox(
            self.win,
            selectmode="multiple",
            exportselection=0,
            height=min(8, len(columns)),
            width=18)
        for col in columns:
            self.value_listbox.insert(
                tk.END,
                col
            )
        self.value_listbox.grid(
            row=1,
            column=1,
            padx=5,
            pady=5
        )

        pivot_btn = customtkinter.CTkButton(self.win,
            text="Pivot & Sum",
            fg_color="#90ee90",
            command=self.do_pivot)
        pivot_btn.grid(row=2,
            column=0,
            columnspan=2,
            pady=10)

        self.result_tree = None

    def do_pivot(self):
        # Get selected indices for groupby and sum columns
        index_indices = self.index_listbox.curselection()
        value_indices = self.value_listbox.curselection()
        index_cols = [self.columns[i] for i in index_indices]
        value_cols = [self.columns[i] for i in value_indices]
        if index_cols and value_cols:
            missing_index_cols = [col for col in index_cols if col not in self.df.columns]
            missing_value_cols = [col for col in value_cols if col not in self.df.columns]

            if missing_index_cols or missing_value_cols:
                messagebox.showerror(
                    "Error",
                    f"Invalid columns selected.\nMissing groupby columns: {missing_index_cols}\nMissing sum columns: {missing_value_cols}"
                )
                return

            try:
                pivot_df = self.df.groupby(index_cols)[value_cols].sum().reset_index()
                if self.result_tree:
                    self.result_tree.destroy()
                self.result_tree = ttk.Treeview(
                    self.win,
                    columns=list(pivot_df.columns),
                    show='headings')
                for col in pivot_df.columns:
                    self.result_tree.heading(col, text=col)
                    self.result_tree.column(col, width=120)
                for _, row in pivot_df.iterrows():
                    self.result_tree.insert(
                        '', tk.END, values=list(row)
                    )
                self.result_tree.grid(row=3, column=0, columnspan=2, padx=5, pady=5)
                self.on_pivot_done(pivot_df)
            except Exception as e:
                messagebox.showerror("Error", f"Pivot failed: {e}")
        else:
            messagebox.showerror("Error", "Please select at least one groupby and one sum column.")

#Add main statement to test the GUI

if __name__ == "__main__":
    try:
        df = get_binance_data(['SOLUSDT', 'BTCUSDT', 'ETCUSDT', 'JUPUSDT', 'ETHUSDT', 'XRPUSDT'], '1d', 365)  # Fetch data for SOLUSDT
        if df is not None and not df.empty:
            DataFrameGUI(df)
        else:
            messagebox.showerror("Error", "Failed to fetch data or received empty DataFrame.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while fetching data: {e}")
