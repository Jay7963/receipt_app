# main.py
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
from datetime import datetime
from gravitylogic import load_items, generate_receipt_pdf, generate_monthly_report

class ReceiptAppUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=10, spacing=10, **kwargs)

        self.items = load_items()
        self.receipt_items = []

        # HEADER
        self.add_widget(Label(text="Receipt Printing System", font_size=24, size_hint_y=None, height=40))

        # MAIN CONTENT
        content = BoxLayout(orientation='horizontal', spacing=10)

        # LEFT FORM
        form = GridLayout(cols=2, spacing=5, size_hint_x=0.6)

        form.add_widget(Label(text="Select Company:"))
        self.company_spinner = Spinner(
            text="Select Company",
            values=["St. Hannah's Girls School", "MAA Restaurant", "The Base Restaurant"]
        )
        form.add_widget(self.company_spinner)

        # Search field
        form.add_widget(Label(text="Search Item:"))
        self.search_input = TextInput(hint_text="Type to search...")
        self.search_input.bind(text=self.filter_items)
        form.add_widget(self.search_input)

        # Item dropdown
        form.add_widget(Label(text="Select Item:"))
        self.item_spinner = Spinner(text="Select Item", values=list(self.items.keys()))
        form.add_widget(self.item_spinner)

        form.add_widget(Label(text="Quantity:"))
        self.qty_input = TextInput(hint_text="Enter Quantity", input_filter="float")
        form.add_widget(self.qty_input)

        self.add_btn = Button(text="Add Item")
        self.add_btn.bind(on_press=self.add_item)
        form.add_widget(self.add_btn)
        form.add_widget(Label())  # placeholder

        content.add_widget(form)

        # RIGHT RECEIPT LIST
        right = BoxLayout(orientation="vertical", size_hint_x=0.4)
        right.add_widget(Label(text="Receipt Items:"))

        self.scroll = ScrollView()
        self.item_box = BoxLayout(orientation='vertical', size_hint_y=None)
        self.item_box.bind(minimum_height=self.item_box.setter('height'))
        self.scroll.add_widget(self.item_box)
        right.add_widget(self.scroll)

        self.delete_btn = Button(text="Clear Items")
        self.delete_btn.bind(on_press=self.clear_items)
        right.add_widget(self.delete_btn)

        content.add_widget(right)
        self.add_widget(content)

        # BOTTOM ACTIONS
        bottom = BoxLayout(size_hint_y=None, height=50, spacing=10)
        self.clear_btn = Button(text="Clear Form", size_hint_x=0.25)
        self.clear_btn.bind(on_press=self.clear_form)

        self.generate_btn = Button(text="Generate PDF Receipt", size_hint_x=0.4)
        self.generate_btn.bind(on_press=self.generate_pdf)

        self.monthly_btn = Button(text="Calculate Monthly Total", size_hint_x=0.35)
        self.monthly_btn.bind(on_press=self.open_monthly_report_popup)

        bottom.add_widget(self.clear_btn)
        bottom.add_widget(self.generate_btn)
        bottom.add_widget(self.monthly_btn)

        self.add_widget(bottom)

    def filter_items(self, instance, text):
        query = text.strip().lower()
        if not query:
            filtered = list(self.items.keys())
        else:
            filtered = [item for item in self.items if query in item.lower()]
        self.item_spinner.values = filtered
        self.item_spinner.text = filtered[0] if filtered else "Select Item"

    def add_item(self, instance):
        item = self.item_spinner.text
        try:
            quantity = float(self.qty_input.text)
            price = self.items.get(item)
            if not price or quantity <= 0:
                raise ValueError
            total = price * quantity
            self.receipt_items.append((item, quantity, price, total))

            label_text = f"{quantity} x {item} @ {price:.2f} = KSH {total:.2f}"
            self.item_box.add_widget(Label(text=label_text, size_hint_y=None, height=30))

            self.qty_input.text = ""
        except:
            self.show_popup("Error", "Invalid quantity or item.")

    def clear_items(self, instance):
        self.receipt_items.clear()
        self.item_box.clear_widgets()

    def clear_form(self, instance):
        self.qty_input.text = ""
        self.search_input.text = ""
        self.item_spinner.text = "Select Item"
        self.company_spinner.text = "Select Company"
        self.clear_items(None)

    def generate_pdf(self, instance):
        company = self.company_spinner.text
        items = self.receipt_items

        if company == "Select Company":
            self.show_popup("Error", "Please select a company.")
            return
        if not items:
            self.show_popup("Error", "No items added to the receipt.")
            return

        filename = generate_receipt_pdf(items, company)
        if filename:
            self.show_popup("Success", f"PDF saved as: {filename}")
            self.clear_items(None)

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message),
                      size_hint=(0.8, 0.3))
        popup.open()

    def open_monthly_report_popup(self, instance):
        popup = ModalView(size_hint=(0.9, 0.7))
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)

        current_year = datetime.now().year
        years = [str(y) for y in range(2020, current_year + 1)]
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        companies = ["St. Hannah's Girls School", "MAA Restaurant", "The Base Restaurant"]

        layout.add_widget(Label(text="Select Year:"))
        year_spinner = Spinner(text=str(current_year), values=years)
        layout.add_widget(year_spinner)

        layout.add_widget(Label(text="Select Month:"))
        month_spinner = Spinner(text=months[0], values=months)
        layout.add_widget(month_spinner)

        layout.add_widget(Label(text="Select Company:"))
        company_spinner = Spinner(text=companies[0], values=companies)
        layout.add_widget(company_spinner)

        def generate_report(_):
            year = int(year_spinner.text)
            month = months.index(month_spinner.text) + 1
            company = company_spinner.text
            filename = generate_monthly_report(year, month, company)
            popup.dismiss()
            if filename:
                self.show_popup("Success", f"Monthly report saved as: {filename}")
            else:
                self.show_popup("Info", "No data found for that selection.")

        generate_btn = Button(text="Generate Monthly Report", size_hint_y=None, height=50)
        generate_btn.bind(on_press=generate_report)

        layout.add_widget(generate_btn)
        popup.add_widget(layout)
        popup.open()

class ReceiptApp(App):
    def build(self):
        return ReceiptAppUI()

if __name__ == '__main__':
    ReceiptApp().run()
