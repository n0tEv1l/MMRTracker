import dearpygui.dearpygui as dpg
import json
import os


# Determine the path to AppData storage
appdata_folder = os.path.join(os.getenv("APPDATA"), "MMRTracker")

# Make sure the folder exists
os.makedirs(appdata_folder, exist_ok=True)

# Path to the file to save data
data_file = os.path.join(appdata_folder, "accounts.json")

# Function to load data from a file
def load_accounts():
    if os.path.exists(data_file):
        with open(data_file, "r") as file:
            return json.load(file)
    return {}

# Function to save data to file
def save_accounts(accounts):
    with open(data_file, "w") as file:
        json.dump(accounts, file, indent=4)

# Function to save data to file# Function to save new account
def save_account(sender, app_data, user_data):
    accounts = load_accounts()
    steam_id = dpg.get_value("steam_id_entry")
    name = dpg.get_value("name_entry")
    current_mmr = int(dpg.get_value("current_mmr_entry"))

    if steam_id in accounts:
        dpg.set_value("status_text", f"Account with ID {steam_id} already exists.")
        return

    accounts[steam_id] = {
        "name": name,
        "current_mmr": current_mmr,
        "mmr_changes": [current_mmr] 
    }
    save_accounts(accounts)
    dpg.set_value("status_text", "Account saved successfully.")
    refresh_account_list()


# Function to update the list of accounts with serial numbers
def refresh_account_list():
    accounts = load_accounts()
    dpg.delete_item("accounts_list", children_only=True)
    for idx, (steam_id, data) in enumerate(accounts.items(), start=1):
        with dpg.group(horizontal=True, parent="accounts_list"):
            dpg.add_button(
                label=f"{idx}. {data['name']} (ID: {steam_id})", 
                callback=load_account,
                user_data=steam_id
            )
            dpg.add_button(label="X", callback=confirm_delete_account, user_data=steam_id)

# Function to confirm account deletion
def confirm_delete_account(sender, app_data, user_data):
    steam_id = user_data
    dpg.configure_item("delete_popup", show=True)
    dpg.set_value("delete_account_id", steam_id)

# Function to delete an account
def delete_account(sender, app_data, user_data):
    steam_id = dpg.get_value("delete_account_id")
    accounts = load_accounts()
    if steam_id in accounts:
        del accounts[steam_id]
        save_accounts(accounts)
        dpg.set_value("status_text", f"Account {steam_id} deleted.")
        refresh_account_list()
    dpg.configure_item("delete_popup", show=False)

# Function for plotting a graph of MMR changes
def draw_graph(account_data):
    mmr_changes = account_data["mmr_changes"]

    x_values = list(range(len(mmr_changes)))
    y_values = mmr_changes

    dpg.delete_item("graph_plot", children_only=True)
    with dpg.plot(label="MMR Progress", height=-1, width=-1, parent="graph_plot"):
        dpg.add_plot_legend()
        dpg.add_plot_axis(dpg.mvXAxis, label="Games", tag="x_axis")
        dpg.add_plot_axis(dpg.mvYAxis, label="MMR", tag="y_axis")
        dpg.add_line_series(x_values, y_values, label="MMR Changes", parent="y_axis")
        scatter_series = dpg.add_scatter_series(x_values, y_values, label="MMR Points", parent="y_axis")
        

# Function to load the selected account
def load_account(sender, app_data, user_data):
    steam_id = user_data
    accounts = load_accounts()

    if steam_id not in accounts:
        dpg.set_value("status_text", f"Account with ID {steam_id} not found.")
        return

    account = accounts[steam_id]
    dpg.set_value("loaded_account_text", f"Loaded account: {account['name']} (ID: {steam_id})")
    draw_graph(account)  
    dpg.show_item("edit_mmr_group")  
    dpg.set_value("edit_mmr_entry", str(account["current_mmr"])) 

    dpg.configure_item("steam_id_entry", show=False)
    dpg.configure_item("name_entry", show=False)
    dpg.configure_item("current_mmr_entry", show=False)
    dpg.configure_item("save_account_button", show=False)
  
    dpg.show_item("add_account_button")

    refresh_account_list()

    update_mmr_changes_list(account)

