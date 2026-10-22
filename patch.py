with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace('ft.colors', 'ft.Colors')
code = code.replace('page.go(', 'page.push_route(')
code = code.replace('ft.app(target=main)', 'ft.run(target=main)')

# Change the routing logic
target_logic = """        # ---------- 1. HOME VIEW ----------
        if page.route == "/":"""

new_logic = """        # ---------- 1. HOME VIEW ----------
        if True: # Always show home view underneath to prevent black screen"""

code = code.replace(target_logic, new_logic)

code = code.replace('elif page.route == "/study":', 'if page.route == "/study":')
code = code.replace('elif page.route == "/dict_select":', 'if page.route == "/dict_select":')
code = code.replace('elif page.route == "/settings":', 'if page.route == "/settings":')

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Patch applied.")
