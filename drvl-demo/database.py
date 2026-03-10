class Database:

    def __init__(self):
        self.tables = {
            "users": ["alice", "bob", "charlie"],
            "orders": [101, 102, 103]
        }

    def execute(self, action, table):

        if action == "DELETE":
            self.tables[table] = []
            return f"All records deleted from {table}"

        return "Unknown action"
