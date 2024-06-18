import os
import meraki
from prettytable import PrettyTable

# API KEY read only permission is enough
API_KEY = os.getenv("MK_TEST_API")

# colors
colors = {
    "stop": "\x1b[0m",
    "red": "\x1b[6;30;41m",
    "green": "\x1b[6;30;42m",
    "blue": "\x1b[6;30;44m",
    "yellow": "\x1b[6;30;43m",
    "white": "\x1b[6;30;47m",
}

# default table and matrix cells

table_cell_devices = {
    "on": colors["green"] + "YES" + colors["stop"],
    "off": colors["red"] + "NO" + colors["stop"],
    "mis": colors["yellow"] + "MIS" + colors["stop"],
    "loc": colors["blue"] + "LOCK" + colors["stop"],
    "ok": colors["green"] + "OK" + colors["stop"],
}
table_cell_summary = {
    "online": colors["green"] + "Online" + colors["stop"],
    "offline": colors["red"] + "Offline" + colors["stop"],
    "match": colors["green"] + "Match" + colors["stop"],
    "mismatch": colors["yellow"] + "Mismatch" + colors["stop"],
    "locked": colors["blue"] + "Locked" + colors["stop"],
    "totals": colors["white"] + "Totals" + colors["stop"],
}


dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)


organizations = dashboard.organizations.getOrganizations()
# for each org get the devices and the devices status
for org in organizations:
    print(f"\n\n{colors['white']}=== {org['name']} / {org['id']} ==={colors['stop']}")

    # get devices
    devices = dashboard.organizations.getOrganizationDevices(
        org["id"], total_pages="all"
    )
    # get devices status
    devices_status = dashboard.organizations.getOrganizationDevicesStatuses(
        org["id"], total_pages="all"
    )

    # counters
    on_mismatch_qty = 0
    on_locked_qty = 0
    on_ok_qty = 0
    off_mismatch_qty = 0
    off_locked_qty = 0
    off_ok_qty = 0

    t_devices = PrettyTable(["Online", "FW Status", "Name", "Serial"])

    # for each device
    for device in devices:
        # find the status
        status_list = [d for d in devices_status if d["serial"] == device["serial"]]

        # 3 cases
        # "Not running configured version" firmware mismatch
        # "Firmware locked. Please contact support" firmware locked
        # <the FW version> all good
        # for each case also split online and offline devices
        if device["firmware"] == "Not running configured version":
            if status_list[0]["status"] == "online":
                t_devices.add_row(
                    [
                        table_cell_devices["on"],
                        table_cell_devices["mis"],
                        device["name"],
                        device["serial"],
                    ]
                )
                on_mismatch_qty += 1
                continue
            else:
                t_devices.add_row(
                    [
                        table_cell_devices["off"],
                        table_cell_devices["mis"],
                        device["name"],
                        device["serial"],
                    ]
                )
                off_mismatch_qty += 1
                continue

        if device["firmware"] == "Firmware locked. Please contact support":
            if status_list[0]["status"] == "online":
                t_devices.add_row(
                    [
                        table_cell_devices["on"],
                        table_cell_devices["loc"],
                        device["name"],
                        device["serial"],
                    ]
                )
                on_locked_qty += 1
                continue
            else:
                t_devices.add_row(
                    [
                        table_cell_devices["off"],
                        table_cell_devices["loc"],
                        device["name"],
                        device["serial"],
                    ]
                )
                off_locked_qty += 1
                continue

        if status_list[0]["status"] == "online":
            t_devices.add_row(
                [
                    table_cell_devices["on"],
                    table_cell_devices["ok"],
                    device["name"],
                    device["serial"],
                ]
            )
            on_ok_qty += 1

        else:
            t_devices.add_row(
                [
                    table_cell_devices["off"],
                    table_cell_devices["ok"],
                    device["name"],
                    device["serial"],
                ]
            )
            off_ok_qty += 1

    print(t_devices)

    # online devices
    status_list = [d for d in devices_status if d["status"] == "online"]

    # create and print summary for the org
    print(
        f"\n> SUMMARY for {org['name']} / {org['id']}\n> Devices online {len(status_list)}/{len(devices)}"
    )

    t_summary = PrettyTable(
        [
            "Status",
            table_cell_summary["match"],
            table_cell_summary["mismatch"],
            table_cell_summary["locked"],
            table_cell_summary["totals"],
        ]
    )
    t_summary.add_row(
        [
            table_cell_summary["online"],
            on_ok_qty,
            on_mismatch_qty,
            on_locked_qty,
            on_ok_qty + on_mismatch_qty + on_locked_qty,
        ]
    )
    t_summary.add_row(
        [
            table_cell_summary["offline"],
            off_ok_qty,
            off_mismatch_qty,
            off_locked_qty,
            off_ok_qty + off_mismatch_qty + off_locked_qty,
        ]
    )
    t_summary.add_row(
        [
            table_cell_summary["totals"],
            on_ok_qty + off_ok_qty,
            on_mismatch_qty + off_mismatch_qty,
            on_locked_qty + off_locked_qty,
            len(devices),
        ]
    )

    print(t_summary)
