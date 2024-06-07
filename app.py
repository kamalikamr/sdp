from flask import Flask, render_template, request, redirect, url_for, session
import csv
import uuid
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'mercy_laundry_management'

class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class SinglyLinkedList:
    def __init__(self):
        self.head = None

    def append(self, data):
        if not self.head:
            self.head = Node(data)
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = Node(data)

    def display(self):
        customers = []
        seen_transaction_ids = set()
        current = self.head
        while current:
            transaction_id = current.data["transaction_id"]
            if transaction_id not in seen_transaction_ids:
                customers.append(current.data)
                seen_transaction_ids.add(transaction_id)
            current = current.next
        return customers

class HashTable:
    def __init__(self):
        self.table = {}

    def insert(self, key, value):
        self.table[key] = value

    def get(self, key):
        return self.table.get(key)

class Queue:
    def __init__(self):
        self.front = None
        self.rear = None
        self.history = []

    def enqueue(self, data):
        new_node = Node(data)
        self.history.append(data)
        if self.rear is None:
            self.front = new_node
            self.rear = new_node
        else:
            self.rear.next = new_node
            self.rear = new_node

    def dequeue(self, transaction_id):
        if self.front is None:
            return "All work completed"

        # If the front node needs to be dequeued
        if self.front.data['transaction_id'] == transaction_id:
            data = self.front.data
            self.front = self.front.next
            if self.front is None:
                self.rear = None
            return data

        # If a middle or rear node needs to be dequeued
        current = self.front
        while current.next and current.next.data['transaction_id'] != transaction_id:
            current = current.next

        if current.next is None:
            return "Transaction ID not found in the queue"

        data = current.next.data
        current.next = current.next.next
        if current.next is None:
            self.rear = current
        return data

    def get_all_data(self):
        data_list = []
        seen_transaction_ids = set()
        current = self.front
        while current:
            transaction_id = current.data["transaction_id"]
            if transaction_id not in seen_transaction_ids:
                data_list.append(current.data)
                seen_transaction_ids.add(transaction_id)
            current = current.next
        return data_list

l1 = Queue()

