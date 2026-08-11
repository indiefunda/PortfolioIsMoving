#!/usr/bin/env python3
"""
PortfolioIsMoving - GUI to manage your monitored stock portfolio.

A simple desktop window (built-in Tkinter, no extra install) to:
  - Add / remove tickers
  - Set the movement threshold (%)
  - Save your portfolio
  - Enable / disable monitoring

Uses only the Python standard library (tkinter, json).
"""

import json
import os
import tkinter as tk
from tkinter import messagebox, ttk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config_local.json")

DEFAULT_CONFIG = {
    "tickers": [],
    "threshold_pct": 5.0,
    "enabled": False,
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            # merge with defaults
            merged = dict(DEFAULT_CONFIG)
            merged.update(cfg)
            return merged
        except Exception:
            return dict(DEFAULT_CONFIG)
    return dict(DEFAULT_CONFIG)


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


class PortfolioGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PortfolioIsMoving")
        self.root.geometry("420x460")
        self.root.resizable(False, False)

        self.config = load_config()
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        pad = {"padx": 12, "pady": 6}

        # Header
        tk.Label(self.root, text="📈 PortfolioIsMoving", font=("Segoe UI", 14, "bold")).pack(anchor="w", **pad)

        # Add ticker row
        add_frame = tk.Frame(self.root)
        add_frame.pack(fill="x", **pad)
        self.ticker_var = tk.StringVar()
        tk.Entry(add_frame, textvariable=self.ticker_var, width=15).pack(side="left")
        tk.Button(add_frame, text="Add", command=self.add_ticker, width=8).pack(side="left", padx=(8, 0))

        # Ticker list
        list_frame = tk.Frame(self.root)
        list_frame.pack(fill="both", expand=True, **pad)
        self.listbox = tk.Listbox(list_frame, height=12)
        scroll = tk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Remove button
        tk.Button(self.root, text="Remove selected", command=self.remove_ticker).pack(anchor="w", **pad)

        # Threshold
        thresh_frame = tk.Frame(self.root)
        thresh_frame.pack(fill="x", **pad)
        tk.Label(thresh_frame, text="Alert when moved ≥").pack(side="left")
        self.threshold_var = tk.DoubleVar(value=self.config.get("threshold_pct", 5.0))
        tk.Spinbox(thresh_frame, from_=1.0, to=100.0, increment=0.5,
                   textvariable=self.threshold_var, width=5).pack(side="left")
        tk.Label(thresh_frame, text="%").pack(side="left")

        # Enable toggle
        self.enabled_var = tk.BooleanVar(value=self.config.get("enabled", False))
        self.enable_check = tk.Checkbutton(
            self.root, text="Enable monitoring", variable=self.enabled_var,
            command=self._toggle_enable, font=("Segoe UI", 11, "bold"))
        self.enable_check.pack(anchor="w", **pad)

        # Status / Save
        self.status_label = tk.Label(self.root, text="", fg="#555")
        self.status_label.pack(anchor="w", **pad)
        tk.Button(self.root, text="Save portfolio", command=self.save).pack(anchor="w", **pad)

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        for t in self.config.get("tickers", []):
            self.listbox.insert(tk.END, t)
        self._update_status()

    def _update_status(self):
        enabled = self.enabled_var.get()
        n = len(self.config.get("tickers", []))
        state = "ON 🟢" if enabled else "OFF ⚪"
        self.status_label.config(text=f"Status: {state}  |  {n} ticker(s) tracked")

    def _toggle_enable(self):
        self.config["enabled"] = self.enabled_var.get()
        self._update_status()

    def add_ticker(self):
        raw = self.ticker_var.get().strip().upper()
        if not raw:
            return
        tickers = self.config.get("tickers", [])
        if raw not in tickers:
            tickers.append(raw)
            self.config["tickers"] = tickers
        self.ticker_var.set("")
        self._refresh_list()

    def remove_ticker(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        tickers = self.config.get("tickers", [])
        if 0 <= idx < len(tickers):
            del tickers[idx]
            self.config["tickers"] = tickers
        self._refresh_list()

    def save(self):
        try:
            threshold = float(self.threshold_var.get())
            if threshold <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Invalid threshold", "Threshold must be a positive number.")
            return
        self.config["threshold_pct"] = threshold
        self.config["enabled"] = self.enabled_var.get()
        save_config(self.config)
        self._update_status()
        messagebox.showinfo("Saved", f"Portfolio saved.\n{len(self.config['tickers'])} ticker(s), "
                                     f"threshold {threshold}%.\nMonitoring: "
                                     f"{'ON' if self.config['enabled'] else 'OFF'}.")


def main():
    root = tk.Tk()
    PortfolioGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
