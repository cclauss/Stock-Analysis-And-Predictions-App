import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
import yfinance as yf
import matplotlib.pyplot as plt
from prophet import Prophet
import websockets
import asyncio
import json

class StockApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Stock Market Analysis and Prediction App")

        # dimensions
        window_width = 350
        window_height = 250
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

        self.resizable(False, False)

        self.portfolio = []  # portfolio symbols storing

        self.symbol_label = tk.Label(self, text="Enter A Stock Symbol:")
        self.symbol_label.pack()

        self.symbol_entry = tk.Entry(self)
        self.symbol_entry.pack()

        self.add_to_portfolio_button = tk.Button(self, text="Add to Portfolio", command=self.add_to_portfolio)
        self.add_to_portfolio_button.pack()

        self.view_portfolio_button = tk.Button(self, text="View Portfolio", command=self.view_portfolio)
        self.view_portfolio_button.pack()

        self.analyze_portfolio_button = tk.Button(self, text="Analyze Portfolio", command=self.analyze_portfolio)
        self.analyze_portfolio_button.pack()

        self.date_range_frame = tk.Frame(self)
        self.date_range_frame.pack()

        self.start_date_label = tk.Label(self.date_range_frame, text="Start Date:")
        self.start_date_label.pack(side=tk.LEFT)

        self.start_date_entry = DateEntry(self.date_range_frame)
        self.start_date_entry.pack(side=tk.LEFT)

        self.end_date_label = tk.Label(self.date_range_frame, text="End Date:")
        self.end_date_label.pack(side=tk.LEFT)

        self.end_date_entry = DateEntry(self.date_range_frame)
        self.end_date_entry.pack(side=tk.LEFT)

        self.analyze_button = tk.Button(self, text="Analyze", command=self.analyze_stock)
        self.analyze_button.pack()

        self.predict_button = tk.Button(self, text="Predict", command=self.predict_stock)
        self.predict_button.pack()

        self.real_time_label = tk.Label(self, text="Real-Time Price: N/A")
        self.real_time_label.pack()

    def analyze_stock(self):
        stock_symbol = self.symbol_entry.get().strip().upper()
        start_date = self.start_date_entry.get_date().strftime('%Y-%m-%d')
        end_date = self.end_date_entry.get_date().strftime('%Y-%m-%d')

        if not stock_symbol:
            messagebox.showerror("Error", "Please enter a stock symbol.")
            return

        try:
            self.stock_data = self.fetch_stock_data(stock_symbol, start_date, end_date)
            self.analyze_and_plot(stock_symbol, self.stock_data)
        except Exception as e:
            messagebox.showerror("Error", f"Error fetching data: {str(e)}")
            return

    def fetch_stock_data(self, symbol, start_date, end_date):
        return yf.download(symbol, start=start_date, end=end_date)

    def analyze_and_plot(self, symbol, data):
        df = data.reset_index()[['Date', 'Close']]
        df = df.rename(columns={'Date': 'ds', 'Close': 'y'})

        plt.figure(figsize=(12, 6))
        plt.plot(df['ds'], df['y'], label='Historical Prices')
        plt.title(f"{symbol} Stock Price Analysis")
        plt.xlabel("Date")
        plt.ylabel("Price (USD)")
        plt.legend()
        plt.grid(True)
        plt.show()

    def plot_stock_data(self, symbol, data):
        df = data.reset_index()[['Date', 'Close']]
        df = df.rename(columns={'Date': 'ds', 'Close': 'y'})

        plt.plot(df['ds'], df['y'], label=symbol.replace(" ", "_"))  # Use a suitable label format

    def analyze_portfolio(self):
        if not self.portfolio:
            messagebox.showinfo("Info", "Portfolio is empty.")
            return

        plt.figure(figsize=(12, 6))

        start_date = self.start_date_entry.get_date().strftime('%Y-%m-%d')
        end_date = self.end_date_entry.get_date().strftime('%Y-%m-%d')

        for symbol in self.portfolio:
            try:
                stock_data = self.fetch_stock_data(symbol, start_date, end_date)
                self.plot_stock_data(symbol, stock_data)
            except Exception as e:
                messagebox.showerror("Error", f"Error fetching data for {symbol}: {str(e)}")

        plt.title("Portfolio Stock Price Analysis")
        plt.xlabel("Date")
        plt.ylabel("Price (USD)")
        plt.legend()
        plt.grid(True)
        plt.show()

    def predict_stock(self):
        if not hasattr(self, "stock_data"):
            messagebox.showerror("Error", "Please fetch data first.")
            return

        symbol = self.symbol_entry.get().strip().upper()
        self.predict_and_plot(symbol, self.stock_data)

    def predict_and_plot(self, symbol, data):
        df = data.reset_index()[['Date', 'Close']]
        df = df.rename(columns={'Date': 'ds', 'Close': 'y'})

        model = Prophet(daily_seasonality=True)
        model.fit(df)

        future = model.make_future_dataframe(periods=1825)
        forecast = model.predict(future)

        plt.figure(figsize=(12, 6))
        plt.plot(df['ds'], df['y'], label='Actual Prices')
        plt.plot(forecast['ds'], forecast['yhat'], label='Predicted Prices', linestyle='dashed')
        plt.title(f"{symbol} Stock Price Prediction")
        plt.xlabel("Date")
        plt.ylabel("Price (USD)")
        plt.legend()
        plt.grid(True)
        plt.show()

    def add_to_portfolio(self):
        stock_symbol = self.symbol_entry.get().strip().upper()
        if stock_symbol not in self.portfolio:
            self.portfolio.append(stock_symbol)
            messagebox.showinfo("Info", f"{stock_symbol} added to portfolio.")
        else:
            messagebox.showinfo("Info", f"{stock_symbol} is already in the portfolio.")

    def view_portfolio(self):
        if self.portfolio:
            portfolio_info = "\n".join(self.portfolio)
        else:
            portfolio_info = "Portfolio is empty."
        messagebox.showinfo("Portfolio", portfolio_info)

    
    async def fetch_real_time_data(self, symbol):
        async with websockets.connect(f"wss://realtime-stock-api.com/ws/stocks/{symbol}") as websocket:
            while True:
                data = await websocket.recv()
                stock_data = json.loads(data)
                price = stock_data['price']
                self.update_real_time_price(price)


    def start_real_time_data(self, symbol):
        loop = asyncio.get_event_loop()
        loop.create_task(self.fetch_real_time_data(symbol))

    def update_real_time_price(self, price):
        self.real_time_label.config(text=f"Real-Time Price: {price} USD")


if __name__ == "__main__":
    app = StockApp()
    app.mainloop()