class CustomerManagement:
    def __init__(self):
        self.customers = SinglyLinkedList()
        self.hash_table = HashTable()
        self.csv_file = "customers.csv"
        self.csv_headers = [
            "username", "name", "contact", "gender", "apartment_block",
            "total_clothes", "service_type", "transaction_id", "deposit_date", "transaction_status"
        ]
        self.load_from_csv()

    def create_customer(self, username, name, contact, gender, apartment_block, total_clothes, service_type, transaction_id, deposit_date, transaction_status):
        customer = {
            "username": username,
            "name": name,
            "contact": contact,
            "gender": gender,
            "apartment_block": apartment_block,
            "total_clothes": total_clothes,
            "service_type": service_type,
            "transaction_id": transaction_id,
            "deposit_date": deposit_date,
            "transaction_status": transaction_status
        }
        self.customers.append(customer)
        self.hash_table.insert(username, customer)
        self.write_to_csv(customer)

    def view_customer(self, username):
        return self.hash_table.get(username)

    def update_customer(self, username, name=None, contact=None, gender=None, apartment_block=None, total_clothes=None, service_type=None, transaction_status=None):
        customer = self.hash_table.get(username)
        if customer:
            if name:
                customer["name"] = name
            if contact:
                customer["contact"] = contact
            if gender:
                customer["gender"] = gender
            if apartment_block:
                customer["apartment_block"] = apartment_block
            if total_clothes:
                customer["total_clothes"] = total_clothes
            if service_type:
                customer["service_type"] = service_type
            if transaction_status:
                customer["transaction_status"] = transaction_status
            self.write_to_csv_all()
        else:
            print("Customer not found.")

    def write_to_csv(self, customer):
        with open(self.csv_file, "a", newline="") as file:
            writer = csv.writer(file)
            if file.tell() == 0:
                writer.writerow(self.csv_headers)
            writer.writerow([
                customer["username"],
                customer["name"],
                customer["contact"],
                customer["gender"],
                customer["apartment_block"],
                customer["total_clothes"],
                customer["service_type"],
                customer["transaction_id"],
                customer["deposit_date"],
                customer["transaction_status"]
            ])

    def write_to_csv_all(self):
        with open(self.csv_file, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(self.csv_headers)
            current = self.customers.head
            while current:
                customer = current.data
                writer.writerow([
                    customer["username"],
                    customer["name"],
                    customer["contact"],
                    customer["gender"],
                    customer["apartment_block"],
                    customer["total_clothes"],
                    customer["service_type"],
                    customer["transaction_id"],
                    customer["deposit_date"],
                    customer["transaction_status"]
                ])
                current = current.next

    def load_from_csv(self):
        try:
            with open(self.csv_file, newline="") as file:
                reader = csv.reader(file)
                headers = next(reader, None)  # Get the headers
                if headers is not None:
                    for row in reader:
                        if len(row) >= len(self.csv_headers):
                            customer = {
                                "username": row[0],
                                "name": row[1],
                                "contact": row[2],
                                "gender": row[3],
                                "apartment_block": row[4],
                                "total_clothes": row[5],
                                "service_type": row[6],
                                "transaction_id": row[7],
                                "deposit_date": row[8],
                                "transaction_status": row[9]
                            }
                            self.customers.append(customer)
                            self.hash_table.insert(row[0], customer)
                            if row[9] == "Pending":
                                order = {'username': row[0], 'transaction_id': row[7], 'transaction_status': row[9]}
                                l1.enqueue(order)
                        else:
                            print("Row has insufficient columns:", row)
        except FileNotFoundError:
            # File does not exist yet
            pass

customer_manager = CustomerManagement()

# In-memory storage for users
users = {
    'admin': {'password': 'adminpass', 'role': 'admin'}
}

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        user = users.get(username)
        if user and user['password'] == password and user['role'] == role:
            session['username'] = username
            session['role'] = role
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid credentials'
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        contact_number = request.form['contact_number']
        email = request.form['email']
        gender = request.form['gender']
        apartment_block = request.form['apartment_block']
        
        if username not in users:
            users[username] = {
                'password': password,
                'role': 'customer',
                'name': name,
                'contact_number': contact_number,
                'email': email,
                'gender': gender,
                'apartment_block': apartment_block
            }
            return redirect(url_for('login'))
        else:
            return 'Username already exists'
    return render_template('signup.html')


@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        if session['role'] == 'customer':
            return redirect(url_for('cloth_deposit'))
        else:
            return redirect(url_for('admin_dashboard'))
    return redirect(url_for('login'))

@app.route('/cloth_deposit', methods=['GET', 'POST'])
def cloth_deposit():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        service_type = request.form['service_type']
        total_clothes = int(request.form['total_clothes']) # Convert to integer

        if service_type == 'washing':
            total_cost = total_clothes * 10
        elif service_type == 'washing_ironing':
            total_cost = total_clothes * 15
        else:
            total_cost = 0

        transaction_id = str(uuid.uuid4())[:8]
        deposit_date = datetime.now().strftime("%d-%m-%Y")
        delivery_date = (datetime.now() + timedelta(days=4)).strftime("%d-%m-%Y")
        transaction_status = "Pending"

        customer_manager.create_customer(
            session['username'], users[session['username']]['name'],
            users[session['username']]['contact_number'], users[session['username']]['gender'],
            users[session['username']]['apartment_block'], total_clothes, service_type,
            transaction_id, deposit_date, transaction_status
        )

        order = {'username': session['username'], 'transaction_id': transaction_id, 'transaction_status': transaction_status}
        l1.enqueue(order)

        return render_template('transaction_slip.html', transaction_id=transaction_id, service_type=service_type,
                               delivery_date=delivery_date,total_cost=total_cost,
                               transaction_status=transaction_status)

    user = users[session['username']]
    return render_template('cloth_deposit.html', user=user)



@app.route('/deposit_result')
def deposit_result():
    if 'username' not in session:
        return redirect(url_for('login'))

    total_cost = request.args.get('total_cost', type=int)
    return render_template('deposit_result.html', total_cost=total_cost)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'adminpass':
            session['username'] = username
            session['role'] = 'admin'
            return redirect(url_for('admin_dashboard'))
        else:
            return 'Invalid credentials'
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'username' in session and session['role'] == 'admin':
        customer_list = customer_manager.customers.display()
        
        work_in_progress = [work for work in l1.get_all_data() if work['transaction_status'] != 'Paid']
        
        history = l1.history

        seen_transaction_ids = set()
        filtered_history = []
        for entry in history:
            if entry["transaction_id"] not in seen_transaction_ids:
                filtered_history.append(entry)
                seen_transaction_ids.add(entry["transaction_id"])

        return render_template('admin_dashboard.html', customers=customer_list, work_in_progress=work_in_progress, history=filtered_history)
    return redirect(url_for('admin_login'))

@app.route('/create_customer', methods=['GET', 'POST'])
def create_customer():
    if 'username' in session and session['role'] == 'admin':
        if request.method == 'POST':
            username = request.form['username']
            name = request.form['name']
            contact = request.form['contact']
            gender = request.form['gender']
            apartment_block = request.form['apartment_block']
            total_clothes = request.form['total_clothes']
            service_type = request.form['service_type']
            transaction_id = str(uuid.uuid4())[:8]
            deposit_date = datetime.now().strftime("%d-%m-%Y")
            transaction_status = "Pending"

            customer_manager.create_customer(username, name, contact, gender, apartment_block, total_clothes, service_type, transaction_id, deposit_date, transaction_status)

            order = {'username': username, 'transaction_id': transaction_id, 'transaction_status': transaction_status}
            l1.enqueue(order)

            return redirect(url_for('admin_dashboard'))
        return render_template('create_customer.html')
    return redirect(url_for('admin_login'))

@app.route('/view_customer/<username>')
def view_customer(username):
    if 'username' in session and session['role'] == 'admin':
        customer = customer_manager.view_customer(username)
        if customer:
            return render_template('view_customer.html', customer=customer)
        else:
            return 'Customer not found'
    return redirect(url_for('admin_login'))

@app.route('/update_customer/<username>', methods=['GET', 'POST'])
def update_customer(username):
    if 'username' in session and session['role'] == 'admin':
        if request.method == 'POST':
            name = request.form['name']
            contact = request.form['contact']
            gender = request.form['gender']
            apartment_block = request.form['apartment_block']
            total_clothes = request.form['total_clothes']
            service_type = request.form['service_type']
            transaction_status = request.form['transaction_status']

            customer_manager.update_customer(username, name, contact, gender, apartment_block, total_clothes, service_type, transaction_status)
            
            if transaction_status == "Paid":
                customer = customer_manager.view_customer(username)
                if customer:
                    transaction_id = customer['transaction_id']
                    l1.dequeue(transaction_id)

            return redirect(url_for('admin_dashboard'))
        customer = customer_manager.view_customer(username)

        if customer:
            return render_template('update_customer.html', customer=customer)
        else:
            return 'Customer not found'
    return redirect(url_for('admin_login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)