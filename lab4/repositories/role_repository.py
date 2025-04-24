class RoleRepository:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def get_by_id(self, role_id):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("SELECT * FROM roles WHERE id = %s;", (role_id,))
            role = cursor.fetchone()
        return role

    def get_all(self):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("SELECT * FROM roles;")
            roles = cursor.fetchall()
        return roles