# Function to update the list of MMR changes
def update_mmr_changes_list(account):
    mmr_changes = account["mmr_changes"]
    
    dpg.delete_item("mmr_changes_list", children_only=True)
    
    for i in reversed(range(len(mmr_changes))):
        change = mmr_changes[i]
        prev_mmr = mmr_changes[i - 1] if i > 0 else account["current_mmr"]
        diff = change - prev_mmr
        diff_str = f"+{diff}" if diff > 0 else str(diff) 
        color = [0, 255, 0] if diff > 0 else [255, 0, 0] 
        dpg.add_text(f"{change} ({diff_str})", color=color, parent="mmr_changes_list")

# Function to change MMR
def change_mmr(sender, app_data, user_data):
    loaded_account = dpg.get_value("loaded_account_text")
    steam_id = loaded_account.split("ID: ")[1].strip(")")

    new_mmr = int(dpg.get_value("edit_mmr_entry"))
    accounts = load_accounts()

    if steam_id in accounts:
        account = accounts[steam_id]
        old_mmr = account["current_mmr"]
      
        account["mmr_changes"].append(new_mmr)
        account["current_mmr"] = new_mmr
        save_accounts(accounts)
        draw_graph(account)
        changes = account["mmr_changes"][-100:]
        dpg.delete_item("mmr_changes_list", children_only=True)

        for i in reversed(range(len(changes))):  
            change = changes[i]
            prev_mmr = changes[i - 1] if i > 0 else old_mmr
            diff = change - prev_mmr
            diff_str = f"+{diff}" if diff > 0 else str(diff)  
            color = [0, 255, 0] if diff > 0 else [255, 0, 0] 
            dpg.add_text(f"{change} ({diff_str})", color=color, parent="mmr_changes_list")
        dpg.set_value("status_text", f"MMR updated to {new_mmr}.")

# Function to display account input fields
def show_account_inputs(sender, app_data, user_data):
    dpg.show_item("steam_id_entry")
    dpg.show_item("name_entry")
    dpg.show_item("current_mmr_entry")
    dpg.show_item("save_account_button")
    dpg.hide_item("add_account_button") 

# Main application
def main_app():
    dpg.create_context()
    dpg.create_viewport(title="MMR Tracker", width=1300, height=680)

    with dpg.window(label="Account Management", width=380, height=640):
        dpg.add_button(label="Add Account", callback=show_account_inputs, tag="add_account_button")
        with dpg.group(tag="account_inputs"):
            dpg.add_input_text(label="Steam ID", tag="steam_id_entry", show=False)
            dpg.add_input_text(label="Name", tag="name_entry", show=False)
            dpg.add_input_text(label="Current MMR", tag="current_mmr_entry", show=False)
            dpg.add_button(label="Save Account", callback=save_account, tag="save_account_button", show=False)
        
        dpg.add_text("", tag="status_text", color=[255, 0, 0])

        dpg.add_text("Accounts:")
        with dpg.group(tag="accounts_list"):
            pass

        dpg.add_text("", tag="loaded_account_text")
        with dpg.group(tag="edit_mmr_group", show=False):
            dpg.add_input_text(label="Edit MMR", tag="edit_mmr_entry")
            dpg.add_button(label="Change MMR", callback=change_mmr)

            dpg.add_text("Last MMR Changes:", tag="mmr_changes_header")
            with dpg.child_window(tag="mmr_changes_list", autosize_x=True, autosize_y=True):
                pass

    with dpg.window(label="MMR Graph", width=904, height=640, pos=(380, 0)):
        with dpg.child_window(tag="graph_plot", autosize_x=True, autosize_y=True):
            pass

    with dpg.window(label="Delete Account Confirmation", modal=True, show=False, tag="delete_popup"):
        dpg.add_text("Are you sure you want to delete this account?")
        dpg.add_button(label="Yes", callback=delete_account)
        dpg.add_button(label="No", callback=lambda: dpg.configure_item("delete_popup", show=False))
        dpg.add_text("", tag="delete_account_id", show=False)

    dpg.setup_dearpygui()
    dpg.show_viewport()
    refresh_account_list()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    main_app()
