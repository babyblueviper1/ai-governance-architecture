from agent import Agent
from database import Database
from drvl import DRVL

environment = "production"

agent = Agent()
db = Database()
drvl = DRVL()

print("\nAI Agent starting database cleanup...\n")

action, table = agent.generate_action()

print(f"AI generated action: {action} on {table}")

allowed, message = drvl.verify(action, table, environment)

print("\nDRVL verification layer engaged")

if not allowed:

    print("\n❌ ACTION BLOCKED")
    print("Reason:", message)

else:

    result = db.execute(action, table)

    print("\n✅ ACTION EXECUTED")
    print(result)
