def test_get_by_id_with_existing_role(role_repository, existing_role): #для существующей роли
    role = role_repository.get_by_id(existing_role.id)
    assert role.id == existing_role.id
    assert role.name == existing_role.name

def test_get_by_id_with_nonexisting_role(role_repository, nonexisting_role_id): #для несуществующей роли
    role = role_repository.get_by_id(nonexisting_role_id)
    assert role is None

def test_all_with_nonempty_db_role(role_repository, example_roles): #возвращает все роли
    roles = role_repository.all()
    assert len(roles) == len(example_roles)
    for loaded_role, example_role in zip(roles, example_roles):
        assert loaded_role.id == example_role.id
        assert loaded_role.name == example_role.name

def test_get_by_id_with_existing_user(user_repository, existing_user): #для существующего пользователя
    user = user_repository.get_by_id(existing_user.id)
    assert user.id == existing_user.id
    assert user.username == existing_user.username
    assert user.first_name == existing_user.first_name

def test_get_by_id_with_nonexisting_user(user_repository, nonexisting_user_id): #для несуществующего пользователя
    user = user_repository.get_by_id(nonexisting_user_id)
    assert user is None

def test_all_with_nonempty_db_user(user_repository, example_users): #возвращает всех пользователей
    users = user_repository.all()
    assert len(users) == len(example_users)
    for loaded_user, example_user in zip(users, example_users):
        assert loaded_user.id == example_user.id
        assert loaded_user.username == example_user.username

def test_get_by_username_and_password(user_repository, existing_user):
    user = user_repository.get_by_username_and_password(existing_user.username, 'password123')
    assert user is not None
    assert user.id == existing_user.id

def test_get_by_username_and_password_with_wrong_password(user_repository, existing_user):
    user = user_repository.get_by_username_and_password(existing_user.username, 'wrongpassword')
    assert user is None

def test_create_user(user_repository, db_connector):
    connection = db_connector.connect()
    with connection.cursor() as cursor:
        cursor.execute("INSERT INTO roles(id, name) VALUES (1, 'test_role');")
        connection.commit()
    username = "newuser"
    password = "newpass"
    first_name = "New"
    middle_name = "N"
    last_name = "User"
    role_id = 1  
    
    user_repository.create(username, password, first_name, middle_name, last_name, role_id)
    
    with user_repository.db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute("SELECT * FROM users WHERE username = %s;", (username,))
        user = cursor.fetchone()
        assert user is not None
        assert user.username == username
        assert user.first_name == first_name
        assert user.role_id == role_id
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE username = %s;", (username,))
        cursor.execute("DELETE FROM roles WHERE id = %s;", (role_id,))
        connection.commit()

def test_update_user(user_repository, existing_user):
    new_first_name = "Updated"
    new_last_name = "Name"
    
    user_repository.update(existing_user.id, new_first_name, existing_user.middle_name, new_last_name, existing_user.role_id)
    
    updated_user = user_repository.get_by_id(existing_user.id)
    assert updated_user.first_name == new_first_name
    assert updated_user.last_name == new_last_name

def test_delete_user(user_repository, existing_user):
    user_repository.delete(existing_user.id)
    deleted_user = user_repository.get_by_id(existing_user.id)
    assert deleted_user is None

def test_check_password(user_repository, existing_user):
    assert user_repository.check_password(existing_user.id, 'password123') is True
    assert user_repository.check_password(existing_user.id, 'wrongpassword') is False

def test_verify_password(user_repository, existing_user):
    new_password = "newsecurepassword"
    user_repository.verify_password(existing_user.id, new_password)
    assert user_repository.check_password(existing_user.id, new_password) is True
    assert user_repository.check_password(existing_user.id, 'password123') is False