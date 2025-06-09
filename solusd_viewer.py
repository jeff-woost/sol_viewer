import pandas as pd
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import customtkinter
import matplotlib.pyplot as plt
from solusd_pull import get_binance_data  # Import the function to fetch data

#
customtkinter.set_default_color_theme("dark-blue")  # Set the customtkinter theme
customtkinter.set_appearance_mode("dark")

class DataFrameGUI:
    def __init__(self, df):
        self.original_df = df.copy()  # Store the original DataFrame
        self.df = df
        self.root = customtkinter.CTk()  # Use CTk window for colorful UI
        self.root.title("Crypto Data")
        self.columns = list(df.columns)
        self.dragged_col = None
        self.create_widgets()
        self.populate_tree()
        self.root.mainloop()

    # import matplotlib.pyplot as plt

    def create_widgets(self):
        # Frame for column controls
        col_frame = customtkinter.CTkFrame(self.root, fg_color="#1111A9")
        col_frame.pack(fill="x", padx=5, pady=5)

        # --- Filter controls ---
        customtkinter.CTkLabel(
            col_frame,
            text="Filter Column:",
            text_color="#00FF00"
        ).pack(
            side="left",
            padx=(10, 2)
        )
        self.filter_col_var = tk.StringVar()
        self.filter_col_menu = customtkinter.CTkComboBox(
            col_frame, variable=self.filter_col_var, values=self.columns, width=100, fg_color="#050552",
            command=self.update_filter_values  # Update values when column changes
        )
        self.filter_col_menu.pack(side="left", padx=2)

        customtkinter.CTkLabel(col_frame, text="Filter Value:", text_color="#1C1E1E").pack(side="left")
        self.filter_val_var = tk.StringVar()
        # Dropdown for filter value
        self.filter_val_menu = customtkinter.CTkComboBox(
            col_frame, variable=self.filter_val_var, values=[], width=100, fg_color="#333366"
        )
        self.filter_val_menu.pack(side="left", padx=2)

        filter_btn = customtkinter.CTkButton(
            col_frame, text="Apply Filter", fg_color="#225533", hover_color="#113322", command=self.apply_filter
        )
        filter_btn.pack(side="left", padx=10)
        clear_filter_btn = customtkinter.CTkButton(
            col_frame, text="Clear Filter", fg_color="#444444", hover_color="#222222", command=self.clear_filter
        )
        clear_filter_btn.pack(side="left", padx=2)
        # --- End filter controls ---

        customtkinter.CTkLabel(col_frame, text="Move Column:", text_color="#FFCC00").pack(side="left")
        self.col_var = tk.StringVar()
        self.col_menu = customtkinter.CTkComboBox(col_frame, variable=self.col_var, values=self.columns, width=120, fg_color="#333366")
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
        customtkinter.CTkLabel(col_frame, text="X:", text_color="#FFCC00").pack(side="left", padx=(20, 2))
        self.x_var = tk.StringVar()
        self.x_menu = customtkinter.CTkComboBox(col_frame, variable=self.x_var, values=self.columns, width=100, fg_color="#333366")
        self.x_menu.pack(side="left", padx=2)

        customtkinter.CTkLabel(col_frame, text="Y1:", text_color="#FFCC00").pack(side="left")
        self.y_var = tk.StringVar()
        self.y_menu = customtkinter.CTkComboBox(col_frame, variable=self.y_var, values=self.columns, width=100, fg_color="#333366")
        self.y_menu.pack(side="left", padx=2)

        customtkinter.CTkLabel(col_frame, text="Y2:", text_color="#FFCC00").pack(side="left")
        self.y2_var = tk.StringVar()
        self.y2_menu = customtkinter.CTkComboBox(
            col_frame,
            variable=self.y2_var,
            values=self.columns,
            width=100,
            fg_color="#333366"
        )
        self.y2_menu.pack(side="left", padx=2)

        graph_btn = customtkinter.CTkButton(
            col_frame, text="Line Graph", fg_color="#225533", hover_color="#113322", command=self.plot_line_graph
        )
        graph_btn.pack(side="left", padx=10)
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
                command=lambda c=col: self.sort_by_column(c)
            )
            self.tree.column(col, width=100)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Track sort order for each column
        self._sort_orders = {col: False for col in self.columns}



    def sort_by_column(self, col):
        # Toggle sort order
        self._sort_orders[col] = not self._sort_orders[col]
        ascending = self._sort_orders[col]
        try:
            sorted_df = self.df.sort_values(by=col, ascending=ascending)
        except Exception:
            # If column is not sortable, sort as string
            sorted_df = self.df.astype({col: str}).sort_values(by=col, ascending=ascending)
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
            messagebox.showerror("Error", "Position must be an integer.")
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
        self.df = self.original_df.copy()
        self.columns = list(self.df.columns)
        self.tree['columns'] = self.columns
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.populate_tree()

    def plot_line_graph(self):
        x_col = self.x_var.get()
        y_col = self.y_var.get()
        y2_col = self.y2_var.get()

        # --- Apply filter to chart data if a filter is set ---
        filter_col = self.filter_col_var.get()
        filter_val = self.filter_val_var.get()
        plot_df = self.df
        if filter_col and filter_val and filter_col in plot_df.columns:
            plot_df = plot_df[plot_df[filter_col].astype(str) == filter_val]

        if (
            x_col and y_col
            and x_col in plot_df.columns
            and y_col in plot_df.columns
            and not plot_df.empty
        ):
            fig, ax1 = plt.subplots(figsize=(10, 5))
            line1, = ax1.plot(plot_df[x_col], plot_df[y_col], marker='o', label=y_col)
            ax1.set_xlabel(x_col)
            ax1.set_ylabel(y_col)
            lines = [line1]
            labels = [y_col]

            if y2_col and y2_col in plot_df.columns:
                ax2 = ax1.twinx()
                bars = ax2.bar(plot_df[x_col], plot_df[y2_col], alpha=0.4, color='orange', label=f"{y2_col} (bar)")
                ax2.set_ylabel(f"{y2_col} (bar)")
                lines.append(bars)
                labels.append(f"{y2_col} (bar)")
                ax2.legend(loc='upper right')

            ax1.set_title(
                f"{y_col} (line) vs {x_col}"
                + (f" + {y2_col} (bar)" if y2_col else "")
            )
            ax1.legend(loc='upper left')
            ax1.grid(True)
            fig.tight_layout()

            # --- Add interactive hover ---
            annot = ax1.annotate("", xy=(0,0), xytext=(15,15), textcoords="offset points",
                                 bbox=dict(boxstyle="round", fc="w"),
                                 arrowprops=dict(arrowstyle="->"))
            annot.set_visible(False)

            def update_annot(ind, line, ax):
                x, y = line.get_data()
                idx = ind["ind"][0]
                annot.xy = (x[idx], y[idx])
                text = f"{x_col}: {x[idx]}\n{y_col}: {y[idx]}"
                annot.set_text(text)
                annot.get_bbox_patch().set_facecolor("#ffffcc")
                annot.get_bbox_patch().set_alpha(0.9)

            def hover(event):
                vis = annot.get_visible()
                if event.inaxes == ax1:
                    cont, ind = line1.contains(event)
                    if cont:
                        update_annot(ind, line1, ax1)
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                    else:
                        if vis:
                            annot.set_visible(False)
                            fig.canvas.draw_idle()
                if y2_col and y2_col in plot_df.columns and event.inaxes == ax2:
                    for bar in bars:
                        if bar.contains(event)[0]:
                            idx = list(bars).index(bar)
                            annot.xy = (bar.get_x() + bar.get_width()/2, bar.get_height())
                            text = f"{x_col}: {plot_df[x_col].iloc[idx]}\n{y2_col}: {plot_df[y2_col].iloc[idx]}"
                            annot.set_text(text)
                            annot.get_bbox_patch().set_facecolor("#ffe4b2")
                            annot.set_visible(True)
                            fig.canvas.draw_idle()
                            break
                    else:
                        if vis:
                            annot.set_visible(False)
                            fig.canvas.draw_idle()

            fig.canvas.mpl_connect("motion_notify_event", hover)
            # --- End interactive hover ---

            plt.show()
        else:
            messagebox.showerror("Error", "Please select X and at least one Y column for the graph, and ensure there is data to plot.")

    def update_filter_values(self, event=None):
        col = self.filter_col_var.get()
        if col in self.df.columns:
            unique_vals = self.df[col].dropna().astype(str).unique()
            self.filter_val_menu.configure(values=list(unique_vals))
            if unique_vals.size > 0:
                self.filter_val_var.set(unique_vals[0])
            else:
                self.filter_val_var.set("")

    def apply_filter(self):
        col = self.filter_col_var.get()
        val = self.filter_val_var.get()
        if col and val:
            try:
                filtered_df = self.df[self.df[col].astype(str) == val]
                self.populate_tree(filtered_df)
            except Exception as e:
                messagebox.showerror("Error", f"Filter failed: {e}")
        else:
            messagebox.showerror("Error", "Please select a column and a filter value.")

    def clear_filter(self):
        self.populate_tree(self.df)


