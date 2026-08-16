#requires Admin login "1234"

from pathlib import Path
import json

# TODO: Move the admin credential out of source code when deployment configuration exists.
AdminPassword : str = "1234"
ALLOWED_ROLES = {"gm", "player"}


def _users_file_path() -> Path:
    return Path(__file__).parent / "data" / "Users.json"


def _load_users() -> dict:
    with _users_file_path().open("r", encoding="utf-8") as file:
        return json.load(file)


def _save_users(users_data: dict) -> None:
    with _users_file_path().open("w", encoding="utf-8") as file:
        json.dump(users_data, file, indent=4, ensure_ascii=False)
        file.write("\n")


def _require_non_empty_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")

def createUser(adminpass: str, username: str, password_Hash: str, role: str) -> str:
    # Create a new user with the given username and password
    # Save the user data to Users.json
    # Create a folder for the user in the Users directory
    # expot the user id
    
    if adminpass != AdminPassword:
        raise ValueError("Invalid admin password")

    _require_non_empty_text(username, "username")
    _require_non_empty_text(password_Hash, "password_Hash")
    if role not in ALLOWED_ROLES:
        raise ValueError(f"Invalid role {role!r}; expected one of {sorted(ALLOWED_ROLES)}")

    users_data = _load_users()
    next_id = users_data.get("next_id")
    if isinstance(next_id, bool) or not isinstance(next_id, int) or next_id < 1:
        raise ValueError("Users.json must contain a positive integer next_id")

    userId = f"User_{username}_{next_id}"
    while userId in users_data:
        next_id += 1
        userId = f"User_{next_id}"

    # Add the new user to the users_data dictionary
    users_data[userId] = {
        "username": username,
        "password_hash": password_Hash,
        "role": role
    }
    users_data["next_id"] = next_id + 1

    _save_users(users_data)

    # Create a folder for the new user, named without the 'User_' prefix
    user_folder_path = Path(__file__).parent / "data" / "User" / userId.removeprefix("User_")
    user_folder_path.mkdir(parents=True, exist_ok=True)

    return userId

def hasUser(userId: str) -> bool:
    # Check if the userId exists in Users.json.
    # Return True if it exists, otherwise return False.
    
    return userId in _load_users()

def listUsers(adminpass: str) -> list:
    if adminpass != AdminPassword:
        raise ValueError("Invalid admin password")  
    return [user_id for user_id in _load_users() if user_id.startswith("User_")]

def getUserRole(userId: str) -> str:
    # Get the role of the user with the given userId
    # Return the role as a string, or None if the user does not exist.
    
    users_data = _load_users()

    if userId in users_data:
        return users_data[userId]['role']
    return None

def loginTestUser(userId: str, username: str, password_Hash: str) -> bool:
    # Check if the userId exists in Users.json.
    # if it does, check if the username and password_Hash match the stored values.
    # Return True if the login is successful, otherwise return False.
    
    users_data = _load_users()

    if userId in users_data:
        user_data = users_data[userId]
        if user_data['username'] == username and user_data['password_hash'] == password_Hash:
            return True
    return False

def deleteUser(adminpass: str, userId: str):
    # Delete the user with the given userId
    # Remove the user data from Users.json
    # Delete the folder for the user in the Users directory
    
    if adminpass != AdminPassword:
        raise ValueError("Invalid admin password")

    users_data = _load_users()

    if userId in users_data:
        # Remove the user from the users_data dictionary
        del users_data[userId]

        _save_users(users_data)

        # Delete the folder for the user
        user_folder_path = Path(__file__).parent / "data" / "User" / userId.removeprefix("User_")
        if user_folder_path.exists() and user_folder_path.is_dir():
            for item in user_folder_path.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    # Recursively delete subdirectories
                    import shutil
                    shutil.rmtree(item)
            user_folder_path.rmdir()

def tryFindUserID(username: str, password_Hash: str) -> str | None:
    users_data = _load_users()

    for key, value in users_data.items():
        if isinstance(value, dict) and value.get("username") == username and value.get("password_hash") == password_Hash:
            return key
    return None

def main():
    #schreibe einen test user in Users.json und lege einen ordner in Users an.
    #hohle den status des users und gebe ihn aus.
    #lösche den user und den ordner wieder.

    id = createUser(AdminPassword, "testuser", "testpasswordhash", "player")

    if not hasUser(id):
        print(f"User {id} does not exist.")

    if not loginTestUser(id, "testuser", "testpasswordhash"):
        print(f"User {id} failed to log in.")

    if loginTestUser(id, "testuser", "wrongpasswordhash"):
        print(f"User {id} logged in successfully with wrong password (this should not happen).")

    try:
        createUser("wrong-admin-password", "testuser2", "testpasswordhash", "testrole")
        print("User was created with a wrong admin password (this should not happen).")
    except ValueError:
        pass

    try:
        deleteUser("wrong-admin-password", id)
        print(f"User {id} was deleted with a wrong admin password (this should not happen).")
    except ValueError:
        pass

    deleteUser(AdminPassword, id)

    if  hasUser(id):
        print(f"User {id} still exists after deletion (this should not happen).")

if __name__ == "__main__":
    main()