# Import necessary libraries
from flask import Flask, request, jsonify
import mysql.connector
import os
from datetime import date
from dotenv import load_dotenv
load_dotenv()
# Create a Flask app
app = Flask(__name__)

# MySQL Configuration
mysql_config = {
    'host': os.environ.get('MYSQL_HOST'),
    'port': int(os.environ.get('MYSQL_PORT')),
    'user': os.environ.get('MYSQL_USER'),
    'password': os.environ.get('MYSQL_PASSWORD'),
}

# Route to authenticate a dealer
@app.route('/dealer_login', methods=['POST'])
def dealer_login():
    try:
        data = request.get_json()
        email = data['email']
        password = data['password']

        # Establish a connection to the dealer database
        connection = mysql.connector.connect(**mysql_config, database='dealer_db')
        cursor = connection.cursor()

        # Check if the dealer credentials are valid
        cursor.execute("SELECT * FROM dealers WHERE email = %s AND password = %s", (email, password))
        dealer = cursor.fetchone()

        connection.close()

        if dealer:
            return jsonify({'message': 'Dealer login successful'}), 200
        else:
            return jsonify({'error': 'Invalid dealer credentials'}), 401

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to create a dealer account
@app.route('/dealer_signup', methods=['POST'])
def dealer_signup():
    try:
        data = request.get_json()
        username = data['username']
        password = data['password']
        email = data['email']
        phone_number = data.get('phone_number', None)

        # Establish a connection to the dealer database
        connection = mysql.connector.connect(**mysql_config, database='dealer_db')
        cursor = connection.cursor()

        # Check if the dealer username already exists
        cursor.execute("SELECT * FROM dealers WHERE username = %s", (username,))
        existing_dealer = cursor.fetchone()

        if existing_dealer: 
            connection.close()
            return jsonify({'error': 'Username already exists'}), 400
        else:
            # Insert the new dealer into the dealers table
            cursor.execute(
                "INSERT INTO dealers (username, password, email, phone_number) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (username, password, email, phone_number)
            )
            connection.commit()
            connection.close()
            return jsonify({'message': 'Dealer signup successful'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/scheduled_pickup_orders', methods=['GET'])
def get_scheduled_pickup_orders():
    try:
        # Establish a connection to the junkee_db database
        connection = mysql.connector.connect(**mysql_config, database='junkee_db')
        cursor = connection.cursor(dictionary=True)

        # Fetch all orders from the scheduled_pickup table
        cursor.execute("SELECT * FROM schedule_pickup")
        scheduled_pickup_orders = cursor.fetchall()
        print(scheduled_pickup_orders)
        # Close cursor and connection
        cursor.close()
        connection.close()

        # Convert date and time fields to string representations
        for order in scheduled_pickup_orders:
            order['date'] = str(order['date'])
            order['time'] = str(order['time'])

        return jsonify({'scheduled_pickup_orders': scheduled_pickup_orders}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500


    except Exception as e:
        return jsonify({'error': str(e)}), 500

    
@app.route('/accept_order', methods=['POST'])
def accept_order():
    try:
        data = request.get_json()
        order_id = data['order_id']
        user_id = data['user_id']
        scheduled_date = data['scheduled_date']
        time_slot = data['time_slot']
        item_counts = data['item_counts']
        otp = data['otp']
        dealer_id = data['dealer_id']  # Ensure dealer_id is included in the JSON data

        # Establish a connection to the MySQL server for accepting an order
        accept_connection = mysql.connector.connect(**mysql_config, database='dealer_db')
        accept_cursor = accept_connection.cursor()
        
        # Insert the data into the "accepted_orders" table
        accept_cursor.execute("INSERT INTO accepted_orders (order_id, user_id, scheduled_date, time_slot, item_counts, otp, dealer_id)" 
                            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (order_id, user_id, scheduled_date, time_slot, item_counts, otp, dealer_id))
        
        accept_connection.commit()
        accept_connection.close()

        # Establish a connection to the MySQL server for deleting from the scheduled_pickup table
        delete_connection = mysql.connector.connect(**mysql_config, database='junkee_db')
        delete_cursor = delete_connection.cursor()

        # Delete the order from the scheduled_pickup table
        delete_cursor.execute("DELETE FROM schedule_pickup WHERE pickup_id = %s", (order_id,))
        
        delete_connection.commit()
        delete_connection.close()

        return jsonify({'message': 'Order accepted successfully'}), 200

    except mysql.connector.Error as error:
        print("Failed to execute MySQL command: {}".format(error))
        return jsonify({'error': 'Database error'}), 500

    except Exception as e:
        print("Error occurred: {}".format(str(e)))
        return jsonify({'error': 'Internal server error'}), 500

# Endpoint to get all orders for a specific dealer
@app.route('/dealer_orders/<int:dealer_id>', methods=['GET'])
def get_dealer_orders(dealer_id):
    try:
        # Establish a connection to the MySQL server
        connection = mysql.connector.connect(**mysql_config, database='dealer_db')
        cursor = connection.cursor(dictionary=True)

        # Fetch all orders for the specified dealer
        cursor.execute("SELECT * FROM accepted_orders WHERE dealer_id = %s", (dealer_id,))
        dealer_orders = cursor.fetchall()
        print(dealer_orders)
        connection.close()

        # Convert schedule_date to string format
        for order in dealer_orders:
            order['scheduled_date'] = order['scheduled_date'].strftime("%Y-%m-%d")
            order['time_slot'] = str(order['time_slot'])
        print(dealer_orders)
        return jsonify({'dealer_orders': dealer_orders}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Run the Flask app
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)