class PivotWindow:
    
    def __init__(self, df, columns, on_pivot_done):
        self.df = df
        self.columns = columns
        self.on_pivot_done = on_pivot_done
        self.win = customtkinter.CTkToplevel()
        self.win.title("Custom Pivot and Sum")

        # Multi-select for groupby columns
        customtkinter.CTkLabel(self.win, text="Group by (Index):", text_color="#FFCC00").grid(row=0, column=0, padx=5, pady=5)
        self.index_listbox = tk.Listbox(self.win, selectmode="multiple", exportselection=0, height=min(8, len(columns)), width=18)
        for col in columns:
            self.index_listbox.insert(tk.END, col)
        self.index_listbox.grid(row=0, column=1, padx=5, pady=5)

        # Multi-select for sum value columns
        customtkinter.CTkLabel(self.win, text="Sum Values:", text_color="#FFCC00").grid(row=1, column=0, padx=5, pady=5)
        self.value_listbox = tk.Listbox(self.win, selectmode="multiple", exportselection=0, height=min(8, len(columns)), width=18)
        for col in columns:
            self.value_listbox.insert(tk.END, col)
        self.value_listbox.grid(row=1, column=1, padx=5, pady=5)

        pivot_btn = customtkinter.CTkButton(self.win, text="Pivot & Sum", fg_color="#90ee90", command=self.do_pivot)
        pivot_btn.grid(row=2, column=0, columnspan=2, pady=10)

        self.result_tree = None

    def do_pivot(self):
        # Get selected indices for groupby and sum columns
        index_indices = self.index_listbox.curselection()
        value_indices = self.value_listbox.curselection()
        index_cols = [self.columns[i] for i in index_indices]
        value_cols = [self.columns[i] for i in value_indices]
        if index_cols and value_cols:
            try:
                pivot_df = self.df.groupby(index_cols)[value_cols].sum().reset_index()
                if self.result_tree:
                    self.result_tree.destroy()
                self.result_tree = ttk.Treeview(self.win, columns=list(pivot_df.columns), show='headings')
                for col in pivot_df.columns:
                    self.result_tree.heading(col, text=col)
                    self.result_tree.column(col, width=120)
                for _, row in pivot_df.iterrows():
                    self.result_tree.insert('', tk.END, values=list(row))
                self.result_tree.grid(row=3, column=0, columnspan=2, padx=5, pady=5)
                self.on_pivot_done(pivot_df)
            except Exception as e:
                messagebox.showerror("Error", f"Pivot failed: {e}")
        else:
            messagebox.showerror("Error", "Please select at least one groupby and one sum column.")



if __name__ == "__main__":
    df = get_binance_data(['SOLUSDT','BTCUSD','ETCUSD','JUPUSD'], '1d', 365)  # Fetch data for SOLUSDT
    DataFrameGUI(df)