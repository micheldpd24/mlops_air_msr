import logging
import requests
# from tinydb import TinyDB, Query
import random



# Set up logging to write to a file

logging.basicConfig(
    filename=f"tests_log.txt",  # Log file name
    level=logging.INFO,  # 
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

BASE_URL = "http://app:5000"  # Change to your Flask app's URL

session = requests.Session()

# def clean_users_base():
#     # Initialize TinyDB
#     db_path = "users/users.json"
#     db = TinyDB(db_path)
#     user_table = db.table("users")

#     # Create a query object
#     User = Query()

#     # Remove users where the 'username' is neither 'admin' nor 'test'
#     user_table.remove(~(User.username == 'admin') & ~(User.username == 'test'))

#     print("Users removed successfully.")


# Function to log the response
def log_response(request_type, endpoint, response):
    logging.info(f"{request_type} request to {endpoint}: {response.status_code}")
    return response.status_code

# Function to register a user and log the result
def register_user(username, password):
    print(f"Attempting to register user: {username}")
    response = session.post(f'{BASE_URL}/register', data={
        'username': username,
        'password': password
    })
    log_response("Post", "/register", response)
    return response.status_code


# Function to login and log the result
def login_user(username, password):
    # logging.info(f"Attempting to log in user: {username}")
    print(f"Attempting to log in user: {username}")
    response = session.post(f'{BASE_URL}/', data={
        'username': username,
        'password': password
    })
    log_response("Post login", "/", response)
    return response.status_code


# Function to access the /recommend route
def access_welcome_route():
    print("Attempting to access /recommend route.")
    response = session.get(f'{BASE_URL}/welcome')  # Assuming login session is stored in cookies
    log_response("Get", "/welcome", response)
    return response.status_code


# Function to send a POST request to /recommend route
def post_to_recommend(URL="9", num_recs="10"):
    print(f"Attempting to send POST request to /recommend with input: URL={URL}, number-of-recs={num_recs}")
    # Assuming the form data is being sent as x-www-form-urlencoded
    response = session.post(f"{BASE_URL}/recommend", data={
        "URL": URL,
        "number-of-recs": num_recs
    })  # Include session cookies for authentication
    log_response("Post", "/recommend", response)
    return response.status_code


# Function to logout and log the result
def logout_user():
    print("Attempting to log out user.")
    response = session.get(f'{BASE_URL}/logout')
    log_response("Get", "/logout", response)
    return response.status_code


def access_delete_user_route():
    print("Attempting to access /delete_user route.")
    response = session.get(f'{BASE_URL}/delete_user')  # Assuming login session is stored in cookies
    log_response("Get", "/delete_user", response)
    return response.status_code


def get_to_monitoring():
    print("Attempting to access /monitoring route.")
    response = session.get(f'{BASE_URL}/monitoring')  # Assuming login session is stored in cookies
    log_response("Get", "/monitoring", response)
    return response.status_code


def get_to_update_params():
    print("Attempting to access /update_params.")
    response = session.get(f'{BASE_URL}/update_params')  # Assuming login session is stored in cookies
    log_response("Get", "/update_params", response)
    return response.status_code


def post_delete_user(username):
    # logging.info("Attempting to access /recommend route.")
    print("Attempting to delete_user.")
    response = session.post(f'{BASE_URL}/delete_user', data={"username": username}) 
    log_response("Post", "/delete_user", response)
    return response.status_code


# Function to run all tests and return 1 if any response is not 200
def run_tests():
    URL = str(random.randint(1, 499))
    # reset users database
    # clean_users_base()

    # Check if any response is not 200 and return 0 if found
    all_responses = [
        # Step 1: Register a user
        # register_user("test2", "Test#User12345"),
        
        # Step 2: Log in with the created user
        login_user("test", "test"),

        # Step 3: Access recommend route
        access_welcome_route(),

        # Step 4: Post recommendation request
        
        post_to_recommend(URL=URL, num_recs="10"),

        # Step 5: Log out the user
        logout_user(),

        # Step 6: Log in as Admin
        login_user("admin", "admin"),

        # Step 7: Access monitoring route
        get_to_monitoring(),

        # Step 8: Access update_params route
        get_to_update_params(),
        
        # Step 9: Access delete_user route
        access_delete_user_route(),

        # Step 10: Delete test1 user
        # post_delete_user("test2")
    ]
    

    if any(res != 200 for res in all_responses):
        print("Test failed: At least one response was not 200.")
        return 1
    
    print("All tests passed.")
    return 0

if __name__ == "__main__":
    # Run all tests and return the result
    result = run_tests()
    
    # Read the log file to check results
    with open("tests_log.txt", 'r') as log_file:
        print(log_file.read())  # Print the content of the log file
    exit(result)